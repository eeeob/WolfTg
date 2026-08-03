import pytest
from pydantic import ValidationError

from WolfTg.methods import GetCodeAccount, BuyAccount, SetCodeAccount


# --- phone numbers -------------------------------------------------------

def test_valid_phone_number_is_normalized():
    method = GetCodeAccount(phone_number="+14155552671")
    assert method.phone_number.startswith("+1")


@pytest.mark.parametrize("value", ["not-a-phone", "", "12", "+9999999999999999"])
def test_invalid_phone_number_is_rejected(value):
    with pytest.raises(ValidationError):
        GetCodeAccount(phone_number=value)


# --- region codes --------------------------------------------------------

def test_valid_region_code_is_lowercased():
    method = BuyAccount(country_code="US", section="active")
    assert method.country_code == "us"


@pytest.mark.parametrize("value", ["ZZ", "", "USA", "1"])
def test_invalid_region_code_is_rejected(value):
    with pytest.raises(ValidationError):
        BuyAccount(country_code=value, section="active")


# --- OTP codes -----------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [("12345", "12345"), ("1 2 3 4 5", "12345"), ("12 345", "12345")],
)
def test_valid_otp_code_is_stripped_of_spaces(raw, expected):
    method = SetCodeAccount(phone_number="+14155552671", code=raw)
    assert method.code == expected


@pytest.mark.parametrize("value", ["123", "abcde", "", "1234567890"])
def test_invalid_otp_code_is_rejected(value):
    with pytest.raises(ValidationError):
        SetCodeAccount(phone_number="+14155552671", code=value)


# --- enum-typed fields ---------------------------------------------------

def test_invalid_enum_value_is_rejected():
    with pytest.raises(ValidationError):
        BuyAccount(country_code="US", section="not-a-section")
