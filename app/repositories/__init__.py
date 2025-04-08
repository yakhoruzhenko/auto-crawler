from abc import ABC, abstractmethod
from typing import Any


class Repository(ABC):
    @abstractmethod
    async def store_reviews(self, cur_reviews: list[dict[str, Any]], *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    async def store_page_number(self, page_number: int, *args: Any, **kwargs: Any) -> str: ...

    @abstractmethod
    async def get_page_number(self, *args: Any, **kwargs: Any) -> str: ...
