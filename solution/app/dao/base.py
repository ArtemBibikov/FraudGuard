from fastapi_cli.cli import logger
from sqlalchemy import select, delete, update, func
from ..database import async_session_maker


class BaseDAO:
    model = None

    @classmethod
    async def find_by_id(cls, model_id):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id = model_id)
            result = await session.execute(query)
            return result.scalars().one_or_none()

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().one_or_none()

    @classmethod
    async def find_all(cls, page: int = 0, size: int = 20, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by).offset(page * size).limit(size)
            res = await session.execute(query)
            return res.scalars().all()

    @classmethod
    async def count(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(func.count(cls.model.id)).filter_by(**filter_by)
            res = await session.execute(query)
            return res.scalar()

    @classmethod
    async def add(cls, **data):
        async with async_session_maker() as session:
            instance = cls.model(**data)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    @classmethod
    async def update(cls, model_id, **data):
        async with async_session_maker() as session:
            query = update(cls.model).where(cls.model.id == model_id).values(**data)
            await session.execute(query)
            await session.commit()
            updated = await cls.find_by_id(model_id)
            return updated

    @classmethod
    async def delete(cls, model_id):
        try:
            async with async_session_maker() as session:
                query = delete(cls.model).where(cls.model.id == model_id)
                await session.execute(query)
                await session.commit()
        except Exception as e:
            logger.error(e, exc_info=True)