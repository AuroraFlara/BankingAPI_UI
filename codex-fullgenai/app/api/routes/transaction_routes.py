from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_account
from app.schemas import AmountPinRequest, TransferRequest
from app.services import TransactionService


router = APIRouter(prefix="/api/account", tags=["transactions"])


@router.post("/deposit", status_code=status.HTTP_200_OK)
async def deposit(
    payload: AmountPinRequest,
    account=Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = TransactionService(db)
    return await service.deposit(account, payload)


@router.post("/withdraw", status_code=status.HTTP_200_OK)
async def withdraw(
    payload: AmountPinRequest,
    account=Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = TransactionService(db)
    return await service.withdraw(account, payload)


@router.post("/fund-transfer", status_code=status.HTTP_200_OK)
async def fund_transfer(
    payload: TransferRequest,
    account=Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = TransactionService(db)
    return await service.transfer(account, payload)


@router.post("/transfer", status_code=status.HTTP_200_OK)
async def transfer_alias(
    payload: TransferRequest,
    account=Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = TransactionService(db)
    return await service.transfer(account, payload)


@router.get("/transactions", status_code=status.HTTP_200_OK)
async def transactions(account=Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    service = TransactionService(db)
    return await service.history(account)
