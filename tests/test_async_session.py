import pytest

from WolfTg import AsyncClient
from WolfTg.methods import GetBalance
from WolfTg.asynchronous.session.session import AsyncIoSession
from WolfTg.errors import TooManyRequests

pytestmark = pytest.mark.asyncio


class FakeAsyncSession(AsyncIoSession):
    def __init__(self, *args, responses, **kw):
        super().__init__(*args, **kw)
        self._responses = list(responses)
        self.calls = 0

    async def make_request(self, request_data, *, timeout=None):
        self.calls += 1
        return self._responses.pop(0)


def _client_with_responses(responses, **session_kw):
    return AsyncClient(
        api_key="K",
        session_factory=lambda c: FakeAsyncSession(c, responses=responses, **session_kw),
    )


async def test_successful_first_attempt_returns_result():
    client = _client_with_responses(
        [(200, '{"ok": true, "result": {"balances": {"buy": 1.0}, "total": 1.0}}')]
    )
    result = await client(GetBalance())
    assert result.total == 1.0


async def test_too_many_requests_below_threshold_retries_and_succeeds(monkeypatch):
    slept = []

    async def fake_sleep(s):
        slept.append(s)

    monkeypatch.setattr("asyncio.sleep", fake_sleep)

    client = _client_with_responses(
        [
            (420, '{"ok": false, "error_id": "TOO_MANY_REQUESTS", "error_value": 2, "message": "slow down"}'),
            (200, '{"ok": true, "result": {"balances": {"buy": 1.0}, "total": 1.0}}'),
        ],
        retries=2,
        sleep_threshold=60,
    )

    result = await client(GetBalance())
    assert result.total == 1.0
    assert slept == [2]


async def test_too_many_requests_above_threshold_raises_immediately():
    client = _client_with_responses(
        [(420, '{"ok": false, "error_id": "TOO_MANY_REQUESTS", "error_value": 999, "message": "slow down"}')],
        retries=3,
        sleep_threshold=60,
    )

    with pytest.raises(TooManyRequests):
        await client(GetBalance())

    assert client.session.calls == 1
