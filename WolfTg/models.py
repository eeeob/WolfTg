from typing import Dict, Literal, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .methods import ApiMethod


@dataclass(frozen=True, slots=True)
class RequestData:
    method: Literal["GET", "POST"]
    headers: Dict[str, str]
    url: str
    json_data: Optional[Dict[str, Any]] = None


@dataclass(frozen=True, slots=True)
class ApiConfig:
    base_url: str = "https://wolf-tg.com/api/{api_method}"
    api_key_header: str = "X-API-Key"
    
    
    def build_request(self, api_key: str, api_method: "ApiMethod") -> RequestData:
        return RequestData(
            method=api_method.__request_method__.upper(), 
            headers={self.api_key_header: api_key}, 
            url=self.base_url.format_map({"api_method": api_method.name}), 
            json_data=api_method.model_dump()
        )

api_config = ApiConfig()



__all__ = (
    "RequestData", 
    "ApiConfig", 
    "api_config", 
)


