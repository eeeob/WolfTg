"""Context propagation, and the reuse rules around it.

A method carries per-call state: the client merges its own context into the
instance before sending. Three different actors can touch that state, with
three different outcomes on reuse:

- The USER calling `with_ctx()` a second time on the same instance gets a
  UserWarning (they are explicitly overwriting their own earlier call), but
  the update still goes through. This tracks the user's own repeated calls
  specifically -- a client's context merge does not count towards it, so the
  user's very first `with_ctx()` call is always silent even if a client
  already merged its context into the instance beforehand.
- The SAME CLIENT injecting its own context into an instance it has
  *already* injected into before (tracked per client instance) is silently
  refused -- no warning, the existing value is just left alone.
- A DIFFERENT CLIENT injecting its own context into an instance some other
  client already merged context into gets a UserWarning (their two contexts
  are about to be mixed on the same instance), but the merge still happens.
"""

import gc
import warnings

import pytest

from WolfTg import Client, AsyncClient
from WolfTg.methods import GetBalance
from WolfTg.models import ApiConfig


# --- context merging -----------------------------------------------------

def test_client_context_is_applied_to_method(sync_factory):
    client = Client(api_key="K", session_factory=sync_factory(), context={"request_id": "abc"})
    method = GetBalance()

    client(method)

    assert method.context == {"request_id": "abc"}


def test_caller_context_wins_over_client_context(sync_factory):
    client = Client(
        api_key="K",
        session_factory=sync_factory(),
        context={"request_id": "client-default", "extra": "keep"},
    )
    method = GetBalance().with_ctx(request_id="caller-set")

    client(method)

    assert method.context == {"request_id": "caller-set", "extra": "keep"}


def test_client_without_context_leaves_caller_context_alone(sync_factory):
    client = Client(api_key="K", session_factory=sync_factory())
    method = GetBalance().with_ctx(mine="kept")

    client(method)

    assert method.context == {"mine": "kept"}


def test_method_without_any_context_stays_empty(sync_factory):
    client = Client(api_key="K", session_factory=sync_factory())
    method = GetBalance()

    client(method)

    assert method.context is None


def test_context_is_never_sent_over_the_wire():
    """Context is local metadata for handlers -- it must not reach the API."""

    method = GetBalance().with_ctx(internal_secret="do-not-send")
    request = ApiConfig().build_request("KEY", method)

    assert "internal_secret" not in str(request.json_data)
    assert request.json_data == {}


async def test_async_client_applies_context(async_factory):
    client = AsyncClient(
        api_key="K", session_factory=async_factory(), context={"tenant": "alpha"}
    )
    method = GetBalance()

    await client(method)

    assert method.context == {"tenant": "alpha"}


# --- user-facing with_ctx() warning ---------------------------------------

def test_first_with_ctx_call_never_warns():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        GetBalance().with_ctx(a=1)

    assert caught == []


def test_second_with_ctx_call_warns_and_still_merges():
    method = GetBalance().with_ctx(a=1)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        method.with_ctx(b=2)

    assert len(caught) == 1
    assert issubclass(caught[0].category, UserWarning)
    assert "GetBalance" in str(caught[0].message)
    assert method.context == {"a": 1, "b": 2}


def test_first_with_ctx_call_never_warns_even_after_a_client_already_merged(sync_factory):
    """The warning tracks the USER's own repeated with_ctx calls specifically
    -- a client merging its context in first does not count as a "first use",
    so the user's very first with_ctx call still stays silent."""

    client = Client(api_key="K", session_factory=sync_factory(), context={"tenant": "alpha"})
    method = GetBalance()
    client(method)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        method.with_ctx(user_key="mine")

    assert caught == []
    assert method.context == {"tenant": "alpha", "user_key": "mine"}


def test_second_with_ctx_call_warns_even_with_a_client_merge_in_between(sync_factory):
    client = Client(api_key="K", session_factory=sync_factory(), context={"tenant": "alpha"})
    method = GetBalance().with_ctx(first="call")
    client(method)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        method.with_ctx(second="call")

    assert len(caught) == 1


# --- client-side silent refusal (per-client) ------------------------------

def test_client_reinjecting_into_the_same_method_is_silently_refused(sync_factory):
    """No warning here -- reusing a shared "template" method on one client is
    a normal pattern, unlike the user explicitly calling with_ctx again."""

    client = Client(api_key="K", session_factory=sync_factory(), context={"tenant": "alpha"})
    method = GetBalance()
    client(method)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        client(method)

    assert caught == []
    assert method.context == {"tenant": "alpha"}


def test_refusal_is_scoped_per_client_not_global(sync_factory):
    """A different client reusing the same instance still gets its own first
    injection (its own bookkeeping is untouched) -- but that injection now
    carries a cross-client warning, covered separately below."""

    alpha = Client(api_key="A", session_factory=sync_factory(), context={"tenant": "alpha"})
    beta = Client(api_key="B", session_factory=sync_factory(), context={"tenant": "beta"})
    method = GetBalance()

    alpha(method)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        beta(method)

    # beta's own per-client bookkeeping did not refuse the call -- the merge
    # went through; the existing value already on the instance simply wins
    # on the conflicting key, same as the normal "caller context wins" rule.
    assert len(caught) == 1
    assert method.context == {"tenant": "alpha"}


