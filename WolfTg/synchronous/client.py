from typing import Any, Callable, Dict, Optional, Type, Tuple

from .._compat import Self
from ..utils.typings import Number
from ..utils import (
    iscoroutinefunction_wrapped, 
    safe_call, 
    run_awaitable_sync, 
    SyncAwaitableRunner
)
from ..methods import ApiMethod
from ..types import ApiType
from ..models import ApiConfig, api_config
from ..base_client import BaseClient, ErrorHandler, ErrorHandlersArg

from .session import Session, RequestsSession


class Client(BaseClient[Session]):
    def __init__(
        self,
        api_key: str,
        config: ApiConfig = api_config,
        session_factory: Callable[..., Session] = RequestsSession,
        session_args: Optional[Tuple[Any, ...]] = None,
        session_kwargs: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        error_handlers: Optional[Dict[Type[Exception], ErrorHandler]] = None,
        use_awaitable_runner: bool = False,

        ):

        super().__init__(
            api_key,
            session=session_factory(self, *(session_args or ()), **(session_kwargs or {})),
            config=config,
            context=context,
            error_handlers=error_handlers,
        )

        self._use_awaitable_runner = use_awaitable_runner
        self._awaitable_runner: Optional[SyncAwaitableRunner] = None

    def __call__(
        self,
        method: ApiMethod[ApiType],
        retries: Optional[int] = None,
        timeout: Optional[Number] = None,
        sleep_threshold: Optional[Number] = None,
        error_handlers: Optional[ErrorHandlersArg] = None,
        ) -> ApiType:

        self._apply_context(method)

        try:
            return self.session(
                method,
                retries=retries,
                timeout=timeout,
                sleep_threshold=sleep_threshold
            )
        except Exception as e:
            handler = self.get_error_handler(
                e, method, extra=self._normalize_error_handlers(error_handlers)
            )

            if handler is not None:
                if iscoroutinefunction_wrapped(handler):
                    coro = handler(e, self, method)

                    if self._awaitable_runner is not None:
                        safe_call(self._awaitable_runner.run, coro, include_exc=Exception, log_exc=True)
                    else:
                        safe_call(run_awaitable_sync, coro, include_exc=Exception, log_exc=True)
                else:
                    safe_call(handler, e, self, method, include_exc=Exception, log_exc=True)

            raise

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self.stop()

    def start(self):
        self.session.start()

        if self._use_awaitable_runner and self._awaitable_runner is None:
            self._awaitable_runner = SyncAwaitableRunner(lazy=True)

    def stop(self):
        self.session.stop()

        if self._awaitable_runner is not None:
            self._awaitable_runner.close()
            self._awaitable_runner = None
