"""
Banking routes: (4 endpoints)
POST /api/account/deposit
POST /api/account/withdraw
POST /api/account/fund-transfer
GET  /api/account/transactions
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_account
from app.models import Account
from app.schemas import DepositRequest, WithdrawRequest, TransferRequest
from app.services import BankingService

router = APIRouter(prefix="/api/account", tags=["banking"])


@router.post("/deposit", status_code=200)
async def deposit(
    req: DepositRequest,
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = BankingService(db)
    return await service.deposit(account, req)


@router.post("/withdraw", status_code=200)
async def withdraw(
    req: WithdrawRequest,
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = BankingService(db)
    return await service.withdraw(account, req)


@router.post("/fund-transfer", status_code=200)
async def fund_transfer(
    req: TransferRequest,
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = BankingService(db)
    return await service.transfer(account, req)


@router.get("/transactions", status_code=200)
async def get_transactions(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = BankingService(db)
    return await service.get_transactions(account)

