from typing import Optional
from aiohttp import ClientSession, TCPConnector, ClientTimeout

from ...typings import Number
from .session import AsyncIoSession


import ssl
import asyncio
import certifi




class AiohttpSession(AsyncIoSession):
    def __init__(
        self, 
        *args, 
        limit: int = 100, 
        limit_per_host: int = 30, 
        ttl_dns_cache: Number = 3600, 
        **kw, 
        ) -> None:
        
        super().__init__(*args, **kw)

        self._timeout = ClientTimeout(total=float(self.timeout))
        self._session: Optional[ClientSession] = None
        self._connector_init = {
            "ssl": ssl.create_default_context(cafile=certifi.where()),
            "limit": limit, 
            "limit_per_host": limit_per_host, 
            "ttl_dns_cache": ttl_dns_cache, 
        }

        
    async def make_request(self, request_data, *, timeout = None):
        if self._session is None or self._session.closed:
            raise RuntimeError("Session is not started. Call start() first.")
    
        if timeout is not None:
            timeout = ClientTimeout(total=float(timeout))

        async with self._session.request(
            request_data.method, 
            request_data.url, 
            headers=request_data.headers, 
            json=request_data.json_data, 
            timeout=timeout
            ) as resp:

            return resp.status, await resp.text()
            
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