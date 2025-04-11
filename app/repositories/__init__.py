from abc import ABC, abstractmethod
from typing import Any


class Repository(ABC):
    @abstractmethod
    async def store_reviews(self, cur_reviews: list[dict[str, Any]], *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    async def get_visited_pages(self, *args: Any, **kwargs: Any) -> list[int]: ...

    @abstractmethod
    async def get_total_pages(self, *args: Any, **kwargs: Any) -> int: ...

    @abstractmethod
    async def store_visited_page(self, page_number: int, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    async def store_total_pages(self, total_pages: int, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    async def adjust_visited_pages(self, *args: Any, **kwargs: Any) -> list[int]: ...
