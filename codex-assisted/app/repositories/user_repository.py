from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.user import User


class UserRepository:
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_phone_number(self, db: AsyncSession, phone_number: str) -> User | None:
        result = await db.execute(select(User).where(User.phone_number == phone_number))
        return result.scalar_one_or_none()

    async def get_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_with_account_by_account_number(self, db: AsyncSession, account_number: str) -> User | None:
        result = await db.execute(
            select(User)
            .options(joinedload(User.account))
            .where(User.account.has(account_number=account_number))
        )
        return result.scalar_one_or_none()

    async def create_user(self, db: AsyncSession, user: User) -> User:
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
