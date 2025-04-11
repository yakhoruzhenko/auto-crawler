from sqlalchemy import ARRAY, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    type_annotation_map = {
        dict[str, int]: JSONB,  # allows to use Mapped[dict[str, Any]] notation
        list[str]: ARRAY(String),  # allows to use Mapped[list[str]] notation
        list[int]: ARRAY(Integer),  # allows to use Mapped[list[int]] notation
    }
