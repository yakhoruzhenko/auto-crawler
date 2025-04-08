from datetime import date as dt_date
from enum import StrEnum

from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EnumValueMixin:
    @classmethod
    def get_name_by_value(cls, value: str) -> str:
        """Return the member name by the provided value."""
        return next((name for name, member in cls.__members__.items() if member.value == value), None)  # type: ignore


class Characteristic(EnumValueMixin, StrEnum):
    ACCELERATION = "динаміка"
    BRAKES = "гальма"
    BUILD_QUALITY = "якість збірки"
    EXTERIOR_DESIGN = "дизайн кузова"
    FUEL_CONSUMPTION = "витрати палива"
    GROUND_CLEARANCE = "дорожній просвіт"
    HANDLING = "керованість"
    INTERIOR_SPACE = "простір салону"
    MATERIAL_QUALITY = "якість матеріалів"
    MAINTENANCE_COST = "вартість обслуговування"
    PRICE = "ціна"
    SOUND_INSULATION = "шумоізоляція"
    TRANSMISSION = "коробка передач"
    TRUNK_SPACE = "об`єм багажника"


class DriveType(EnumValueMixin, StrEnum):
    CITY_TRIPS = "Поїздки в місті"
    COMMERCIAL_TRANSPORT = "Комерційні перевезення"
    FAMILY = "Сім'я"
    TRAVEL = "Подорожі"


class Review(Base):
    __tablename__ = 'reviews'

    link: Mapped[str] = mapped_column(primary_key=True)  # there are "duplicated" reviews for the different links
    name: Mapped[str] = mapped_column()
    year: Mapped[int] = mapped_column()
    review_text: Mapped[str] = mapped_column()
    total_rating: Mapped[float] = mapped_column()
    rating_components: Mapped[dict[str, int]] = mapped_column()
    mileage: Mapped[int] = mapped_column(nullable=True)
    fuel_consumption: Mapped[float] = mapped_column(nullable=True)
    drive_type: Mapped[str] = mapped_column(nullable=True)
    pros: Mapped[list[str]] = mapped_column(nullable=True)
    pros_text: Mapped[str] = mapped_column(nullable=True)
    cons: Mapped[list[str]] = mapped_column(nullable=True)
    cons_text: Mapped[str] = mapped_column(nullable=True)
    date: Mapped[dt_date] = mapped_column()


# {
#    "name":"Citroen C-Elysee",
#    "year":"2023",
#    "link":"reviews/citroen/c-elysee/179990/",
#    "review_text":"Перше авто з салону. Тож після покупки своїм вибором задоволений.",
#    "total_rating":4.8,
#    "rating_components":{
#       "Керування":5,
#       "Надійність":4,
#       "Комфорт":4,
#       "Ціна":5,
#       "Дизайн":4
#    },
#    "mileage":10,
#    "fuel_consumption":8.0,
#    "drive_type":"Сім'я",
#    "pros":[
#       "дизайн кузова",
#       "динаміка",
#       "якість збірки",
#       "коробка передач",
#       "об`єм багажника",
#       "простір салону",
#       "вартість обслуговування",
#       "гальма",
#       "керованість",
#       "ціна"
#    ],
#    "cons":[
#       "дорожній просвіт",
#       "витрати палива",
#       "шумоізоляція"
#    ],
#    "date":"2 дні назад"
# },
