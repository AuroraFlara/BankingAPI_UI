from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Account


class AccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_account_number(self, account_number: str) -> Account | None:
        result = await self.db.execute(
            select(Account)
            .options(selectinload(Account.user))
            .where(Account.account_number == account_number)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Account | None:
        result = await self.db.execute(
            select(Account)
            .options(selectinload(Account.user))
            .where(Account.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def account_number_exists(self, account_number: str) -> bool:
        result = await self.db.execute(select(Account.id).where(Account.account_number == account_number))
        return result.first() is not None

    async def create(self, account: Account) -> Account:
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account

    async def save(self, account: Account) -> Account:
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account
