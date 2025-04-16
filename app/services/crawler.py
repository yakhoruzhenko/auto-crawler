import asyncio
import logging
import random
import time
from typing import Any, Type
from urllib.parse import urljoin

import aiohttp
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.exceptions import FailedToFetchView, ReviewAlreadyExists
from app.repositories import Repository
from app.repositories.db.crawler import CrawlerRepository
from app.repositories.file.crawler import FileRepository  # noqa: F401
from app.services.date_parser import parse_relative_date
from app.services.html_parser import BeautifulSoupParser, Element, HTMLParser
from app.services.logger import setup_logging  # noqa: F401

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
    MIN_MAX_SLEEP_TIME = (1, 3)

    def __init__(self, parser_class: Type[HTMLParser], repo_class: Type[Repository]):
        self._parser_class: Type[HTMLParser] = parser_class
        self._repo: Repository = repo_class()
        self._should_parse_full_review: bool | None = None
        self.total_reviews_scrapped: int = 0

    async def _get_total_pages(self) -> int:
        html = await self._fetch_view(self.BASE_URL)
        parser = self._parser_class(html)
        try:
            last_page = max(
                int(a.text.strip()) for a in parser.select(".page-link") if a.text.strip().isdigit()
            )
            return last_page
        except Exception as e:
            logging.error("Could not determine total pages")
            raise e

    @staticmethod
    def round_robin_split(pages_to_crawl: list[int], workers: int) -> list[list[int]]:
        buckets: list[list[int]] = [[] for _ in range(workers)]
        for i, item in enumerate(pages_to_crawl):
            buckets[i % workers].append(item)
        return buckets

    async def prepare_pages(self, total_pages_to_crawl: int, workers: int) -> list[list[int]]:
        total_pages = await self._get_total_pages()
        stored_total_pages = await self._repo.get_total_pages()
        if not stored_total_pages:
            stored_total_pages = total_pages
            await self._repo.store_total_pages(stored_total_pages)
        if total_pages_to_crawl > total_pages:
            total_pages_to_crawl = total_pages
        if delta := total_pages - stored_total_pages:
            await self._repo.store_total_pages(total_pages)
            visited_pages = set(await self._repo.adjust_visited_pages(delta))
        else:
            visited_pages = set(await self._repo.get_visited_pages())
        if visited_pages:
            max_visited_page = min(total_pages, max(visited_pages))
        else:
            max_visited_page = 0
        start_page = max_visited_page + 1
        pages_range = set(range(1, start_page))
        missing_pages = list(pages_range - visited_pages)
        if max_visited_page == total_pages and len(missing_pages) == 0:
            logging.info("No pages left to parse. Finishing")
            return []
        elif len(missing_pages) > total_pages_to_crawl:
            pages_to_crawl = missing_pages[:total_pages_to_crawl]
        elif len(missing_pages) == total_pages_to_crawl:
            pages_to_crawl = missing_pages
        else:
            extra_pages_count = total_pages_to_crawl - len(missing_pages)
            extra_pages = list(range(start_page, start_page + extra_pages_count))
            missing_pages.extend(extra_pages)
            pages_to_crawl = missing_pages
        logging.info(f"Preparing to crawl {len(pages_to_crawl)} pages")
        return self.round_robin_split(pages_to_crawl, workers)

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(FailedToFetchView),
        reraise=True
    )
    async def _fetch_view(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.HEADERS) as response:
                if response.status == 404:
                    return ''
                elif response.status != 200:
                    # logging.warning(f"Response code: {response.status}. Response: {await response.text()}")
                    logging.warning(f"Response code: {response.status}.")
                    raise FailedToFetchView(f"Failed to fetch {url}. Status: {response.status}")
                return await response.text()

    def _parse_short_review(self, article: Element, review_data: dict[str, Any], html_parser: HTMLParser) -> None:
        # Extract car name, year and link
        car_card_tag = article.find('a', class_='reviews-cars_name-link')
        car_name_year = car_card_tag.text.strip() if car_card_tag else None
        if car_name_year:
            review_data['name'], review_data['year'] = car_name_year[:-5], int(car_name_year[-4:])
        if car_card_tag:
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
            logging.warning(f"Date tag: {date_tag} can not be converted to date")
        review_data['date'] = date

        if self._should_parse_full_review:
            raise NotImplementedError("Parsing full reviews is not implemented yet")
            # url = urljoin(self.BASE_URL, review_data['link'])
            # view = self._fetch_view(url)
            # self._parse_full_review(view, review_data, html_parser)

    def _parse_full_review(self, html: str, review_data: dict[str, Any], html_parser: HTMLParser) -> None:
        raise NotImplementedError("Parsing full reviews is not implemented yet")

    def _extract_reviews(self, html: str) -> list[dict[str, Any]]:
        """Extracts review data from the given page HTML."""
        html_parser = self._parser_class(html)
        reviews = []
        try:
            for article in html_parser.find_all('article', class_='reviews-car-card_i'):
                review_data: dict[str, Any] = {}
                # print(article.prettify())
                # breakpoint()
                self._parse_short_review(article, review_data, html_parser)
                reviews.append(review_data)

        except Exception as e:
            logging.warning(f"Skipping a review due to the failed parsing. Error: {e}")
            # logging.warning(f"Skipping a review due to the failed parsing. Error: {e}" +
            #                 f"\nCar tag: {article.find('a', class_='reviews-cars_name-link')}.")

        return reviews

    async def crawl(self, pages_to_crawl: list[int], no_sleep: bool | None = False, worker_id: int | None = 1) -> None:
        for page in pages_to_crawl:
            url = urljoin(self.BASE_URL, self.PAGE_PARAM.format(page))
            logging.info(f"Worker {worker_id} -- Fetching page {page}: {url}")
            try:
                html = await self._fetch_view(url)
                reviews = self._extract_reviews(html)
            except FailedToFetchView as e:
                logging.error(f"Worker {worker_id} -- Failed to fetch the page: {e}")
                continue
            except (ValueError, TypeError) as e:
                logging.error(f"Worker {worker_id} -- Failed to parse the page: {e}")
            if not reviews:
                logging.warning(f"Worker {worker_id} -- No reviews found at the page: {page}")

            # Store page and reviews
            self.total_reviews_scrapped += len(reviews)
            try:
                await self._repo.store_reviews(reviews)
            except ReviewAlreadyExists as e:
                logging.info(f"Worker {worker_id} -- {e}")

            await self._repo.store_visited_page(page)

            if no_sleep:
                continue

            # Randomized sleep to avoid detection
            sleep_time = random.uniform(*self.MIN_MAX_SLEEP_TIME)  # nosec
            logging.info(f"Worker {worker_id} -- Sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)


async def main(total_pages_to_crawl: int | None = None,
               workers: int | None = None,
               no_sleep: bool | None = None) -> None:
    try:
        if not workers or workers < 1:
            workers = 1
        if not total_pages_to_crawl or total_pages_to_crawl < 1:
            total_pages_to_crawl = 1
        if no_sleep is None:
            no_sleep = False
        crawler = AutoReviewCrawler(parser_class=BeautifulSoupParser, repo_class=CrawlerRepository)
        pages_per_worker = await crawler.prepare_pages(total_pages_to_crawl, workers)
        await asyncio.gather(*[crawler.crawl(
            pages_to_crawl=pages,
            no_sleep=no_sleep,
            worker_id=i + 1
        ) for i, pages in enumerate(pages_per_worker)])
        print(f"Total reviews scraped: {crawler.total_reviews_scrapped}")
    except Exception as e:
        logging.exception(e)

if __name__ == "__main__":
    SLEEP_TIME = 60 * 60 * 24
    while True:
        asyncio.run(main(
            total_pages_to_crawl=1,
            workers=1,
            no_sleep=True,
        ))
        time.sleep(SLEEP_TIME)
