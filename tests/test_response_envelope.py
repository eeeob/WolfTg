import pytest
from pydantic import ValidationError

from WolfTg.methods import Response
from WolfTg.types.buy import BuySessionsResult


def test_success_response_requires_no_error_fields():
    resp = Response[BuySessionsResult](
        ok=True,
        result={
            "id": "order123",
            "country_code": "us",
            "section": "active",
            "session_type": "telethon",
            "qty": 2,
            "force_full": False,
            "include_json": False,
            "status": "pending",
            "ready_count": 0,
        },
    )
    assert resp.ok
    assert resp.result.id == "order123"


def test_failed_response_requires_message_and_error_id():
    with pytest.raises(ValidationError):
        Response[BuySessionsResult](ok=False)


def test_failed_response_with_message_and_error_id_is_valid():
    resp = Response[BuySessionsResult](
        ok=False, message="bad request", error_id="INVALID_SECTION"
    )
    assert not resp.ok
    assert resp.error_id == "INVALID_SECTION"
