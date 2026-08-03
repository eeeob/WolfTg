"""Client/session lifecycle: start, stop, reuse, and misuse."""

import pytest

from WolfTg import Client, AsyncClient
from WolfTg.methods import GetBalance
from WolfTg.synchronous.session.requests import RequestsSession
from WolfTg.asynchronous.session.aiohttp import AiohttpSession


def test_stop_without_start_is_a_noop(sync_factory):
    Client(api_key="K", session_factory=sync_factory()).stop()


def test_double_start_and_double_stop_are_idempotent(sync_factory):
    client = Client(api_key="K", session_factory=sync_factory(), use_awaitable_runner=True)

    client.start()
    client.start()
    client.stop()
    client.stop()


def test_client_can_be_restarted_after_stop(sync_factory):
    client = Client(api_key="K", session_factory=sync_factory())

    client.start()
    client.stop()
    client.start()
    try:
        assert client(GetBalance()).total == 1.0
    finally:
        client.stop()


def test_context_manager_starts_and_stops(sync_factory):
    with Client(api_key="K", session_factory=sync_factory()) as client:
        assert client(GetBalance()).total == 1.0


async def test_async_context_manager_starts_and_stops(async_factory):
    async with AsyncClient(api_key="K", session_factory=async_factory()) as client:
        result = await client(GetBalance())

    assert result.total == 1.0


async def test_async_stop_without_start_is_a_noop(async_factory):
    await AsyncClient(api_key="K", session_factory=async_factory()).stop()


# --- real transports refuse to work unstarted ---------------------------

def test_requests_transport_requires_start():
    client = Client(api_key="K")

    with pytest.raises(RuntimeError, match="not started"):
        client(GetBalance())


async def test_aiohttp_transport_requires_start():
    client = AsyncClient(api_key="K")

    with pytest.raises(RuntimeError, match="not started"):
        await client(GetBalance())


def test_requests_transport_start_is_idempotent():
    session = RequestsSession(None)

    session.start()
    first = session._session
    session.start()

    assert session._session is first

    session.stop()
    assert session._session is None


async def test_aiohttp_transport_start_is_idempotent():
    session = AiohttpSession(None)

    await session.start()
    first = session._session
    await session.start()

    assert session._session is first

    await session.stop()


# --- constructor plumbing ------------------------------------------------

def test_session_kwargs_reach_the_session(sync_factory):
    client = Client(
        api_key="K", session_factory=sync_factory(), session_kwargs={"retries": 5, "timeout": 7}
    )

    assert client.session.retries == 5
    assert client.session.timeout == 7


def test_session_args_reach_the_session():
    seen = {}

    class Recording(RequestsSession):
        def __init__(self, client, *args, **kw):
            seen["args"] = args
            super().__init__(client, **kw)

    Client(api_key="K", session_factory=Recording, session_args=("positional",))

    assert seen["args"] == ("positional",)


async def test_async_session_kwargs_reach_the_session(async_factory):
    client = AsyncClient(
        api_key="K", session_factory=async_factory(), session_kwargs={"retries": 5}
    )

    assert client.session.retries == 5


def test_api_key_is_read_only(sync_factory):
    client = Client(api_key="SECRET", session_factory=sync_factory())

    assert client.api_key == "SECRET"

    with pytest.raises(AttributeError):
        client.api_key = "other"


def test_api_key_is_sent_as_auth_header(sync_factory):
    client = Client(api_key="SECRET", session_factory=sync_factory())
    client(GetBalance())

    assert client.session.last_request.headers == {"X-API-Key": "SECRET"}
