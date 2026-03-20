from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_account
from app.schemas import PinCreateRequest, PinUpdateRequest
from app.services import PinService


router = APIRouter(prefix="/api/account/pin", tags=["pin"])


@router.post("/create", status_code=status.HTTP_200_OK)
async def create_pin(
    payload: PinCreateRequest,
    account=Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = PinService(db)
    return await service.create_pin(account, payload)


@router.post("/update", status_code=status.HTTP_200_OK)
async def update_pin(
    payload: PinUpdateRequest,
    account=Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = PinService(db)
    return await service.update_pin(account, payload)


@router.get("/check", status_code=status.HTTP_200_OK)
async def check_pin(account=Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    _ = db
    return PinService.check_pin(account)
