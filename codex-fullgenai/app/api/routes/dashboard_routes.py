from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_account
from app.services import DashboardService


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/user", status_code=status.HTTP_200_OK)
async def user_dashboard(account=Depends(get_current_account)):
    return DashboardService.user_dashboard(account)


@router.get("/account", status_code=status.HTTP_200_OK)
async def account_dashboard(account=Depends(get_current_account)):
    return DashboardService.account_dashboard(account)
