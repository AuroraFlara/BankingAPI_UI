"""
PIN management routes: (3 endpoints)
POST /api/account/pin/create
POST /api/account/pin/update
GET  /api/account/pin/check
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_account
from app.models import Account
from app.schemas import PinCreateRequest, PinUpdateRequest
from app.services import PinService

router = APIRouter(prefix="/api/account", tags=["pin"])


@router.post("/pin/create", status_code=200)
async def create_pin(
    req: PinCreateRequest,
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = PinService(db)
    return await service.create_pin(account, req)


@router.post("/pin/update", status_code=200)
async def update_pin(
    req: PinUpdateRequest,
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = PinService(db)
    return await service.update_pin(account, req)


@router.get("/pin/check", status_code=200)
async def check_pin(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = PinService(db)
    return await service.check_pin(account)
