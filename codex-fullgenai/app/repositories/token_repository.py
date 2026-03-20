from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Token


class TokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, token: Token) -> Token:
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token
