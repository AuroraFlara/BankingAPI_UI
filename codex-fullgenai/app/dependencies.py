from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import APIError
from app.core.security import decode_access_token, is_invalid_token
from app.db.session import get_db
from app.repositories import AccountRepository


async def get_current_account(
    db: AsyncSession = Depends(get_db), authorization: str | None = Header(default=None)
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise APIError(status_code=401, message="Unauthorized")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise APIError(status_code=401, message="Unauthorized")

    try:
        payload = decode_access_token(token)
    except Exception as exc:  # nosec B110
        if is_invalid_token(exc):
            raise APIError(status_code=401, message="Unauthorized") from exc
        raise

    account_number = payload.get("sub")
    if not account_number:
        raise APIError(status_code=401, message="Unauthorized")

    account_repo = AccountRepository(db)
    account = await account_repo.get_by_account_number(account_number)
    if not account:
        raise APIError(status_code=401, message="Unauthorized")

    return account
