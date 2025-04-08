from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any


class Element(ABC):
    @abstractmethod
    def find(self, *args: Any, **kwargs: Any) -> Element | None:
        pass

    @abstractmethod
    def prettify(self, *args: Any, **kwargs: Any) -> str:
        pass

    @property
    @abstractmethod
    def text(*args: Any, **kwargs: Any) -> str:
        pass


class HTMLParser(ABC):
    @abstractmethod
    def __init__(self, markup: str, features: str | Sequence[str], *args: Any, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def find(self, *args: Any, **kwargs: Any) -> Element | None:
        pass

    @abstractmethod
    def find_all(self, name: str, *args: Any, **kwargs: Any) -> list[Element]:
        pass

    @abstractmethod
    def select(self, *args: Any, **kwargs: Any) -> list[Element]:
        pass
