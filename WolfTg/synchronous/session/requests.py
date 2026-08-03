from typing import Optional

from requests.adapters import HTTPAdapter
from requests import Session as ReqSession
from requests.exceptions import Timeout as ReqTimeout

from .session import Session


class RequestsSession(Session):
    def __init__(
        self, 
        *args, 
        pool_connections: int = 10, 
        pool_maxsize: int = 30, 
        **kw, 
        ) -> None:

        super().__init__(*args, **kw)

        self._session: Optional[ReqSession] = None
        self._adapter_init = {
            "pool_connections": pool_connections, 
            "pool_maxsize": pool_maxsize, 
        }

    def make_request(self, request_data, *, timeout = None):
        if self._session is None:
            raise RuntimeError("Session is not started. Call start() first.")
    
        if timeout is None:
            timeout = self.timeout

        # requests raises its own Timeout (an OSError), which is NOT a builtin
        # TimeoutError -- translate it so the base session's retry loop sees it.
        try:
            resp = self._session.request(
                request_data.method,
                request_data.url,
                headers=request_data.headers,
                json=request_data.json_data,
                timeout=timeout
                )
        except ReqTimeout as e:
            raise TimeoutError(str(e)) from e

        return resp.status_code, resp.text

    def start(self) -> None:
        if self._session is None:
            self._session = ReqSession()
            adapter = HTTPAdapter(**self._adapter_init)
            self._session.mount("https://", adapter)
            self._session.mount("http://", adapter)

    def stop(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None