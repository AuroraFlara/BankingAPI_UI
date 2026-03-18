from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import Token


class TokenRepository:
    async def get_by_token(self, db: AsyncSession, token: str) -> Token | None:
        result = await db.execute(select(Token).where(Token.token == token))
        return result.scalar_one_or_none()

    async def create_token(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        token: str,
        expiry_at: datetime,
    ) -> Token:
        token_row = Token(
            account_id=account_id,
            token=token,
            created_at=datetime.utcnow(),
            expiry_at=expiry_at,
        )
        db.add(token_row)
        await db.flush()
        await db.refresh(token_row)
        return token_row
