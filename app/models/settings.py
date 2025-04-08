from sqlalchemy.orm import Mapped, mapped_column

from app.infra.engine import Base


class Settings(Base):
    __tablename__ = 'settings'
    id: Mapped[int] = mapped_column(primary_key=True)
    page_number: Mapped[int] = mapped_column()
