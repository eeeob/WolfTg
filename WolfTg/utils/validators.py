import pytools as ut

def validate_rc(v: str):
    v = v.lower()

    if v not in ut.get_countries():
        raise ValueError("country code is invalid")
    
    return v

def validate_phone_number(v: str):
    if not ut.is_phone_number(v):
        raise ValueError("invalid PhoneNumber")
    
    return ut.parse_phone(v)


def validate_otp_tele_code(v: str):
    if not ut.is_tg_otp_code(v, remove_spaces=True):
        raise ValueError("invalid otp code")
    
    return ut.clean_spaces(v)




__all__ = (
    "validate_rc", 
    "validate_phone_number", 
    "validate_otp_tele_code", 
)





