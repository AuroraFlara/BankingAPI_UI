from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


class AccountRepository:
    async def get_by_id(self, db: AsyncSession, account_id: int) -> Account | None:
        result = await db.execute(select(Account).where(Account.id == account_id))
        return result.scalar_one_or_none()

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> Account | None:
        result = await db.execute(select(Account).where(Account.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_by_account_number(self, db: AsyncSession, account_number: str) -> Account | None:
        result = await db.execute(select(Account).where(Account.account_number == account_number))
        return result.scalar_one_or_none()

    async def get_by_account_number_for_update(self, db: AsyncSession, account_number: str) -> Account | None:
        result = await db.execute(
            select(Account).where(Account.account_number == account_number).with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, db: AsyncSession, account_ids: set[int]) -> list[Account]:
        if not account_ids:
            return []
        result = await db.execute(select(Account).where(Account.id.in_(account_ids)))
        return list(result.scalars().all())

    async def create_account(self, db: AsyncSession, account: Account) -> Account:
        db.add(account)
        await db.flush()
        await db.refresh(account)
        return account
