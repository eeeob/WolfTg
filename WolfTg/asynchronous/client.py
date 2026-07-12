from typing import Optional, Callable, Self

from ..typings import Number
from ..methods import ApiMethod
from ..types import ApiType
from ..models import ApiConfig, api_config

from .session import AsyncIoSession, AiohttpSession




class AsyncClient:
    def __init__(
        self, 
        api_key: str, 
        config: ApiConfig = api_config, 
        session_factory: Callable[[Self], AsyncIoSession] = AiohttpSession, 
        ):
        
        self.config = config
        self.session = session_factory(self)

        self.__api_key = api_key

    @property
    def api_key(self) -> str:
        return self.__api_key
    
    async def __call__(
        self, 
        method: ApiMethod[ApiType], 
        retries: Optional[int] = None, 
        timeout: Optional[Number] = None, 
        sleep_threshold: Optional[Number] = None, 
        ) -> ApiType: 

        return await self.session(
            method, 
            retries=retries, 
            timeout=timeout, 
            sleep_threshold=sleep_threshold
        )
    
    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.stop()

    async def start(self):
        await self.session.start()

    async def stop(self):
        await self.session.stop()