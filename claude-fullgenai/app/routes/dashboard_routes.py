"""
Dashboard routes: (2 endpoints)
GET /api/dashboard/user
GET /api/dashboard/account
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_account
from app.models import Account
from app.services import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/user", status_code=200)
async def get_user_dashboard(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    return await service.get_user_details(account)


@router.get("/account", status_code=200)
async def get_account_dashboard(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    return await service.get_account_details(account)
