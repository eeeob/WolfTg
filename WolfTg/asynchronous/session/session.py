from typing import Tuple, Optional, TYPE_CHECKING

from pydantic import ValidationError
from http import HTTPStatus


from ...typings import Number
from ...models import RequestData
from ...errors import ApiError, TooManyRequests, InvalidResponseError, ResponseValidationError
from ...methods import ApiMethod, Response
from ...types import ApiType

from ...utils import to_coroutine, to_thread

import abc
import json
import asyncio
import logging

if TYPE_CHECKING:
    from ..client import AsyncClient



log = logging.getLogger(__name__)



class AsyncIoSession(abc.ABC):
    RETRIES = 1
    TIMEOUT = 60
    SLEEP_THRESHOLD = 60

    def __init__(
        self, 
        client: "AsyncClient", 
        retries: int = RETRIES, 
        timeout: Number = TIMEOUT, 
        sleep_threshold: Number = SLEEP_THRESHOLD
        ) -> None:

        self.client = client

        self.retries = retries
        self.timeout = timeout 
        self.sleep_threshold = sleep_threshold 

    def _check_response(
        self, 
        method: ApiMethod[ApiType], 
        status_code: int, 
        content: str
        ) -> Response[ApiType]:

        method_name = method.name

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
    
    if TYPE_CHECKING:
        check_response = to_coroutine(_check_response)
    else:
        async def check_response(self, *args, **kw):
            return await to_thread(self._check_response, *args, log_exc=False, **kw)

    async def __call__(
        self, 
        api_method: ApiMethod[ApiType], 
        retries: Optional[int] = None, 
        timeout: Optional[Number] = None, 
        sleep_threshold: Optional[Number] = None, 
        ) -> ApiType: 
        
        if retries is None:
            retries = self.retries
        
        if sleep_threshold is None:
            sleep_threshold = self.sleep_threshold
        
        req_data = self.client.config.build_request(
            self.client.api_key, api_method

        )

        for i in range(1, retries + 1):
            log.debug("Attempt %d/%d | %s", i, retries, req_data)

            try:
                status_code, content = await self.make_request(req_data, timeout=timeout)
            except TimeoutError:
                log.warning(
                    "Attempt %d/%d timed out | request=%s timeout=%s",
                    i, retries, req_data, timeout
                )
                continue

            try:
                return (await self.check_response(api_method, status_code, content)).result
            except TooManyRequests as e:
                if e.value > sleep_threshold:
                    raise

                log.warning(
                    "Rate limited, sleeping | request=%s retry_after=%s attempt=%d/%d",
                    req_data, e.value, i, retries
                )
                await asyncio.sleep(e.value)
        
        
        raise TimeoutError(f"Failed after {retries} retries for {req_data}")

    @abc.abstractmethod
    async def make_request(
        self, 
        request_data: RequestData, 
        *, 
        timeout: Optional[Number] = None
        ) -> Tuple[int, str]:
        raise NotImplementedError

    async def start(self) -> None: 
        pass
    
    async def stop(self) -> None: 
        pass