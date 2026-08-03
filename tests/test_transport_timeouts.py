"""Transport-level regression tests.

These exercise the real transport classes (not the fake sessions used
elsewhere), because the retry loop keys on the builtin TimeoutError and
each transport raises its own timeout type.
"""

import asyncio

import aiohttp
import pytest
import requests

from WolfTg import Client
from WolfTg.methods import GetBalance
from WolfTg.synchronous.session.requests import RequestsSession
from WolfTg.asynchronous.session.aiohttp import AiohttpSession


class _RaisingHttpSession:
    """Stands in for requests.Session and always raises `exc`."""

    def __init__(self, exc):
        self._exc = exc
        self.calls = 0

    def request(self, *args, **kwargs):
        self.calls += 1
        raise self._exc


@pytest.mark.parametrize(
    "exc",
    [
        requests.exceptions.Timeout("t"),
        requests.exceptions.ConnectTimeout("t"),
        requests.exceptions.ReadTimeout("t"),
    ],
)
def test_requests_timeouts_are_translated_to_builtin_timeout_error(exc):
    """requests' Timeout is an OSError, not a builtin TimeoutError.

    Without translation the retry loop's `except TimeoutError` misses it and
    the error escapes on the first attempt.
    """

    class Fixed(RequestsSession):
        def start(self):
            self._session = _RaisingHttpSession(exc)

    client = Client(api_key="K", session_factory=lambda c, **kw: Fixed(c, retries=3, **kw))
    client.start()

    with pytest.raises(TimeoutError):
        client(GetBalance())

    # all three attempts must have been made, not just one
    assert client.session._session.calls == 3


def test_requests_non_timeout_errors_still_propagate():
    """Only timeouts are translated; other transport errors must not be retried."""

    class Fixed(RequestsSession):
        def start(self):
            self._session = _RaisingHttpSession(
                requests.exceptions.SSLError("bad cert")
            )

    client = Client(api_key="K", session_factory=lambda c, **kw: Fixed(c, retries=3, **kw))
    client.start()

    with pytest.raises(requests.exceptions.SSLError):
        client(GetBalance())

    assert client.session._session.calls == 1


class _RaisingClientSession:
    """Stands in for aiohttp.ClientSession and always raises `exc`."""

    closed = False

    def __init__(self, exc):
        self._exc = exc
        self.calls = 0

    def request(self, *args, **kwargs):
        self.calls += 1
        raise self._exc


@pytest.mark.parametrize(
    "exc",
    [
        aiohttp.ServerTimeoutError("t"),
        aiohttp.ConnectionTimeoutError("t"),
        asyncio.TimeoutError("t"),
    ],
)
async def test_aiohttp_timeouts_are_translated_to_builtin_timeout_error(exc):
    """On Python < 3.11 asyncio.TimeoutError is not the builtin TimeoutError,
    so aiohttp's timeouts must be translated or async retries never fire."""

    from WolfTg import AsyncClient

    class Fixed(AiohttpSession):
        async def start(self):
            self._session = _RaisingClientSession(exc)

    client = AsyncClient(api_key="K", session_factory=lambda c, **kw: Fixed(c, retries=3, **kw))
    await client.start()

    with pytest.raises(TimeoutError):
        await client(GetBalance())

    assert client.session._session.calls == 3


async def test_aiohttp_non_timeout_errors_still_propagate():
    from WolfTg import AsyncClient

    class Fixed(AiohttpSession):
        async def start(self):
            self._session = _RaisingClientSession(
                aiohttp.ClientConnectionError("refused")
            )

    client = AsyncClient(api_key="K", session_factory=lambda c, **kw: Fixed(c, retries=3, **kw))
    await client.start()

    with pytest.raises(aiohttp.ClientConnectionError):
        await client(GetBalance())

    assert client.session._session.calls == 1
