from abc import ABC, abstractmethod
from typing import Generic, Optional, Tuple, TypeVar, TYPE_CHECKING

from pydantic import ValidationError
from http import HTTPStatus

from .errors import ApiError, InvalidResponseError, ResponseValidationError, TooManyRequests
from .methods import ApiMethod, Response
from .models import RequestData
from .types import ApiType
from .utils.typings import Number

import json
import logging

if TYPE_CHECKING:
    from .base_client import BaseClient

log = logging.getLogger(__name__)

ClientT = TypeVar("ClientT", bound="BaseClient")


class BaseSession(ABC, Generic[ClientT]):
    """Shared, non-async logic for `Session` and `AsyncIoSession`. Must be subclassed."""

    RETRIES = 1
    TIMEOUT = 60
    SLEEP_THRESHOLD = 60

    def __init__(
        self,
        client: ClientT,
        retries: int = RETRIES,
        timeout: Number = TIMEOUT,
        sleep_threshold: Number = SLEEP_THRESHOLD
        ) -> None:

        self.client: ClientT = client

        self.retries = retries
        self.timeout = timeout
        self.sleep_threshold = sleep_threshold

    def _resolve_call_params(
        self,
        api_method: ApiMethod,
        retries: Optional[int],
        sleep_threshold: Optional[Number],
        ) -> Tuple[int, Number, RequestData]:

        if retries is None:
            retries = self.retries

        if sleep_threshold is None:
            sleep_threshold = self.sleep_threshold

        # Without this the retry loop's range() is empty and the request is
        # never sent, which surfaces as a misleading "timed out" error.
        if retries < 1:
            raise ValueError(f"retries must be >= 1, got {retries}")

        req_data = self.client.config.build_request(self.client.api_key, api_method)

        return retries, sleep_threshold, req_data

    def _parse_and_validate_response(
        self,
        method: ApiMethod[ApiType],
        status_code: int,
        content: str
        ) -> Response[ApiType]:

        method_name = type(method).__name__

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise InvalidResponseError(e, method_name) from e

        try:
            response_type = Response[method.__returning__]
            response = response_type.model_validate(data)
        except ValidationError as e:
            raise ResponseValidationError(e, method_name) from e

        if HTTPStatus.OK <= status_code <= HTTPStatus.IM_USED and response.ok:
            log.debug(
                "Request succeeded | method=%s status=%d",
                method_name, status_code
            )
            return response

        ApiError.raise_it(status_code, response, method_name)

    @abstractmethod
    def make_request(
        self,
        request_data: RequestData,
        *,
        timeout: Optional[Number] = None
        ):
        raise NotImplementedError


__all__ = (
    "BaseSession",
)
