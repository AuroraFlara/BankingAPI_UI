from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_account, get_db
from app.models.models import Account
from app.schemas.account_schemas import (
    CreatePINRequest,
    PINCheckResponse,
    PINCreateUpdateResponse,
    UpdatePINRequest,
)
from app.services.pin_service import PINService

router = APIRouter(prefix="/api/account/pin", tags=["PIN"])


@router.post("/create", response_model=PINCreateUpdateResponse)
async def create_pin(
    payload: CreatePINRequest,
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = PINService(db)
    return await service.create_pin(account, payload.pin, payload.password)


@router.post("/update", response_model=PINCreateUpdateResponse)
async def update_pin(
    payload: UpdatePINRequest,
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = PINService(db)
    return await service.update_pin(
        account,
        payload.oldPin,
        payload.newPin,
        payload.password,
    )


@router.get("/check", response_model=PINCheckResponse)
async def check_pin(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = PINService(db)
    return await service.is_pin_created(account)
