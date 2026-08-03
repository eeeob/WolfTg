"""Options the real transports pass through to the underlying HTTP client."""

import aiohttp

from WolfTg import Client, AsyncClient
from WolfTg.methods import GetBalance
from WolfTg.models import RequestData
from WolfTg.synchronous.session.requests import RequestsSession
from WolfTg.asynchronous.session.aiohttp import AiohttpSession

REQUEST = RequestData(method="GET", headers={"X-API-Key": "K"}, url="https://example.invalid/x")
BODY = '{"ok": true, "result": {"balances": {}, "total": 0}}'


class _RecordingHttpSession:
    closed = False

    def __init__(self):
        self.seen = []

    def request(self, method, url, **kwargs):
        self.seen.append(kwargs)
        return _Resp()


class _Resp:
    status_code = 200
    text = BODY


def test_requests_uses_session_timeout_by_default():
    session = RequestsSession(None, timeout=42)
    session._session = _RecordingHttpSession()

    session.make_request(REQUEST)

    assert session._session.seen[0]["timeout"] == 42


def test_requests_per_call_timeout_overrides_session_default():
    session = RequestsSession(None, timeout=42)
    session._session = _RecordingHttpSession()

    session.make_request(REQUEST, timeout=5)

    assert session._session.seen[0]["timeout"] == 5


def test_requests_pool_options_reach_the_adapter():
    session = RequestsSession(None, pool_connections=3, pool_maxsize=9)

    assert session._adapter_init == {"pool_connections": 3, "pool_maxsize": 9}

    session.start()
    try:
        adapter = session._session.get_adapter("https://example.invalid")
        assert adapter._pool_connections == 3
        assert adapter._pool_maxsize == 9
    finally:
        session.stop()


def test_requests_start_creates_and_stop_closes_the_session():
    session = RequestsSession(None)
    assert session._session is None

    session.start()
    assert session._session is not None

    session.stop()
    assert session._session is None


def test_aiohttp_connector_options_are_stored():
    session = AiohttpSession(None, limit=7, limit_per_host=3, ttl_dns_cache=99)

    assert session._connector_init == {
        "limit": 7,
        "limit_per_host": 3,
        "ttl_dns_cache": 99,
        "loop": None,
    }


async def test_aiohttp_start_creates_and_stop_closes_the_session():
    session = AiohttpSession(None)
    assert session._session is None

    await session.start()
    assert isinstance(session._session, aiohttp.ClientSession)
    assert not session._session.closed

    await session.stop()
    assert session._session.closed


class _AsyncRespCtx:
    """Minimal async context manager mimicking aiohttp's request()."""

    def __init__(self, status, body):
        self._status = status
        self._body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    @property
    def status(self):
        return self._status

    async def text(self):
        return self._body


async def test_aiohttp_returns_status_and_body_on_success():
    """Covers the happy path through the real AiohttpSession.make_request."""

    class Recording:
        closed = False

        def request(self, method, url, **kwargs):
            return _AsyncRespCtx(200, BODY)

    session = AiohttpSession(None)
    session._session = Recording()

    status, body = await session.make_request(REQUEST)

    assert status == 200
    assert body == BODY


async def test_aiohttp_client_end_to_end_success():
    class Recording:
        closed = False

        def request(self, method, url, **kwargs):
            return _AsyncRespCtx(200, BODY)

    class Fixed(AiohttpSession):
        async def start(self):
            self._session = Recording()

    client = AsyncClient(api_key="K", session_factory=Fixed)
    await client.start()

    assert (await client(GetBalance())).total == 0


async def test_aiohttp_per_call_timeout_is_converted():
    """A per-call timeout must be wrapped in ClientTimeout, not passed raw."""

    seen = {}

    class Recording:
        closed = False

        def request(self, method, url, **kwargs):
            seen.update(kwargs)
            raise aiohttp.ServerTimeoutError("stop here")

    session = AiohttpSession(None)
    session._session = Recording()

    try:
        await session.make_request(REQUEST, timeout=12)
    except TimeoutError:
        pass

    assert isinstance(seen["timeout"], aiohttp.ClientTimeout)
    assert seen["timeout"].total == 12.0


def test_client_forwards_transport_kwargs_end_to_end():
    client = Client(
        api_key="K",
        session_kwargs={"timeout": 11, "pool_maxsize": 4},
    )

    assert client.session.timeout == 11
    assert client.session._adapter_init["pool_maxsize"] == 4


def test_async_client_forwards_transport_kwargs_end_to_end():
    client = AsyncClient(
        api_key="K",
        session_kwargs={"timeout": 11, "limit": 4},
    )

    assert client.session.timeout == 11
    assert client.session._connector_init["limit"] == 4
