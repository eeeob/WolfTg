from typing import Any, Optional, ClassVar, TYPE_CHECKING

from .._compat import Never

from .exceptions.all import exceptions as exceptions_dict
from . import exceptions

if TYPE_CHECKING:
    from ..methods import Response


class ApiError(Exception):
    ID = None
    CODE = None
    NAME = None
    MESSAGE = "{value}"

    STORE_VALUE: ClassVar[bool] = True

    def __init__(
        self, 
        value: Optional[Any] = None, 
        method_name: Optional[str] = None, 
        ):

        super().__init__("WolfTg says: [{} {}] - {} {}".format(
            self.CODE, 
            self.ID or self.NAME, 
            self.MESSAGE.format(value=value) if self.STORE_VALUE else value, 
            f'(caused by "{method_name}")' if method_name else "" 
        ))

        self.value = value if self.STORE_VALUE else None

    @staticmethod
    def raise_it(
        error_code: int, 
        response: "Response", 
        method_name: Optional[str] = None
        ) -> Never:

        error_message = response.message

        if error_code not in exceptions_dict:
            raise UnknownError(
                value=f"[{error_code} {error_message}]", 
                method_name=method_name, 
            )

        error_id = response.error_id


        if error_id not in exceptions_dict[error_code]:
            raise getattr(exceptions, exceptions_dict[error_code]["_"])(
                value=f"[{error_code} {error_message}]", 
                method_name=method_name 
            )
        
        error_cls = getattr(exceptions, exceptions_dict[error_code][error_id])
        
        raise error_cls(
            value=response.error_value if error_cls.STORE_VALUE else error_message, 
            method_name=method_name 
        )

class UnknownError(ApiError):
    CODE = 520
    NAME = "Unknown error"

class InvalidResponseError(UnknownError):
    NAME = "Invalid Response"

class ResponseValidationError(UnknownError):
    NAME = "Response Validation Error"



__all__ = (
    "ApiError", 
    "UnknownError", 
    "InvalidResponseError", 
    "ResponseValidationError", 
)



