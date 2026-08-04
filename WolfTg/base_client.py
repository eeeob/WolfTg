from weakref import WeakValueDictionary

from abc import ABC
from typing import Any, Dict, Generic, Iterable, Optional, Type, TypeVar, Union, TypeAlias, TYPE_CHECKING

from .utils.typings import MaybeCoroutineCallable
from .utils import validation
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
NormalizedErrorHandlers: TypeAlias = Dict[Type[Exception], Dict[Optional[Type[ApiMethod]], ErrorHandler]]
ErrorHandlersArg: TypeAlias = Union[
    Dict[Type[Exception], ErrorHandler],
    NormalizedErrorHandlers,
]



class BaseClient(ABC, Generic[SessionT]):
    """Shared, non-async logic for `Client` and `AsyncClient`. Must be subclassed."""

    def __init__(
        self,
        api_key: str,
        session: SessionT,
        config: ApiConfig = api_config,
        context: Optional[Dict[str, Any]] = None,
        error_handlers: Optional[ErrorHandlersArg] = None,
        ) -> None:

        self.config = config
        self.session: SessionT = session

        # exception type -> method type -> handler. `None` as the method type
        # means "any method" -- how a plain handler value is stored, and the
        # same key `add_error_handler` falls back to when no `methods` is
        # given. The constructor also accepts an already-nested dict directly.
        self.error_handlers: NormalizedErrorHandlers = self._normalize_error_handlers(error_handlers)

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

    @staticmethod
    def _normalize_error_handlers(
        error_handlers: Optional[ErrorHandlersArg],
        ) -> NormalizedErrorHandlers:
        """Normalize either accepted shape into method-type -> handler buckets.

        Accepts a plain `{exc_type: handler}` mapping (applies to every
        method) or an already-nested `{exc_type: {method_type: handler}}`
        mapping, and normalizes both into the latter shape.
        """

        return {
            exc_type: (
                dict(value)
                if isinstance(value, dict)
                else {None: value}
                if callable(value)
                else validation(False, TypeError("error_handlers values must be callables or dictionaries of method types to callables"))
            )
            for exc_type, value in (error_handlers or {}).items()
        }

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
        methods: Optional[Iterable[Type[ApiMethod]]] = None,
        ) -> None:
        """Register a handler for `exc_type`.

        With `methods` omitted, the handler applies to every `ApiMethod`.
        With `methods` given, it only applies when the failing call used one
        of those method types -- a call with a different method type falls
        through to a method-less handler registered for the same (or a
        parent) exception type, if any.
        """

        bucket = self.error_handlers.setdefault(exc_type, {})

        if methods is None:
            bucket[None] = handler
            return

        for method_type in methods:
            bucket[method_type] = handler

    def get_error_handler(
        self,
        error: Exception,
        method: Optional[Union[ApiMethod, Type[ApiMethod]]] = None,
        extra: Optional[NormalizedErrorHandlers] = None,
        ) -> Optional[ErrorHandler]:
        """Resolve the handler for `error` (optionally scoped to `method`).

        `extra` is consulted before `self.error_handlers` at each exception
        class in the MRO -- it's how a single call's one-off handlers take
        priority over the client's own, without replacing them outright.
        """

        if not self.error_handlers and not extra:
            return None

        method_type = (
            method if isinstance(method, type)
            else type(method)
            if method is not None
            else None
        )

        for cls in type(error).__mro__:
            for handlers in (extra, self.error_handlers):
                if not handlers:
                    continue

                bucket = handlers.get(cls)
                if bucket is None:
                    continue

                if method_type is not None and (handler := bucket.get(method_type)) is not None:
                    return handler

                if (handler := bucket.get(None)) is not None:
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
    "ErrorHandler",
    "ErrorHandlersArg",
    "NormalizedErrorHandlers",
)
