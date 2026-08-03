"""How raw HTTP status + body pairs are turned into results or errors."""

import pytest

from WolfTg import Client
from WolfTg.methods import GetBalance
from WolfTg.errors import (
    ApiError,
    InternalServerError,
    InvalidResponseError,
    ResponseValidationError,
    UnknownError,
)

RESULT = '{"ok": true, "result": {"balances": {"buy": 1.0}, "total": 1.0}}'


def _call(sync_factory, status, body):
    client = Client(api_key="K", session_factory=sync_factory(responses=[(status, body)]))
    return client(GetBalance())


@pytest.mark.parametrize("status", [200, 201, 226])
def test_success_statuses_return_the_result(sync_factory, status):
    """200..226 (OK..IM_USED) is the success window."""

    assert _call(sync_factory, status, RESULT).total == 1.0


@pytest.mark.parametrize("status", [300, 302, 400, 500])
def test_non_success_statuses_raise(sync_factory, status):
    with pytest.raises(ApiError):
        _call(sync_factory, status, RESULT)


def test_ok_true_without_result_returns_none(sync_factory):
    assert _call(sync_factory, 200, '{"ok": true}') is None


def test_success_status_with_ok_false_still_raises(sync_factory):
    with pytest.raises(UnknownError):
        _call(sync_factory, 200, '{"ok": false, "error_id": "X", "message": "m"}')


def test_error_status_with_ok_true_still_raises(sync_factory):
    with pytest.raises(InternalServerError):
        _call(sync_factory, 500, RESULT)


def test_malformed_json_raises_invalid_response(sync_factory):
    with pytest.raises(InvalidResponseError):
        _call(sync_factory, 200, "<html>gateway error</html>")


def test_result_failing_schema_raises_response_validation_error(sync_factory):
    with pytest.raises(ResponseValidationError):
        _call(sync_factory, 200, '{"ok": true, "result": {"total": "not-a-number"}}')


def test_failed_response_missing_error_id_is_a_validation_error(sync_factory):
    """The envelope requires message + error_id whenever ok is false."""

    with pytest.raises(ResponseValidationError):
        _call(sync_factory, 400, '{"ok": false, "message": "no id"}')


def test_error_message_names_the_failing_method(sync_factory):
    with pytest.raises(ApiError) as exc_info:
        _call(sync_factory, 500, RESULT)

    assert "GetBalance" in str(exc_info.value)


def test_empty_body_raises_invalid_response(sync_factory):
    with pytest.raises(InvalidResponseError):
        _call(sync_factory, 200, "")
