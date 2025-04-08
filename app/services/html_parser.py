from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from bs4 import BeautifulSoup


class Element(ABC):
    @abstractmethod
    def find(self, *args: Any, **kwargs: Any) -> Element | None:
        ...

    @abstractmethod
    def prettify(self, *args: Any, **kwargs: Any) -> str:
        ...

    @property
    @abstractmethod
    def text(*args: Any, **kwargs: Any) -> str:
        ...

    @abstractmethod
    def __getitem__(self, index: str) -> Any:
        ...


class HTMLParser(ABC):
    @abstractmethod
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ...

    @abstractmethod
    def find(self, *args: Any, **kwargs: Any) -> Element | None:
        ...

    @abstractmethod
    def find_all(self, *args: Any, **kwargs: Any) -> list[Element]:
        ...

    @abstractmethod
    def select(self, *args: Any, **kwargs: Any) -> list[Element]:
        ...


class BeautifulSoupParser(HTMLParser):
    def __init__(self, markup: str, features: str | Sequence[str], *args: Any, **kwargs: Any):
        self._soup = BeautifulSoup(markup, features, *args, **kwargs)

    def find(self, name: str, *args: Any, **kwargs: Any) -> Any:
        return self._soup.find(name, *args, **kwargs)

    def find_all(self, name: str, *args: Any, **kwargs: Any) -> list[Any]:
        return self._soup.find_all(name, *args, **kwargs)

    def select(self, *args: Any, **kwargs: Any) -> list[Any]:
        return self._soup.select(*args, **kwargs)
