from ..typings import PhoneNumber, RegionCode, Number
from ..enums import AccountSection, BuySessionType, OrderStatus

from .base import ApiObject


class BuyAccountResult(ApiObject):
    phone_number: PhoneNumber
    price: Number

class BuySessionsResult(ApiObject):
    id: str

    country_code: RegionCode

    section: AccountSection
    session_type: BuySessionType
    
    qty: int

    force_full: bool
    include_json: bool

    status: OrderStatus
    ready_count: int

class GetCodeAccountResult(ApiObject):
    phone_number: PhoneNumber
    code: int
    password: str





__all__ = (
    "BuyAccountResult", 
    "BuySessionsResult", 
    "GetCodeAccountResult", 
)



