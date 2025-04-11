import logging
import os
from typing import Any

import aiofiles

from app.repositories import Repository

logger = logging.getLogger(__name__)


class FileRepository(Repository):
    def __init__(self) -> None:
        self._reviews_path = self._get_full_file_path('../static/reviews')
        self._page_path = self._get_full_file_path('../static/page')

    @staticmethod
    def _get_full_file_path(file_path: str) -> str:
        static_path = os.path.join(os.path.dirname(__file__), file_path)
        return static_path

    async def store_reviews(self, cur_reviews: list[dict[str, Any]]) -> None:
        async with aiofiles.open(self._reviews_path, 'a+') as f:
            await f.write(f'{cur_reviews},\n')

    # async def store_page_number(self, page_number: int) -> None:
    #     async with aiofiles.open(self._page_path, 'w') as f:
    #         await f.write(str(page_number))

    # async def get_page_number(self) -> int:
    #     try:
    #         async with aiofiles.open(self._page_path, 'r') as f:
    #             content = await f.read()
    #             current_page = int(content)
    #     except (FileNotFoundError, ValueError):
    #         logging.debug("No last_page file found or it's corrupted, creating the new")
    #         current_page = 0
    #         await self.store_page_number(current_page)
    #     return current_page
