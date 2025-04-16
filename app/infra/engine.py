import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)


def get_db_url() -> str:
    return 'postgresql+asyncpg://%s:%s@%s:%s/%s' % (
        os.getenv('PGUSER', 'reviewer'),
        os.getenv('PGPASSWORD', 'password'),
        os.getenv('PGHOST', 'localhost'),
        os.getenv('PGPORT', '5788'),
        os.getenv('PGDATABASE', 'reviews_db'),
    )


DATABASE_URL = get_db_url()
engine = create_async_engine(DATABASE_URL)


SessionMaker = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession,
                                  expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = SessionMaker()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        logging.error(f'DB ERROR: {e}')
        raise e
    finally:
        await session.close()
