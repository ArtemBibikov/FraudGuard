from sqlalchemy import select
from ..config import settings
from ..database import async_session_maker, engine_antifraud
from ..users.auth import get_password_hash
from ..users.models import User
from ..database import Base
from ..enums.enums import UserRole


async def create_tables_user():
        async with engine_antifraud.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def create_admin_user():
    async with async_session_maker() as session:
        query = select(User).where(User.email == settings.ADMIN_EMAIL)
        result = await session.execute(query)
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            new_admin = User(
                email=settings.ADMIN_EMAIL,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                full_name=settings.ADMIN_FULLNAME,
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(new_admin)
            await session.commit()
