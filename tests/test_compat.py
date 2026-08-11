"""Guards for the 3.10 compatibility layer.

The StrEnum backport is the risky part: a plain `class X(str, Enum)` turns
`auto()` into "1", "2", ... instead of the lowercased member name, which would
silently change every enum value sent to the API.
"""

import sys
from enum import auto

import pytest

from WolfTg._compat import Never, Self, StrEnum
from WolfTg.enums import (
    AccountOperation,
    AccountSection,
    BuySessionType,
    OrderStatus,
    SendCodeType,
    UserBalanceType,
)
from WolfTg.methods import BuySessions


def test_compat_exports_are_importable():
    assert Never is not None
    assert Self is not None
    assert StrEnum is not None


def test_backport_is_only_used_below_311():
    import enum

    if sys.version_info >= (3, 11):
        assert StrEnum is enum.StrEnum
    else:
        assert StrEnum is not getattr(enum, "StrEnum", None)


def test_auto_yields_lowercased_member_name():
    class Sample(StrEnum):
        ACTIVE = auto()
        PYROGRAM_STRING = auto()

    assert Sample.ACTIVE.value == "active"
    assert Sample.PYROGRAM_STRING.value == "pyrogram_string"


def test_members_are_real_strings():
    class Sample(StrEnum):
        ACTIVE = auto()

    assert isinstance(Sample.ACTIVE, str)
    assert Sample.ACTIVE == "active"
    assert str(Sample.ACTIVE) == "active"


@pytest.mark.parametrize(
    "member,expected",
    [
        (AccountSection.ACTIVE, "active"),
        (AccountSection.SPAM, "spam"),
        (AccountSection.FROZEN, "frozen"),
        (AccountOperation.SELL, "sell"),
        (AccountOperation.BUY, "buy"),
        (BuySessionType.PYROGRAM, "pyrogram"),
        (BuySessionType.PYROGRAM_STRING, "pyrogram_string"),
        (BuySessionType.TELETHON_STRING, "telethon_string"),
        (BuySessionType.TDATA, "tdata"),
        (OrderStatus.PENDING, "pending"),
        (OrderStatus.CANCELLING, "cancelling"),
        (UserBalanceType.REFERRAL, "referral"),
        (SendCodeType.EMAIL, "email"),
    ],
)
def test_wire_values_of_every_public_enum(member, expected):
    """Locks the exact strings the API sees, on every supported Python."""

    assert member.value == expected


def test_enum_values_survive_model_dump():
    dumped = BuySessions(
        country_code="US", section="active", session_type="telethon", qty=2
    ).model_dump()

    assert dumped["section"] == "active"
    assert dumped["session_type"] == "telethon"
    assert dumped["country_code"] == "us"


def test_no_module_uses_version_gated_syntax():
    """Compiles every module against the running interpreter -- catches a
    3.11+/3.12+ construct sneaking in below the declared floor."""

    import compileall
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent / "WolfTg"

    assert compileall.compile_dir(str(root), quiet=2, force=True)
