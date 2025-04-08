import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import ARRAY, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


def get_db_url() -> str:
    return 'postgresql+asyncpg://%s:%s@%s:%s/%s' % (
        os.getenv('PGUSER', 'postgres'),
        os.getenv('PGPASSWORD', 'password'),
        os.getenv('PGHOST', 'localhost'),
        os.getenv('PGPORT', '5432'),
        os.getenv('PGDATABASE', 'postgres'),
    )


DATABASE_URL = get_db_url()
engine = create_async_engine(DATABASE_URL)


class Base(DeclarativeBase):
    type_annotation_map = {
        dict[str, int]: JSONB,  # allows to use Mapped[dict[str, Any]] notation
        list[str]: ARRAY(String),  # allows to use Mapped[list[str]] notation
    }


SessionMaker = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession,
                                  expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = SessionMaker()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        logger.error(f'DB ERROR: {e}')
        raise e
    finally:
        await session.close()
