import pytest
from pydantic import ValidationError

from WolfTg.methods import GetCodeAccount, BuyAccount


def test_valid_phone_number_is_normalized():
    method = GetCodeAccount(phone_number="+14155552671")
    assert method.phone_number.startswith("+1")


def test_invalid_phone_number_is_rejected():
    with pytest.raises(ValidationError):
        GetCodeAccount(phone_number="not-a-phone")


def test_valid_region_code_is_lowercased():
    method = BuyAccount(country_code="US", section="active")
    assert method.country_code == "us"


def test_invalid_region_code_is_rejected():
    with pytest.raises(ValidationError):
        BuyAccount(country_code="ZZ", section="active")
