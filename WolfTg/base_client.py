from weakref import WeakValueDictionary

from abc import ABC
from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union, TypeAlias, TYPE_CHECKING

from .utils.typings import MaybeCoroutineCallable
from .methods import ApiMethod
from .models import ApiConfig, api_config


if TYPE_CHECKING:
    from .base_session import BaseSession
    from .asynchronous import AsyncClient
    from .synchronous import Client

SessionT = TypeVar("SessionT", bound="BaseSession")
ErrorHandler: TypeAlias = MaybeCoroutineCallable[
    [Exception, Union["AsyncClient", "Client"], "ApiMethod"], 
    Any
    ]



class BaseClient(ABC, Generic[SessionT]):
    """Shared, non-async logic for `Client` and `AsyncClient`. Must be subclassed."""

    def __init__(
        self,
        api_key: str,
        session: SessionT,
        config: ApiConfig = api_config,
        context: Optional[Dict[str, Any]] = None,
        error_handlers: Optional[Dict[Type[Exception], ErrorHandler]] = None,
        ) -> None:

        self.config = config
        self.session: SessionT = session

        self.error_handlers: Dict[Type[Exception], ErrorHandler] = dict(error_handlers or {})

        self.__api_key = api_key
        self.__context: Dict[str, Any] = dict(context or {})

        # Which ApiMethod instances THIS client has already injected its own
        # context into -- scoped per client, so a different client reusing the
        # same instance still gets its one shot. ApiMethod isn't hashable
        # (plain pydantic models aren't), so it can't be a WeakSet element or
        # a WeakKeyDictionary key -- both need to hash the referent. Keying by
        # id() sidesteps that (an int is always hashable), and a
        # WeakValueDictionary only requires the *value* to support weak refs,
        # which ApiMethod does -- entries are evicted automatically once the
        # instance is garbage-collected, with no manual finalizer needed, and
        # a later object reusing the same id() can't be mistaken for the
        # original since the old entry is already gone by then.
        self.__ctx_applied_ids: "WeakValueDictionary[int, ApiMethod]" = WeakValueDictionary()

    @property
    def api_key(self) -> str:
        return self.__api_key

    @property
    def context(self) -> Dict[str, Any]:
        return self.__context

    def add_error_handler(
        self,
        exc_type: Type[Exception],
        handler: ErrorHandler,
        ) -> None:

        self.error_handlers[exc_type] = handler

    def get_error_handler(self, error: Exception) -> Optional[ErrorHandler]:
        if not self.error_handlers:
            return

        for cls in type(error).__mro__:
            if (handler := self.error_handlers.get(cls)) is not None:
                return handler

        return None

    def _apply_context(self, method: ApiMethod) -> ApiMethod:
        if not self.context:
            return method

        if (key := id(method)) not in self.__ctx_applied_ids:
            self.__ctx_applied_ids[key] = method
            method._merge_client_ctx(self.context)

        return method


__all__ = (
    "BaseClient",
)
