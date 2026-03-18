from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_account_number_from_token
from app.db.database import get_db
from app.services.account_service import AccountService
from app.services.user_service import UserService


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
user_service = UserService()
account_service = AccountService()


@router.get("/user")
async def dashboard_user(
    account_number: str = Depends(get_account_number_from_token),
    db: AsyncSession = Depends(get_db),
):
    return await user_service.dashboard_user(db, account_number)


@router.get("/account")
async def dashboard_account(
    account_number: str = Depends(get_account_number_from_token),
    db: AsyncSession = Depends(get_db),
):
    return await account_service.dashboard_account(db, account_number)
