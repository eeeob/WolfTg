import pytest

from WolfTg.synchronous.session.session import Session
from WolfTg.asynchronous.session.session import AsyncIoSession

OK_BODY = '{"ok": true, "result": {"balances": {"buy": 1.0}, "total": 1.0}}'
ERR_BODY = '{"ok": false, "error_id": "INVALID_SECTION", "message": "bad", "error_value": "x"}'


def rate_limited_body(error_value):
    return (
        '{"ok": false, "error_id": "TOO_MANY_REQUESTS", '
        '"message": "slow down", "error_value": %s}' % error_value
    )


class FakeSession(Session):
    """Sync session that replays canned (status, body) pairs."""

    def __init__(self, *args, responses=None, **kw):
        super().__init__(*args, **kw)
        self._responses = list(responses or [(200, OK_BODY)])
        self.calls = 0

    def make_request(self, request_data, *, timeout=None):
        self.calls += 1
        self.last_request = request_data
        # repeat the final response once exhausted
        return self._responses.pop(0) if len(self._responses) > 1 else self._responses[0]


class FakeAsyncSession(AsyncIoSession):
    """Async twin of FakeSession."""

    def __init__(self, *args, responses=None, **kw):
        super().__init__(*args, **kw)
        self._responses = list(responses or [(200, OK_BODY)])
        self.calls = 0

    async def make_request(self, request_data, *, timeout=None):
        self.calls += 1
        self.last_request = request_data
        return self._responses.pop(0) if len(self._responses) > 1 else self._responses[0]


@pytest.fixture
def sync_factory():
    """Build a session_factory yielding a FakeSession with given responses/kwargs."""

    def make(responses=None, **session_kw):
        return lambda client, **kw: FakeSession(
            client, responses=responses, **{**session_kw, **kw}
        )

    return make


@pytest.fixture
def async_factory():
    def make(responses=None, **session_kw):
        return lambda client, **kw: FakeAsyncSession(
            client, responses=responses, **{**session_kw, **kw}
        )

    return make
