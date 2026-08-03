from enum import auto

from .._compat import StrEnum

class AccountOperation(StrEnum):
    SELL = auto()
    BUY = auto()

class AccountSection(StrEnum):
    ACTIVE = auto()
    SPAM = auto()
    FROZEN = auto()

class BuySessionType(StrEnum):
    PYROGRAM = auto()
    PYROGRAM_STRING = auto()
    KURIGRAM = auto()
    KURIGRAM_STRING = auto()
    TELETHON = auto()
    TELETHON_STRING = auto()
    TDATA = auto()


__all__ = (
    "AccountOperation", 
    "AccountSection", 
    "BuySessionType", 
)

