"""Repository helpers: simple database access functions.

These wrap SQLAlchemy calls and return model instances. Keep queries
here so the service layer remains focused on business rules.
"""

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, Account, Transaction, Token
from datetime import datetime


async def get_user_by_email(db: AsyncSession, email: str):
    q = await db.execute(select(User).where(User.email == email))
    return q.scalars().first()


async def get_user_by_phone(db: AsyncSession, phone: str):
    q = await db.execute(select(User).where(User.phone_number == phone))
    return q.scalars().first()


async def create_user(db: AsyncSession, **kwargs):
    obj = User(**kwargs)
    db.add(obj)
    await db.flush()
    return obj


async def create_account(db: AsyncSession, **kwargs):
    obj = Account(**kwargs)
    db.add(obj)
    await db.flush()
    return obj


async def get_account_by_number(db: AsyncSession, acc_num: str):
    q = await db.execute(
        select(Account).options(selectinload(Account.user)).where(Account.account_number == acc_num)
    )
    return q.scalars().first()


async def get_account_by_id(db: AsyncSession, acc_id: int):
    q = await db.execute(select(Account).where(Account.id == acc_id))
    return q.scalars().first()


async def save_transaction(db: AsyncSession, **kwargs):
    obj = Transaction(**kwargs)
    db.add(obj)
    await db.flush()
    return obj


async def list_transactions_for_account(db: AsyncSession, account_id: int):
    q = await db.execute(
        select(Transaction)
        .where(
            (Transaction.source_account_id == account_id)
            | (Transaction.target_account_id == account_id)
        )
        .order_by(Transaction.transaction_date.desc())
    )
    return q.scalars().all()


async def save_token(db: AsyncSession, token_str: str, account_id: int):
    # Avoid inserting duplicate token strings (JWTs may be deterministic).
    q = await db.execute(select(Token).where(Token.token == token_str))
    existing = q.scalars().first()
    if existing:
        return existing
    now = datetime.utcnow()
    obj = Token(token=token_str, account_id=account_id, created_at=now, expiry_at=now)
    db.add(obj)
    await db.flush()
    return obj


async def revoke_token(db: AsyncSession, token_str: str):
    q = await db.execute(select(Token).where(Token.token == token_str))
    obj = q.scalars().first()
    if obj:
        await db.delete(obj)
    return obj
