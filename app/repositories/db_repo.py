from typing import Any

from sqlalchemy import cast, column, func, select, update
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER, insert
from sqlalchemy.exc import IntegrityError

from app.exceptions import ReviewAlreadyExists
from app.infra.engine import get_session
from app.models.review import Characteristic, DriveType, Review
from app.models.settings import Settings
from app.repositories import Repository


class DBRepository(Repository):
    async def store_reviews_with_override(self, cur_reviews: list[dict[str, Any]]) -> None:
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
        db_reviews: list[Review] = []
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
                db_reviews.append(new_review)
            session.add_all(db_reviews)
            try:
                await session.commit()
            except IntegrityError as e:
                if 'duplicate key value violates unique constraint' in e.args[0]:
                    await session.rollback()
                    failed = []
                    for db_review in db_reviews:
                        try:
                            session.add(db_review)
                            await session.commit()
                        except IntegrityError:
                            await session.rollback()
                            failed.append(db_review)
                    if failed:
                        msg = f"Duplicate reviews found: {len(failed)}. Signaling crawler to stop."
                        raise ReviewAlreadyExists(msg)

    async def store_visited_page(self, page_number: int) -> None:
        async with get_session() as session:
            stmt = update(Settings).where(Settings.id == 1).values(
                visited_pages=func.array_append(Settings.visited_pages, page_number)
            )
            await session.execute(stmt)
            await session.commit()

    async def store_total_pages(self, total_pages: int) -> None:
        async with get_session() as session:
            stmt = insert(Settings).values(id=1, total_pages=total_pages)
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=dict(total_pages=total_pages)
            )
            await session.execute(stmt)
            await session.commit()

    async def get_visited_pages(self) -> list[int]:
        async with get_session() as session:
            visited_pages = await session.execute(select(Settings.visited_pages).where(Settings.id == 1))
            return visited_pages.scalar_one()

    async def get_total_pages(self) -> int:
        async with get_session() as session:
            total_pages = await session.execute(select(Settings.total_pages).where(Settings.id == 1))
            return total_pages.scalar_one()

    async def adjust_visited_pages(self, k: int) -> list[int]:
        async with get_session() as session:
            shifted_array_subquery = select(
                func.coalesce(
                    func.array_agg(column("x") + k),
                    cast(func.array([]), ARRAY(INTEGER))  # Fallback to empty array
                )
            ).select_from(
                func.unnest(Settings.visited_pages).alias("x")
            ).scalar_subquery()

            stmt = (
                update(Settings)
                .where(Settings.id == 1)
                .values(visited_pages=shifted_array_subquery)
                .returning(Settings.visited_pages)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.scalar_one()
