from typing import Optional, TYPE_CHECKING

from ...typings import Number
from ...errors import TooManyRequests
from ...methods import ApiMethod, Response
from ...types import ApiType
from ...base_session import BaseSession

import time
import logging

if TYPE_CHECKING:
    from ..client import Client


log = logging.getLogger(__name__)



class Session(BaseSession["Client"]):
    check_response = BaseSession._parse_and_validate_response

    def __call__(
        self,
        api_method: ApiMethod[ApiType],
        retries: Optional[int] = None,
        timeout: Optional[Number] = None,
        sleep_threshold: Optional[Number] = None,
        ) -> ApiType:

        retries, sleep_threshold, req_data = self._resolve_call_params(
            api_method, retries, sleep_threshold
        )

        for i in range(1, retries + 1):
            log.debug("Attempt %d/%d | %s", i, retries, req_data)

            try:
                status_code, content = self.make_request(req_data, timeout=timeout)
            except TimeoutError:
                log.warning(
                    "Attempt %d/%d timed out | request=%s timeout=%s",
                    i, retries, req_data, timeout
                )
                continue

            try:
                return self.check_response(api_method, status_code, content).result
            except TooManyRequests as e:
                retry_after = e.value

                if retry_after is None or retry_after > sleep_threshold:
                    raise

                log.warning(
                    "Rate limited, sleeping | request=%s retry_after=%s attempt=%d/%d",
                    req_data, retry_after, i, retries
                )
                time.sleep(retry_after)
        
        
        raise TimeoutError(f"Failed after {retries} retries for {req_data}")

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass