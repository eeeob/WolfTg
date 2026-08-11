from typing import Optional
from aiohttp import ClientSession, TCPConnector, ClientTimeout

from ...utils.typings import Number
from .session import AsyncIoSession


import asyncio




class AiohttpSession(AsyncIoSession):
    def __init__(
        self, 
        *args, 
        limit: int = 100, 
        limit_per_host: int = 0, 
        ttl_dns_cache: Optional[Number] = 3600, 
        loop: Optional[asyncio.AbstractEventLoop] = None, 
        **kw, 
        ) -> None:
        
        super().__init__(*args, **kw)

        self._timeout = ClientTimeout(total=float(self.timeout))
        self._session: Optional[ClientSession] = None
        self._connector_init = {
            "limit": limit, 
            "limit_per_host": limit_per_host, 
            "ttl_dns_cache": ttl_dns_cache, 
            "loop": loop, 
        }

        
    async def make_request(self, request_data, *, timeout = None):
        if self._session is None or self._session.closed:
            raise RuntimeError("Session is not started. Call start() first.")
    
        if timeout is not None:
            timeout = ClientTimeout(total=float(timeout))

        # On Python < 3.11 asyncio.TimeoutError is its own class rather than an
        # alias of the builtin, so aiohttp's timeouts would slip past the base
        # session's `except TimeoutError` -- translate them.
        try:
            async with self._session.request(
                request_data.method,
                request_data.url,
                headers=request_data.headers,
                json=request_data.json_data,
                timeout=timeout
                ) as resp:

                return resp.status, await resp.text()
        except asyncio.TimeoutError as e:
            if isinstance(e, TimeoutError):
                raise
            raise TimeoutError(str(e)) from e
            
    async def start(self):
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                connector=TCPConnector(**self._connector_init), 
                timeout=self._timeout, 
                raise_for_status=False 
            )

    async def stop(self):
        if self._session and not self._session.closed:
            await self._session.close()
            await asyncio.sleep(0.25)  # graceful SSL shutdown