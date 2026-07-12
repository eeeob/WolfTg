from typing import Dict, Optional, Union

from ..enums import AccountSection, UserBalanceType
from ..typings import RegionCode, Number

from .base import ApiObject


class _SellAccountsCountryInfo(ApiObject):
    price: Number

class _BuyAccountsCountryInfo(_SellAccountsCountryInfo):
    qty: int
    


AvailableCountriesResult = Dict[AccountSection, Dict[RegionCode, Union[_SellAccountsCountryInfo, _BuyAccountsCountryInfo]]]
AvailableCountriesBySectionResult = Dict[RegionCode, Union[Number, _BuyAccountsCountryInfo]]


class _CountryInfoBuyOptions(ApiObject):
    is_open: bool
    price: Optional[Number] = None

class _CountryInfoSellOptions(_CountryInfoBuyOptions):
    checking_time: Optional[Number] = None


class GetCountryInfoResult(ApiObject):
    name: str
    country_code: int
    region_code: str
    flag: str

    qtys: Dict[AccountSection, int]

    buy_options: Dict[AccountSection, _CountryInfoBuyOptions]
    sell_options: Dict[AccountSection, _CountryInfoSellOptions]

class GetBalanceResult(ApiObject):
    balances: Dict[UserBalanceType, Number]
    total: Number




__all__ = (
    "AvailableCountriesResult", 
    "AvailableCountriesBySectionResult", 
    "GetCountryInfoResult", 
    "GetBalanceResult", 
)




