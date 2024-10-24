from typing import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from config import Config, PostgreSQLConfig


engine = create_async_engine(
    PostgreSQLConfig.SQLALCHEMY_URL,
    echo=Config.DEBUG
)
metadata = MetaData()

Base = declarative_base(metadata=metadata)


def session_factory() -> AsyncSession:
    return sessionmaker(
        bind=engine,
        class_=AsyncSession
    )()


async def get_db() -> AsyncIterator[AsyncSession]:
    session = session_factory()
    try:
        yield session
        await session.commit()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()
