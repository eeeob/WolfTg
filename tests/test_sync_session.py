import pytest

from WolfTg import Client
from WolfTg.methods import GetBalance
from WolfTg.synchronous.session.session import Session
from WolfTg.errors import TooManyRequests


class FakeSession(Session):
    def __init__(self, *args, responses, **kw):
        super().__init__(*args, **kw)
        self._responses = list(responses)
        self.calls = 0

    def make_request(self, request_data, *, timeout=None):
        self.calls += 1
        return self._responses.pop(0)


def _client_with_responses(responses, **session_kw):
    client = Client(api_key="K", session_factory=lambda c: FakeSession(c, responses=responses, **session_kw))
    return client


def test_successful_first_attempt_returns_result():
    client = _client_with_responses(
        [(200, '{"ok": true, "result": {"balances": {"buy": 1.0}, "total": 1.0}}')]
    )
    result = client(GetBalance())
    assert result.total == 1.0


def test_too_many_requests_below_threshold_retries_and_succeeds(monkeypatch):
    slept = []
    monkeypatch.setattr("time.sleep", lambda s: slept.append(s))

    client = _client_with_responses(
        [
            (420, '{"ok": false, "error_id": "TOO_MANY_REQUESTS", "error_value": 2, "message": "slow down"}'),
            (200, '{"ok": true, "result": {"balances": {"buy": 1.0}, "total": 1.0}}'),
        ],
        retries=2,
        sleep_threshold=60,
    )

    result = client(GetBalance())
    assert result.total == 1.0
    assert slept == [2]


def test_too_many_requests_above_threshold_raises_immediately():
    client = _client_with_responses(
        [(420, '{"ok": false, "error_id": "TOO_MANY_REQUESTS", "error_value": 999, "message": "slow down"}')],
        retries=3,
        sleep_threshold=60,
    )

    with pytest.raises(TooManyRequests):
        client(GetBalance())

    assert client.session.calls == 1


def test_timeout_error_exhausts_retries():
    class TimeoutSession(Session):
        def make_request(self, request_data, *, timeout=None):
            raise TimeoutError("boom")

    client = Client(api_key="K", session_factory=lambda c: TimeoutSession(c, retries=2))

    with pytest.raises(TimeoutError):
        client(GetBalance())
