from typing import Annotated, TypeAlias, Union
from pydantic import AfterValidator

from . import utils as ut

Number: TypeAlias = Union[int, float]

PhoneNumber = Annotated[str, AfterValidator(ut.validate_phone_number)]
RegionCode = Annotated[str, AfterValidator(ut.validate_rc)]
OtpCode = Annotated[str, AfterValidator(ut.validate_otp_tele_code)]



__all__ = (
    "Number", 
    "PhoneNumber", 
    "RegionCode", 
    "OtpCode", 
)