def test_reuse_on_a_client_with_no_context_is_a_pure_noop(sync_factory):
    client = Client(api_key="K", session_factory=sync_factory())
    method = GetBalance()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        client(method)
        client(method)
        client(method)

    assert caught == []
    assert method.context is None


def test_reuse_call_still_succeeds_despite_the_refusal(sync_factory):
    client = Client(api_key="K", session_factory=sync_factory(), context={"x": 1})
    method = GetBalance()
    client(method)

    result = client(method)

    assert result.total == 1.0


def test_internal_retries_do_not_trigger_client_refusal(sync_factory):
    """The refusal check is per client-level call, not per HTTP attempt --
    the retry loop reusing the instance internally must merge exactly once
    and keep retrying normally."""

    from .conftest import OK_BODY, rate_limited_body

    client = Client(
        api_key="K",
        session_factory=sync_factory(
            responses=[(420, rate_limited_body(0)), (200, OK_BODY)],
            retries=3,
            sleep_threshold=60,
        ),
        context={"x": 1},
    )

    result = client(GetBalance())

    assert result.total == 1.0
    assert client.session.calls == 2


def test_fresh_instances_are_always_accepted_without_refusal(sync_factory):
    client = Client(api_key="K", session_factory=sync_factory(), context={"x": 1})

    for _ in range(3):
        assert client(GetBalance()).total == 1.0


async def test_client_refusal_applies_to_async_client_too(async_factory):
    client = AsyncClient(api_key="K", session_factory=async_factory(), context={"tenant": "a"})
    method = GetBalance()

    await client(method)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        await client(method)

    assert caught == []
    assert method.context == {"tenant": "a"}


async def test_sync_and_async_clients_each_get_their_own_shot(sync_factory, async_factory):
    """Each client's own bookkeeping lets its first merge through; the
    cross-client warning still fires since it's a *different* client."""

    sync_client = Client(api_key="K", session_factory=sync_factory(), context={"x": 1})
    async_client = AsyncClient(api_key="K", session_factory=async_factory(), context={"y": 2})
    method = GetBalance()

    sync_client(method)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        await async_client(method)

    assert len(caught) == 1


# --- cross-client warning (a *different* client merging into the same
# instance) ------------------------------------------------------------

def test_second_distinct_client_merging_warns(sync_factory):
    alpha = Client(api_key="A", session_factory=sync_factory(), context={"tenant": "alpha"})
    beta = Client(api_key="B", session_factory=sync_factory(), context={"tenant": "beta"})
    method = GetBalance()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        alpha(method)
        assert caught == []  # first client ever -- no warning

        beta(method)
        assert len(caught) == 1
        assert issubclass(caught[0].category, UserWarning)
        assert "GetBalance" in str(caught[0].message)


def test_third_distinct_client_warns_again(sync_factory):
    one = Client(api_key="1", session_factory=sync_factory(), context={"x": 1})
    two = Client(api_key="2", session_factory=sync_factory(), context={"x": 2})
    three = Client(api_key="3", session_factory=sync_factory(), context={"x": 3})
    method = GetBalance()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        one(method)
        two(method)
        three(method)

    assert len(caught) == 2


def test_same_client_reused_after_a_second_client_does_not_rewarn(sync_factory):
    """The cross-client flag only cares about *some other* client having
    already merged -- the originating client's own repeats stay silent."""

    alpha = Client(api_key="A", session_factory=sync_factory(), context={"tenant": "alpha"})
    beta = Client(api_key="B", session_factory=sync_factory(), context={"tenant": "beta"})
    method = GetBalance()

    alpha(method)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        beta(method)
        assert len(caught) == 1

        alpha(method)  # alpha's own bookkeeping already refuses this silently
        assert len(caught) == 1


def test_no_cross_client_warning_when_second_client_has_no_context(sync_factory):
    """Nothing is merged if the client has no context configured, so there is
    nothing to warn about."""

    alpha = Client(api_key="A", session_factory=sync_factory(), context={"tenant": "alpha"})
    no_ctx_client = Client(api_key="B", session_factory=sync_factory())
    method = GetBalance()

    alpha(method)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        no_ctx_client(method)

    assert caught == []


async def test_cross_client_warning_between_sync_and_async(sync_factory, async_factory):
    sync_client = Client(api_key="K", session_factory=sync_factory(), context={"x": 1})
    async_client = AsyncClient(api_key="K", session_factory=async_factory(), context={"y": 2})
    method = GetBalance()

    sync_client(method)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        await async_client(method)

    assert len(caught) == 1


# --- per-client weakref bookkeeping ----------------------------------------

def test_tracking_entry_is_garbage_collected_with_the_method(sync_factory):
    client = Client(api_key="K", session_factory=sync_factory(), context={"x": 1})
    method = GetBalance()
    client(method)

    tracked_ids = client._BaseClient__ctx_applied_ids
    method_id = id(method)
    assert method_id in tracked_ids

    del method
    gc.collect()

    assert method_id not in tracked_ids


def test_each_client_instance_has_its_own_tracking_dict(sync_factory):
    alpha = Client(api_key="A", session_factory=sync_factory(), context={"tenant": "alpha"})
    beta = Client(api_key="B", session_factory=sync_factory(), context={"tenant": "beta"})

    assert alpha._BaseClient__ctx_applied_ids is not beta._BaseClient__ctx_applied_ids
