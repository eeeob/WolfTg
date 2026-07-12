from enum import auto, StrEnum

class OrderStatus(StrEnum):
    PENDING = auto()
    PROCESSING = auto()
    DELIVERING = auto()
    DELIVERED = auto()
    CANCELLING = auto()          
    CANCELLED = auto()   

class UserBalanceType(StrEnum):
    SELL = auto()
    BUY = auto()
    REFERRAL = auto()

class SendCodeType(StrEnum):
    APP = auto()
    EMAIL = auto()


__all__ = (
    "OrderStatus", 
    "UserBalanceType", 
    "SendCodeType", 
)





