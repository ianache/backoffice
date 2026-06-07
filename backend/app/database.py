from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(settings.database_url, echo=settings.debug)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)
