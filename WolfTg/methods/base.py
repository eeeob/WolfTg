import warnings

from abc import ABC, abstractmethod
from typing import Optional, ClassVar, Generic, Type, Any, Dict, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, JsonValue, model_validator, PrivateAttr

from .._compat import Self
from ..types import ApiType


class Response(BaseModel, Generic[ApiType]):
    ok: bool
    result: Optional[ApiType] = None

    error_id: Optional[str] = None
    error_value: Optional[JsonValue] = None
    message: Optional[str] = None


    @model_validator(mode='after')
    def check_error_fields(self) -> Self:
        if not self.ok and not (self.message and self.error_id is not None):
            raise ValueError("Failed response must have both message and error_id")

        return self
    
class ApiMethod(BaseModel, Generic[ApiType], ABC):
    model_config = ConfigDict(
        extra="allow", 
        use_enum_values=True, 
        populate_by_name=True, 
        arbitrary_types_allowed=True, 
    )

    if TYPE_CHECKING:
        __returning__: ClassVar[Type[ApiType]]
        __request_method__: ClassVar[str]
    else:
        @property
        @abstractmethod
        def __returning__(self) -> Type[ApiType]:
            pass
        @property
        @abstractmethod
        def __request_method__(self) -> str:
            pass

    _context: Optional[Dict[str, Any]] = PrivateAttr(default=None)
    _ctx_applied: bool = PrivateAttr(default=False)
    _client_ctx_applied: bool = PrivateAttr(default=False)

    @property
    def context(self) -> Optional[Dict[str, Any]]:
        return self._context

    def with_ctx(self, **context: Any) -> Self:
        if context:
            if self._ctx_applied:
                warnings.warn(
                    f"Overwriting context already set on this {type(self).__name__} "
                    "instance -- matching keys are replaced, others are kept. Build a new "
                    f"{type(self).__name__}(...) instead if this call was meant for a "
                    "separate request.",
                    UserWarning,
                    stacklevel=2,
                )

            if self._context is None:
                self._context = {}
            self._context.update(context)
            self._ctx_applied = True
        return self

    def _merge_client_ctx(self, client_context: Dict[str, Any]) -> None:
        """Merge a client's own context in, without the `with_ctx` warning.

        Caller-set context always wins on conflicting keys. Warns if some
        other client already merged its own context into this same instance
        before -- each client only ever calls this once per instance (a
        second call from the *same* client is refused earlier, before
        reaching here), so getting here with the flag already set means a
        *different* client is reusing an instance another client touched.
        """

        if not client_context:
            return

        if self._client_ctx_applied:
            warnings.warn(
                f"Client context has already been merged into this {type(self).__name__} "
                "instance by another client. Reusing one method instance across multiple "
                "clients mixes their context together -- build a new "
                f"{type(self).__name__}(...) per client if this wasn't intended.",
                UserWarning,
                stacklevel=4,
            )

        self._context = {**client_context, **(self._context or {})}
        self._client_ctx_applied = True


__all__ = (
    "Response", 
    "ApiMethod", 

)

    


