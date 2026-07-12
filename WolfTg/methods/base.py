from abc import ABC, abstractmethod
from typing import Optional, ClassVar, Generic, Type, Self, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, JsonValue, model_validator
from utils import classproperty
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
        def __returning__(self) -> [Type[ApiType]]:
            pass
        @property
        @abstractmethod
        def __request_method__(self) -> ClassVar[str]:
            pass

    @classproperty(cached=True)
    def name(cls):
        return cls.__name__
    

__all__ = (
    "Response", 
    "ApiMethod", 

)

    


