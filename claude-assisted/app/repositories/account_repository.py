from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Account


class AccountRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def find_by_user_id(self, user_id: int) -> Optional[Account]:
        result = await self._db.execute(
            select(Account).where(Account.user_id == user_id)
        )
        return result.scalars().first()

    async def find_by_account_number(self, account_number: str) -> Optional[Account]:
        result = await self._db.execute(
            select(Account).where(Account.account_number == account_number)
        )
        return result.scalars().first()

    async def find_by_account_number_with_user(self, account_number: str) -> Optional[Account]:
        """Joined eager load of Account + User in a single query (eliminates N+1)."""
        result = await self._db.execute(
            select(Account)
            .options(joinedload(Account.user))
            .where(Account.account_number == account_number)
        )
        return result.scalars().first()

    async def save(self, account: Account) -> Account:
        self._db.add(account)
        await self._db.flush()
        await self._db.refresh(account)
        return account
