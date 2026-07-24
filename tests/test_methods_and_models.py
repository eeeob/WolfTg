from WolfTg.methods import BuySessions, GetBalance
from WolfTg.models import ApiConfig


def test_method_name_is_class_name():
    method = BuySessions(
        country_code="US", section="active", session_type="telethon", qty=2
    )
    assert method.name == "BuySessions"


def test_model_dump_uses_enum_values():
    method = BuySessions(
        country_code="US", section="active", session_type="telethon", qty=2
    )
    dumped = method.model_dump()
    assert dumped["section"] == "active"
    assert dumped["session_type"] == "telethon"
    assert dumped["country_code"] == "us"


def test_build_request_formats_url_and_auth_header():
    config = ApiConfig()
    method = GetBalance()

    req = config.build_request("SECRET_KEY", method)

    assert req.url == "https://wolf-tg.com/api/GetBalance"
    assert req.method == "GET"
    assert req.headers == {"X-API-Key": "SECRET_KEY"}
    assert req.json_data == {}
