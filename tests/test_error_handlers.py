"""Error-handler dispatch, sync/async interop, and isolation guarantees.

Handlers are side-effect hooks: they run, then the original error propagates
regardless. A handler must never swallow, replace, or mask that error.
"""

import asyncio

import pytest

from WolfTg import Client, AsyncClient
from WolfTg.methods import GetBalance
from WolfTg.errors import ApiError, BadRequest, InvalidUserId, TooManyRequests

from .conftest import ERR_BODY


def _sync_client(sync_factory, **kw):
    return Client(api_key="K", session_factory=sync_factory(responses=[(400, ERR_BODY)]), **kw)


def _async_client(async_factory, **kw):
    return AsyncClient(
        api_key="K", session_factory=async_factory(responses=[(400, ERR_BODY)]), **kw
    )


# --- dispatch ------------------------------------------------------------

def test_handler_receives_error_client_and_method(sync_factory):
    seen = []
    client = _sync_client(sync_factory, error_handlers={BadRequest: lambda *a: seen.append(a)})
    method = GetBalance()

    with pytest.raises(BadRequest):
        client(method)

    (error, passed_client, passed_method), = seen
    assert isinstance(error, BadRequest)
    assert passed_client is client
    assert passed_method is method


def test_most_specific_handler_wins_over_base_class(sync_factory):
    fired = []
    body = '{"ok": false, "error_id": "INVALID_USER_ID", "message": "bad", "error_value": "x"}'
    client = Client(
        api_key="K",
        session_factory=sync_factory(responses=[(400, body)]),
        error_handlers={
            ApiError: lambda *a: fired.append("ApiError"),
            BadRequest: lambda *a: fired.append("BadRequest"),
            InvalidUserId: lambda *a: fired.append("InvalidUserId"),
        },
    )

    with pytest.raises(InvalidUserId):
        client(GetBalance())

    assert fired == ["InvalidUserId"]


def test_base_class_handler_catches_subclass(sync_factory):
    fired = []
    client = _sync_client(sync_factory, error_handlers={ApiError: lambda *a: fired.append(1)})

    with pytest.raises(BadRequest):
        client(GetBalance())

    assert fired == [1]


def test_non_matching_handler_is_not_invoked(sync_factory):
    fired = []
    client = _sync_client(
        sync_factory, error_handlers={TooManyRequests: lambda *a: fired.append(1)}
    )

    with pytest.raises(BadRequest):
        client(GetBalance())

    assert fired == []


def test_handlers_apply_to_non_api_exceptions_too(sync_factory):
    """Handlers key on any Exception, not just ApiError."""

    fired = []
    client = Client(
        api_key="K",
        session_factory=sync_factory(retries=-1),
        error_handlers={ValueError: lambda *a: fired.append(1)},
    )

    with pytest.raises(ValueError):
        client(GetBalance())

    assert fired == [1]


def test_add_error_handler_registers_after_construction(sync_factory):
    fired = []
    client = _sync_client(sync_factory)
    client.add_error_handler(ApiError, lambda *a: fired.append(1))

    with pytest.raises(BadRequest):
        client(GetBalance())

    assert fired == [1]


def test_no_handlers_registered_is_a_clean_passthrough(sync_factory):
    client = _sync_client(sync_factory)

    with pytest.raises(BadRequest):
        client(GetBalance())


# --- method-scoped handlers ------------------------------------------------

def test_method_scoped_handler_fires_for_its_method(sync_factory):
    fired = []
    client = _sync_client(sync_factory)
    client.add_error_handler(
        BadRequest, lambda *a: fired.append(1), methods=[GetBalance]
    )

    with pytest.raises(BadRequest):
        client(GetBalance())

    assert fired == [1]


def test_method_scoped_handler_does_not_fire_for_other_methods(sync_factory):
    from WolfTg.methods import AvailableCountries

    fired = []
    client = _sync_client(sync_factory)
    client.add_error_handler(
        BadRequest, lambda *a: fired.append(1), methods=[AvailableCountries]
    )

    with pytest.raises(BadRequest):
        client(GetBalance())

    assert fired == []


def test_method_scoped_handler_wins_over_method_less_handler(sync_factory):
    fired = []
    client = Client(
        api_key="K",
        session_factory=sync_factory(responses=[(400, ERR_BODY)]),
        error_handlers={BadRequest: lambda *a: fired.append("generic")},
    )
    client.add_error_handler(
        BadRequest, lambda *a: fired.append("scoped"), methods=[GetBalance]
    )

    with pytest.raises(BadRequest):
        client(GetBalance())

    assert fired == ["scoped"]


def test_method_less_handler_still_catches_a_different_method(sync_factory):
    from WolfTg.methods import AvailableCountries

    fired = []
    client = Client(
        api_key="K",
        session_factory=sync_factory(responses=[(400, ERR_BODY)]),
        error_handlers={BadRequest: lambda *a: fired.append("generic")},
    )
    client.add_error_handler(
        BadRequest, lambda *a: fired.append("scoped"), methods=[AvailableCountries]
    )

    with pytest.raises(BadRequest):
        client(GetBalance())

    assert fired == ["generic"]


# --- isolation -----------------------------------------------------------

def test_handler_exception_does_not_mask_the_original_error(sync_factory):
    def exploding(error, client, method):
        raise RuntimeError("handler exploded")

    client = _sync_client(sync_factory, error_handlers={BadRequest: exploding})

    with pytest.raises(BadRequest):
        client(GetBalance())


async def test_async_handler_exception_does_not_mask_original(async_factory):
    async def exploding(error, client, method):
        raise RuntimeError("handler exploded")

    client = _async_client(async_factory, error_handlers={BadRequest: exploding})

    with pytest.raises(BadRequest):
        await client(GetBalance())


