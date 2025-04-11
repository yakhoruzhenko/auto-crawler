from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Settings(Base):
    __tablename__ = 'settings'
    id: Mapped[int] = mapped_column(primary_key=True)
    visited_pages: Mapped[list[int]] = mapped_column(server_default="'{}'")
    total_pages: Mapped[int] = mapped_column(server_default="0")
