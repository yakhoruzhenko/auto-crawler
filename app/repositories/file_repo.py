import logging
import os
from typing import Any

from app.repositories import Repository

logger = logging.getLogger(__name__)


# FIXME: replace with async appoach
class FileRepository(Repository):
    def __init__(self):
        self._reviews_path = self._get_full_file_path('../static/reviews')
        self._page_path = self._get_full_file_path('../static/page')

    @staticmethod
    async def _get_full_file_path(file_path: str) -> str:
        static_path = os.path.join(os.path.dirname(__file__), file_path)
        return static_path

    async def store_reviews(self, cur_reviews: list[dict[str, Any]]) -> None:
        with open(self._reviews_path, 'a+') as f:
            f.write(f'{cur_reviews},\n')

    async def store_page_number(self, page_number: int) -> None:
        with open(self._page_path, 'w') as f:
            f.write(str(page_number))

    async def get_page_number(self) -> int:
        try:
            with open(self._page_path) as f:
                current_page = int(f.read())
        except FileNotFoundError or ValueError:
            logging.debug("No last_page file found or it's corrupted, creating the new")
            current_page = 0
            self.store_page_number(current_page)
        return current_page
