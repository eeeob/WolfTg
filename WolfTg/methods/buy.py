from pydantic import Field

from ..typings import PhoneNumber, RegionCode
from ..enums import AccountSection, BuySessionType
from ..types import BuyAccountResult, BuySessionsResult, GetCodeAccountResult

from .base import ApiMethod


class BuyAccount(ApiMethod[BuyAccountResult]):
    __returning__ = BuyAccountResult
    __request_method__ = "GET"

    country_code: RegionCode
    section: AccountSection

class BuySessions(ApiMethod[BuySessionsResult]):
    __returning__ = BuySessionsResult
    __request_method__ = "GET"

    country_code: RegionCode
    section: AccountSection
    session_type: BuySessionType
    
    qty: int = Field(gt=0)

    force_full: bool = False
    include_json: bool = False

class GetCodeAccount(ApiMethod[GetCodeAccountResult]):
    __returning__ = GetCodeAccountResult
    __request_method__ = "GET"

    phone_number: PhoneNumber

class GetBuySessionsOrder(ApiMethod[BuySessionsResult]):
    __returning__ = BuySessionsResult
    __request_method__ = "GET"
    
    order_id: str



__all__ = (
    "BuyAccount", 
    "BuySessions", 
    "GetCodeAccount", 
    "GetBuySessionsOrder", 


)


