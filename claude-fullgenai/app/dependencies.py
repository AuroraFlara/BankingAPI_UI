"""
FastAPI dependency: extract and validate the Bearer JWT,
then return the resolved Account ORM object.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.security import decode_access_token
from app.repositories import AccountRepository
from app.models import Account
import jwt as pyjwt

bearer_scheme = HTTPBearer()


async def get_current_account(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Account:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"},
        )

    account_number: str = payload.get("sub")
    if not account_number:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid token payload"},
        )

    repo = AccountRepository(db)
    account = await repo.find_by_account_number(account_number)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Account not found"},
        )
    return account
