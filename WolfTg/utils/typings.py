from typing import Annotated, TypeAlias
from pydantic import AfterValidator

from pytools.typings import *
from pytools.typings import __all__ as pytools_all

import pytools as _ut

ValidPhoneNumber: TypeAlias = Annotated[
    PhoneNumber,
    AfterValidator(lambda v: (
        v if _ut.is_phone_number(v)
        else _ut.validation(False, ValueError("Invalid phone number"))
        )
    ),
]
ValidRegionCode: TypeAlias = Annotated[
    RegionCode,
    AfterValidator(lambda v: (
        v.lower() if v.lower() in _ut.get_countries()
        else _ut.validation(False, ValueError("Invalid country code"))
        )
    ),
]
ValidTgOtpCode: TypeAlias = Annotated[
    str,
    AfterValidator(lambda v: (
        _ut.clean_spaces(v)
        if _ut.is_tg_otp_code(v, remove_spaces=True)
        else _ut.validation(False, ValueError("Invalid OTP code"))
        )
    )
]




__all__ = (
    *pytools_all,
    "ValidPhoneNumber",
    "ValidRegionCode",
    "ValidTgOtpCode",
)




