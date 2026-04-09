from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings

engine_antifraud = create_async_engine(settings.DATABASE_URL)

async_session_maker = sessionmaker(engine_antifraud, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass
