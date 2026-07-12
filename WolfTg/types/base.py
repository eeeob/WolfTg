from typing import TypeVar
from pydantic import BaseModel, ConfigDict

ApiType = TypeVar("ApiType")

class ApiObject(BaseModel):
    model_config = ConfigDict(
        extra="allow", 
        validate_assignment=True, 
        frozen=True, 
        arbitrary_types_allowed=True, 
        defer_build=True, 
    )



__all__ = (
    "ApiType", 
    "ApiObject", 
)





