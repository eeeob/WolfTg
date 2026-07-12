from ..typings import RegionCode
from ..enums import AccountSection, AccountOperation
from ..types import AvailableCountriesResult, AvailableCountriesBySectionResult, GetCountryInfoResult, GetBalanceResult

from .base import ApiMethod


class AvailableCountries(ApiMethod[AvailableCountriesResult]):
    __returning__ = AvailableCountriesResult
    __request_method__ = "GET"

    operation: AccountOperation

class AvailableCountriesBySection(ApiMethod[AvailableCountriesBySectionResult]):
    __returning__ = AvailableCountriesBySectionResult
    __request_method__ = "GET"

    operation: AccountOperation
    section: AccountSection

class GetCountryInfo(ApiMethod[GetCountryInfoResult]):
    __returning__ = GetCountryInfoResult
    __request_method__ = "GET"

    country_code: RegionCode

class GetBalance(ApiMethod[GetBalanceResult]):
    __returning__ = GetBalanceResult
    __request_method__ = "GET"




__all__ = (
    "AvailableCountries", 
    "AvailableCountriesBySection", 
    "GetCountryInfo", 
    "GetBalance", 
)



