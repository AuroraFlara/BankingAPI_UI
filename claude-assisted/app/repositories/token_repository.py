from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Token


class TokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def find_by_token(self, token_str: str) -> Optional[Token]:
        result = await self._db.execute(
            select(Token).where(Token.token == token_str)
        )
        return result.scalars().first()

    async def save(self, token: Token) -> Token:
        self._db.add(token)
        await self._db.flush()
        await self._db.refresh(token)
        return token

    async def delete_by_account_id(self, account_id: int) -> None:
        """Remove all tokens for the given account (logout / re-login)."""
        result = await self._db.execute(
            select(Token).where(Token.account_id == account_id)
        )
        for token_row in result.scalars().all():
            await self._db.delete(token_row)
        await self._db.flush()
