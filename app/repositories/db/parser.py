from typing import Any, Optional, Sequence

from sqlalchemy import Numeric, cast, func, select

from app.infra.engine import get_session
from app.models.review import ReviewParsed


class ParserRepository:
    @classmethod
    async def get_avg_rating_per_year(
        cls,
        model: Optional[str] = None,
        brand: Optional[str] = None,
        min_reviews_per_year: int = 3
    ) -> list[dict[str, Any]]:
        async with get_session() as session:
            stmt = (
                select(
                    func.round(cast(func.avg(ReviewParsed.total_rating), Numeric), 2).label("avg_rating"),
                    ReviewParsed.year,
                    func.count().label("review_count")
                )
                .group_by(ReviewParsed.year)
                .order_by(ReviewParsed.year.asc())
            )

            if model:
                stmt = stmt.where(ReviewParsed.model == model)
            if brand:
                stmt = stmt.where(ReviewParsed.brand == brand)

            stmt = stmt.having(func.count() > min_reviews_per_year)

            result = await session.execute(stmt)
            rows: Sequence[Any] = result.all()

            return [
                {"year": row.year, "avg_rating": float(row.avg_rating), "review_count": row.review_count}
                for row in rows
            ]
