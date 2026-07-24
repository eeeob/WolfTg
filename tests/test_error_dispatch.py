import pytest

from WolfTg.errors import exceptions
from WolfTg.errors.api_error import ApiError, UnknownError
from WolfTg.errors.exceptions.all import exceptions as exceptions_dict
from WolfTg.methods import Response


def _make_response(error_id, message="boom", error_value=None):
    return Response(ok=False, error_id=error_id, error_value=error_value, message=message)


@pytest.mark.parametrize("status_code", list(exceptions_dict))
def test_fallback_class_is_raised_and_importable(status_code):
    fallback_name = exceptions_dict[status_code]["_"]

    fallback_cls = getattr(exceptions, fallback_name)
    assert issubclass(fallback_cls, ApiError)

    with pytest.raises(fallback_cls):
        ApiError.raise_it(status_code, _make_response("SOME_UNKNOWN_ERROR_ID"), "SomeMethod")


# A handful of message templates expect a dict-shaped `value` (e.g. "{value[attempts]}").
# Supply one so the test exercises class resolution, not message formatting.
_DICT_VALUE_ERROR_IDS = {
    "INVALID_VERIFICATION_CODE": {"attempts": 1, "seconds": 30},
    "INVALID_PASSWORD": {"attempts": 1, "seconds": 30, "hint": "hint"},
    "CHANGED_PASSWORD": {"attempts": 1, "seconds": 30, "hint": "hint"},
    "SESSION_PASSWORD_NEEDED": {"account": "acc", "hint": "hint", "attempts": 1, "seconds": 30},
}


@pytest.mark.parametrize(
    "status_code,error_id",
    [
        (status_code, error_id)
        for status_code, ids in exceptions_dict.items()
        for error_id in ids
        if error_id != "_"
    ],
)
def test_known_error_id_resolves_to_concrete_class(status_code, error_id):
    concrete_name = exceptions_dict[status_code][error_id]
    concrete_cls = getattr(exceptions, concrete_name)

    error_value = _DICT_VALUE_ERROR_IDS.get(error_id, "boom")

    with pytest.raises(concrete_cls):
        ApiError.raise_it(status_code, _make_response(error_id, error_value=error_value), "SomeMethod")


def test_unknown_status_code_raises_unknown_error():
    with pytest.raises(UnknownError):
        ApiError.raise_it(418, _make_response("X"), "SomeMethod")


def test_error_message_contains_method_name():
    with pytest.raises(ApiError) as exc_info:
        ApiError.raise_it(400, _make_response("INVALID_SECTION"), "BuySessions")

    assert "BuySessions" in str(exc_info.value)