def test_successful_call_never_invokes_a_handler(sync_factory):
    fired = []
    client = Client(
        api_key="K",
        session_factory=sync_factory(),
        error_handlers={Exception: lambda *a: fired.append(1)},
    )

    client(GetBalance())

    assert fired == []


# --- sync/async interop --------------------------------------------------

def test_sync_client_runs_a_sync_handler(sync_factory):
    fired = []
    client = _sync_client(sync_factory, error_handlers={BadRequest: lambda *a: fired.append(1)})

    with pytest.raises(BadRequest):
        client(GetBalance())

    assert fired == [1]


def test_sync_client_runs_an_async_handler(sync_factory):
    fired = []

    async def handler(error, client, method):
        fired.append(1)

    client = _sync_client(sync_factory, error_handlers={BadRequest: handler})

    with pytest.raises(BadRequest):
        client(GetBalance())

    assert fired == [1]


async def test_async_client_runs_a_sync_handler(async_factory):
    fired = []
    client = _async_client(async_factory, error_handlers={BadRequest: lambda *a: fired.append(1)})

    with pytest.raises(BadRequest):
        await client(GetBalance())

    assert fired == [1]


async def test_async_client_runs_an_async_handler(async_factory):
    fired = []

    async def handler(error, client, method):
        fired.append(1)

    client = _async_client(async_factory, error_handlers={BadRequest: handler})

    with pytest.raises(BadRequest):
        await client(GetBalance())

    assert fired == [1]


# --- awaitable runner ----------------------------------------------------

def test_async_handler_from_sync_client_inside_running_loop_needs_runner(sync_factory):
    """Without a runner, an async handler cannot be driven from inside an
    already-running loop (asyncio.run would deadlock), so it is skipped and
    logged. `use_awaitable_runner=True` is the supported remedy."""

    fired = []

    async def handler(error, client, method):
        fired.append(1)

    async def main():
        client = _sync_client(sync_factory, error_handlers={BadRequest: handler})
        with pytest.raises(BadRequest):
            client(GetBalance())
        return fired

    assert asyncio.run(main()) == []


def test_awaitable_runner_drives_async_handler_inside_running_loop(sync_factory):
    fired = []

    async def handler(error, client, method):
        fired.append(1)

    async def main():
        with _sync_client(
            sync_factory, error_handlers={BadRequest: handler}, use_awaitable_runner=True
        ) as client:
            with pytest.raises(BadRequest):
                client(GetBalance())
        return fired

    assert asyncio.run(main()) == [1]


def test_runner_is_created_on_start_and_closed_on_stop(sync_factory):
    client = _sync_client(sync_factory, use_awaitable_runner=True)
    assert client._awaitable_runner is None

    client.start()
    runner = client._awaitable_runner
    assert runner is not None

    client.stop()
    assert client._awaitable_runner is None
    assert not runner.running


def test_restart_creates_a_fresh_runner(sync_factory):
    client = _sync_client(sync_factory, use_awaitable_runner=True)

    client.start()
    first = client._awaitable_runner
    client.stop()

    client.start()
    second = client._awaitable_runner
    client.stop()

    assert second is not first


def test_runner_is_not_created_without_the_flag(sync_factory):
    client = _sync_client(sync_factory)
    client.start()

    assert client._awaitable_runner is None

    client.stop()


# --- per-call error_handlers ------------------------------------------------

def test_per_call_handler_fires_alongside_client_handler(sync_factory):
    fired = []
    client = _sync_client(
        sync_factory, error_handlers={BadRequest: lambda *a: fired.append("client")}
    )

    with pytest.raises(BadRequest):
        client(GetBalance(), error_handlers={BadRequest: lambda *a: fired.append("call")})

    assert fired == ["call"]


def test_per_call_handler_works_with_no_client_handlers_registered(sync_factory):
    fired = []
    client = _sync_client(sync_factory)

    with pytest.raises(BadRequest):
        client(GetBalance(), error_handlers={BadRequest: lambda *a: fired.append(1)})

    assert fired == [1]


def test_per_call_handler_does_not_leak_into_later_calls(sync_factory):
    fired = []
    client = Client(
        api_key="K", session_factory=sync_factory(responses=[(400, ERR_BODY), (400, ERR_BODY)])
    )

    with pytest.raises(BadRequest):
        client(GetBalance(), error_handlers={BadRequest: lambda *a: fired.append(1)})

    with pytest.raises(BadRequest):
        client(GetBalance())

    assert fired == [1]


def test_per_call_handler_falls_back_to_client_handler_for_other_types(sync_factory):
    fired = []
    client = _sync_client(
        sync_factory, error_handlers={ApiError: lambda *a: fired.append("client")}
    )

    with pytest.raises(BadRequest):
        client(GetBalance(), error_handlers={TooManyRequests: lambda *a: fired.append("call")})

    assert fired == ["client"]


def test_per_call_handler_can_be_method_scoped(sync_factory):
    from WolfTg.methods import AvailableCountries

    fired = []
    client = _sync_client(sync_factory)

    with pytest.raises(BadRequest):
        client(
            GetBalance(),
            error_handlers={BadRequest: {AvailableCountries: lambda *a: fired.append("scoped")}},
        )

    assert fired == []


async def test_per_call_handler_works_on_async_client(async_factory):
    fired = []
    client = _async_client(async_factory)

    with pytest.raises(BadRequest):
        await client(GetBalance(), error_handlers={BadRequest: lambda *a: fired.append(1)})

    assert fired == [1]
