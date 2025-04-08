from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from app.exceptions import ReviewAlreadyExists
from app.infra.engine import get_session
from app.models.review import Characteristic, DriveType, Review
from app.models.settings import Settings
from app.repositories import Repository


class DBRepository(Repository):
    async def store_reviews_with_override(self, cur_reviews: list[dict[str, Any]]):
        reviews = []
        async with get_session() as session:
            for review in cur_reviews:
                new_review = Review(
                    link=review['link'],
                    name=review['name'],
                    year=review['year'],
                    review_text=review['review_text'],
                    total_rating=review['total_rating'],
                    rating_components=review['rating_components'],
                    mileage=review['mileage'],
                    fuel_consumption=review['fuel_consumption'],
                    drive_type=review['drive_type'],
                    pros=review['pros'],
                    cons=review['cons'],
                    date=review['date']
                )
                reviews.append(new_review)
            stmt = insert(Review).values([e.__dict__ for e in cur_reviews])
            stmt = stmt.on_conflict_do_nothing()
            await session.execute(stmt)
            await session.commit()

    async def store_reviews(self, cur_reviews: list[dict[str, Any]]) -> None:
        reviews = []
        async with get_session() as session:
            for review in cur_reviews:
                drive_type = DriveType.get_name_by_value(review['drive_type'])
                pros = [Characteristic.get_name_by_value(pro) for pro in review['pros']] if review['pros'] else []
                pros_text = ', '.join(review['pros']) if review['pros'] else None
                cons = [Characteristic.get_name_by_value(con) for con in review['cons']] if review['cons'] else []
                cons_text = ', '.join(review['cons']) if review['cons'] else None
                new_review = Review(
                    link=review['link'],
                    name=review['name'],
                    year=review['year'],
                    review_text=review['review_text'],
                    total_rating=review['total_rating'],
                    rating_components=review['rating_components'],
                    mileage=review['mileage'],
                    fuel_consumption=review['fuel_consumption'],
                    drive_type=drive_type,
                    pros=pros,
                    pros_text=pros_text,
                    cons=cons,
                    cons_text=cons_text,
                    date=review['date']
                )
                reviews.append(new_review)
            session.add_all(reviews)
            try:
                await session.commit()
            except IntegrityError as e:
                if 'duplicate key value violates unique constraint' in e.args[0]:
                    await session.rollback()
                    failed = []
                    for review in reviews:
                        try:
                            session.add(review)
                            await session.commit()
                        except IntegrityError:
                            await session.rollback()
                            failed.append(review)
                    if failed:
                        msg = f"Duplicate reviews found: {len(failed)}. Signaling crawler to stop."
                        raise ReviewAlreadyExists(msg)

    async def store_page_number(self, page_number: int) -> None:
        async with get_session() as session:
            try:
                stmt = insert(Settings).values(id=1, page_number=page_number)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['id'],
                    set_=dict(page_number=page_number)
                )
                await session.execute(stmt)
                await session.commit()
            except IntegrityError as e:
                raise e

    async def get_page_number(self) -> int:
        async with get_session() as session:
            current_page = await session.execute(select(Settings.page_number))
            if page := current_page.scalar():
                return page
            else:
                return 0
