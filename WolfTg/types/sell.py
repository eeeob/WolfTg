from ..typings import PhoneNumber, Number
from ..enums import SendCodeType

from .base import ApiObject


class SellAccountResult(ApiObject):
    phone_number: PhoneNumber
    code_expiry_at: Number
    attempts: int
    type: SendCodeType

class SetCodeAccountResult(ApiObject):
    phone_number: PhoneNumber
    checked_at: Number

class SetPasswordAccountResult(SetCodeAccountResult):
    pass



__all__ = (
    "SellAccountResult", 
    "SetCodeAccountResult", 
    "SetPasswordAccountResult", 
)



