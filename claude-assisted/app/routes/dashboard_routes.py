from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_account, get_db
from app.models.models import Account
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/user")
async def get_user(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    return await service.get_user(account)


@router.get("/account")
async def get_account(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    return await service.get_account(account)
