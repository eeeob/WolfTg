"""Retry loop, rate-limit backoff, and their edge cases."""

import pytest

from WolfTg import Client, AsyncClient
from WolfTg.methods import GetBalance
from WolfTg.errors import TooManyRequests

from .conftest import OK_BODY, rate_limited_body


# --- retries guard -------------------------------------------------------

@pytest.mark.parametrize("retries", [0, -1, -100])
def test_non_positive_retries_is_rejected_not_silently_skipped(sync_factory, retries):
    """Regression: range(1, 0+1) is empty, so the request was never sent and
    the caller got a misleading TimeoutError instead of an error about the
    bad argument."""

    client = Client(api_key="K", session_factory=sync_factory(retries=retries))

    with pytest.raises(ValueError, match="retries must be >= 1"):
        client(GetBalance())

    assert client.session.calls == 0


@pytest.mark.parametrize("retries", [0, -1])
async def test_non_positive_retries_is_rejected_async(async_factory, retries):
    client = AsyncClient(api_key="K", session_factory=async_factory(retries=retries))

    with pytest.raises(ValueError, match="retries must be >= 1"):
        await client(GetBalance())

    assert client.session.calls == 0


def test_per_call_retries_overrides_session_default(sync_factory):
    client = Client(api_key="K", session_factory=sync_factory(retries=5))

    with pytest.raises(ValueError):
        client(GetBalance(), retries=0)


# --- rate limiting -------------------------------------------------------

def test_retries_after_rate_limit_below_threshold(sync_factory, monkeypatch):
    slept = []
    monkeypatch.setattr("time.sleep", slept.append)

    client = Client(
        api_key="K",
        session_factory=sync_factory(
            responses=[(420, rate_limited_body("2")), (200, OK_BODY)],
            retries=2,
            sleep_threshold=60,
        ),
    )

    assert client(GetBalance()).total == 1.0
    assert slept == [2.0]


def test_raises_immediately_when_retry_after_exceeds_threshold(sync_factory):
    client = Client(
        api_key="K",
        session_factory=sync_factory(
            responses=[(420, rate_limited_body("999"))], retries=3, sleep_threshold=60
        ),
    )

    with pytest.raises(TooManyRequests):
        client(GetBalance())

    assert client.session.calls == 1


async def test_rate_limit_backoff_async(async_factory, monkeypatch):
    slept = []

    async def fake_sleep(s):
        slept.append(s)

    monkeypatch.setattr("asyncio.sleep", fake_sleep)

    client = AsyncClient(
        api_key="K",
        session_factory=async_factory(
            responses=[(420, rate_limited_body("2")), (200, OK_BODY)],
            retries=2,
            sleep_threshold=60,
        ),
    )

    result = await client(GetBalance())

    assert result.total == 1.0
    assert slept == [2.0]
