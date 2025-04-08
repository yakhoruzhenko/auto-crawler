import asyncio
import logging
import random
from typing import Any, Type
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.exceptions import ReviewAlreadyExists
from app.repositories import Repository
from app.repositories.db_repo import DBRepository
from app.repositories.file_repo import FileRepository  # noqa: F401
from app.services.date_parser import parse_relative_date
from app.services.logging import setup_logging  # noqa: F401
from app.services.parser import HTMLParser

logger = logging.getLogger(__name__)


class AutoReviewCrawler:
    BASE_URL = "https://auto.ria.com/uk/reviews/"
    PAGE_PARAM = "?page={}"  # Format for pagination
    MAX_RETRIES = 5
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.3',
        'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Language': 'uk',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }

    rating_components_mapping = {
        "Керування": "Handling",
        "Надійність": "Reliability",
        "Комфорт": "Comfort",
        "Ціна": "Price",
        "Дизайн": "Styling"
    }

    def __init__(self, parser_class: Type[HTMLParser], repo_class: Type[Repository]):
        self._parser_class = parser_class
        self._repo = repo_class()
        self._parser_features = 'html.parser'
        self._pages_to_crawl = None
        self._current_page = None
        self._should_parse_full_review = None
        self.total_reviews_scrapped = 0

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(ValueError),
        reraise=True
    )
    async def _fetch_view(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.HEADERS) as response:
                if response.status != 200:
                    # logging.warning(f"Response code: {response.status}. Response: {await response.text()}")
                    logging.warning(f"Response code: {response.status}.")
                    raise ValueError(f"Failed to fetch {url}. Status: {response.status}")
                return await response.text()

    def _parse_short_review(self, article: str, review_data: dict[str, Any], html_parser: HTMLParser) -> None:
        # Extract car name, year and link
        car_card_tag = article.find('a', class_='reviews-cars_name-link')
        car_name_year = car_card_tag.text.strip()
        review_data['name'], review_data['year'] = car_name_year[:-5], int(car_name_year[-4:])
        review_data['link'] = car_card_tag['href'].lstrip('/')

        # Extract review text
        review_text_tag = article.find('p', class_='reviews-car-card_desc-i reviews-cars_desc-cont',
                                       itemprop='reviewBody')
        review_data['review_text'] = review_text_tag.text.strip() if review_text_tag else None

        # Extract review total rating
        rating_tag = article.find('span', class_='dupl-number')
        review_data['total_rating'] = float(rating_tag.text.strip()) if rating_tag else None

        # Extract review rating components
        rating_components = {}
        for li in html_parser.find_all('li', class_='reviews-car-cardrat-i'):
            category_tag = li.find('div', class_='reviews-car-card_rat-tit')
            value_tag = li.find('strong', class_='reviews-car-card_rating-val')

            # Mapping cyrillic to english
            if category_tag and value_tag:
                category = category_tag.text.strip()
                value = int(value_tag.text.strip())
                mapped_category = self.rating_components_mapping.get(category, category)
                rating_components[mapped_category] = value

        review_data['rating_components'] = rating_components

        # Extract mileage
        mileage_tag = article.find('span', class_='reviews-cars__char', title='Пробіг')
        review_data['mileage'] = int(mileage_tag.text.strip().split()[0]) if mileage_tag else None

        # Extract fuel consumption
        fuel_span = article.find('span', class_='reviews-cars__char', title='Витрати пального')
        review_data['fuel_consumption'] = float(fuel_span.text.strip().split(' ')[0]) if fuel_span else None

        # Extract drive type
        drive_span = article.find('span', class_='reviews-cars__char reviews-cars__type')
        review_data['drive_type'] = drive_span.text.strip() if drive_span else None

        # Extract pros
        pros_tag = article.find('p',
                                class_='reviews-car-card_desc-i reviews-car-card_plus reviews-car-card_profit')
        review_data['pros'] = pros_tag.text.strip().split(', ') if pros_tag else None

        # Extract cons
        cons_tag = article.find('p',
                                class_='reviews-car-card_desc-i reviews-car-card_minus reviews-car-card_profit')
        review_data['cons'] = cons_tag.text.strip().split(', ') if cons_tag else None

        # Extract review date
        date_tag = article.find('span',
                                class_='reviews-car-card_author-date reviews-car-card_author-i')
        date = parse_relative_date(date_tag.text.strip()) if date_tag else None
        if not date:
            logger.warning(f"Date tag: {date_tag} can not be converted to date")
        review_data['date'] = date

        if self._should_parse_full_review:
            raise NotImplementedError("Parsing full reviews is not implemented yet")
            # url = urljoin(self.BASE_URL, review_data['link'])
            # view = self._fetch_view(url)
            # self._parse_full_review(view, review_data, html_parser)

    def _parse_full_review(self, html: str, review_data: dict[str, Any], html_parser: HTMLParser) -> None:
        raise NotImplementedError("Parsing full reviews is not implemented yet")

    def _extract_reviews(self, html: str) -> list[dict]:
        """Extracts review data from the given page HTML."""
        html_parser = self._parser_class(html, self._parser_features)
        reviews = []
        try:
            for article in html_parser.find_all('article', class_='reviews-car-card_i'):
                review_data: dict[str, Any] = {}
                # print(article.prettify())
                # breakpoint()
                self._parse_short_review(article, review_data, html_parser)
                reviews.append(review_data)

        except AttributeError:
            logging.warning("Skipping a review due to missing fields")

        return reviews

    async def _get_last_page(self) -> int:
        """Fetches the first page to determine the total number of review pages."""
        html = await self._fetch_view(self.BASE_URL)
        parser = self._parser_class(html, self._parser_features)

        try:
            last_page = max(
                int(a.text.strip()) for a in parser.select(".page-link") if a.text.strip().isdigit()
            )
            pages_to_crawl = None
            if self._pages_to_crawl:
                pages_to_crawl = self._pages_to_crawl
                if self._current_page:
                    pages_to_crawl += self._current_page

            return min(last_page, pages_to_crawl) if pages_to_crawl else last_page
        except Exception:
            logging.error("Could not determine total pages, defaulting to 1")
            return 1

    async def crawl(self, start_page: int | None = None, pages_to_crawl: int | None = None,
                    should_parse_full_review: bool | None = False) -> None:
        """Starts the crawling process, iterating through review pages."""
        self._should_parse_full_review = should_parse_full_review
        self._current_page = await self._repo.get_page_number()
        self._pages_to_crawl = pages_to_crawl
        last_page = await self._get_last_page()
        if not start_page:
            start_page = self._current_page

        for page in range(start_page + 1, last_page + 1):
            url = urljoin(self.BASE_URL, self.PAGE_PARAM.format(page))
            logging.info(f"Fetching page {page} / {last_page}: {url}")
            html = await self._fetch_view(url)
            try:
                reviews = self._extract_reviews(html)
            except TypeError as e:
                logging.error(f"Failed to parse the page: {e}")
                return
            if not reviews:
                logging.warning(f"No reviews found at the page: {page}. Exiting")
                return

            # Store page and reviews
            self._current_page = page
            self.total_reviews_scrapped += len(reviews)
            try:
                await self._repo.store_reviews(reviews)
            except ReviewAlreadyExists:
                await self._repo.store_page_number(0)
                logging.info("Resetting the start page to 0")
                return

            await self._repo.store_page_number(self._current_page)

            # Randomized sleep to avoid detection
            sleep_time = random.uniform(2, 4)
            logging.info(f"Sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)


# TODO: refactor to run multiple async tasks splitting the pages span equally if possible
# TODO: create a celery task that runs once a day
async def main():
    # await asyncio.sleep(300)
    crawler = AutoReviewCrawler(parser_class=BeautifulSoup, repo_class=DBRepository)
    await crawler.crawl(pages_to_crawl=10)
    # await crawler.crawl()
    print(f"Total reviews scraped: {crawler.total_reviews_scrapped}")

if __name__ == "__main__":
    asyncio.run(main())
