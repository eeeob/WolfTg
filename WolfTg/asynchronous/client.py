from typing import Any, Callable, Dict, Optional, Type, Tuple

from .._compat import Self
from ..typings import Number
from ..utils import maybe_awaitable
from ..methods import ApiMethod
from ..types import ApiType
from ..models import ApiConfig, api_config
from ..base_client import BaseClient, ErrorHandler

from .session import AsyncIoSession, AiohttpSession




class AsyncClient(BaseClient[AsyncIoSession]):
    def __init__(
        self,
        api_key: str,
        config: ApiConfig = api_config,
        session_factory: Callable[..., AsyncIoSession] = AiohttpSession,
        session_args: Optional[Tuple[Any, ...]] = None,
        session_kwargs: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        error_handlers: Optional[Dict[Type[Exception], ErrorHandler]] = None,
        ):

        super().__init__(
            api_key,
            session=session_factory(self, *(session_args or ()), **(session_kwargs or {})),
            config=config,
            context=context,
            error_handlers=error_handlers,
        )

    async def __call__(
        self,
        method: ApiMethod[ApiType],
        retries: Optional[int] = None,
        timeout: Optional[Number] = None,
        sleep_threshold: Optional[Number] = None,
        ) -> ApiType:

        self._apply_context(method)

        try:
            return await self.session(
                method,
                retries=retries,
                timeout=timeout,
                sleep_threshold=sleep_threshold
            )
        except Exception as e:
            handler = self.get_error_handler(e)
            if handler is not None:
                await maybe_awaitable(handler, e, self, method, return_exc=True)
            raise

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.stop()

    async def start(self):
        await self.session.start()

    async def stop(self):
        await self.session.stop()
