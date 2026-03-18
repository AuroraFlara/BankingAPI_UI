from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models import User, Account, Transaction, Token
from typing import Optional, List


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def find_by_phone(self, phone_number: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

    async def save(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user


class AccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_account_number(self, account_number: str) -> Optional[Account]:
        result = await self.db.execute(
            select(Account).where(Account.account_number == account_number)
        )
        return result.scalar_one_or_none()

    async def find_by_user_id(self, user_id: int) -> Optional[Account]:
        result = await self.db.execute(
            select(Account).where(Account.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def exists_by_account_number(self, account_number: str) -> bool:
        result = await self.db.execute(
            select(Account.id).where(Account.account_number == account_number)
        )
        return result.scalar_one_or_none() is not None

    async def save(self, account: Account) -> Account:
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account


class TransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction

    async def find_by_account_id_ordered(self, account_id: int) -> List[Transaction]:
        result = await self.db.execute(
            select(Transaction)
            .where(
                (Transaction.source_account_id == account_id)
                | (Transaction.target_account_id == account_id)
            )
            .order_by(desc(Transaction.transaction_date))
        )
        return result.scalars().all()


class TokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, token: Token) -> Token:
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token
