from typing import Optional, Callable, Self

from ..typings import Number
from ..methods import ApiMethod
from ..types import ApiType
from ..models import ApiConfig, api_config

from .session import Session, RequestsSession


class Client:
    def __init__(
        self, 
        api_key: str, 
        config: ApiConfig = api_config, 
        session_factory: Callable[[Self], Session] = RequestsSession, 
        ):
        
        self.config = config
        self.session = session_factory(self)

        self.__api_key = api_key
    

    @property
    def api_key(self) -> str:
        return self.__api_key
    

    def __call__(
        self, 
        method: ApiMethod[ApiType], 
        retries: Optional[int] = None, 
        timeout: Optional[Number] = None, 
        sleep_threshold: Optional[Number] = None, 
        ) -> ApiType: 

        return self.session(
            method, 
            retries=retries, 
            timeout=timeout, 
            sleep_threshold=sleep_threshold
        )
    
    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self.stop()

    def start(self):
        self.session.start()

    def stop(self):
        self.session.stop()