from typing import Optional

from ..typings import PhoneNumber, OtpCode
from ..enums import AccountSection
from ..types import SellAccountResult, SetCodeAccountResult, SetPasswordAccountResult

from .base import ApiMethod


class SellAccount(ApiMethod[SellAccountResult]):
    __returning__ = SellAccountResult
    __request_method__ = "POST"

    phone_number: PhoneNumber
    section: Optional[AccountSection] = None

class SetCodeAccount(ApiMethod[SetCodeAccountResult]):
    __returning__ = SetCodeAccountResult
    __request_method__ = "POST"

    phone_number: PhoneNumber
    code: OtpCode
    password: Optional[str] = None

class SetPasswordAccount(ApiMethod[SetPasswordAccountResult]):
    __returning__ = SetPasswordAccountResult
    __request_method__ = "POST"

    phone_number: PhoneNumber
    password: str
    




__all__ = (
    "SellAccount", 
    "SetCodeAccount", 
    "SetPasswordAccount", 
)





