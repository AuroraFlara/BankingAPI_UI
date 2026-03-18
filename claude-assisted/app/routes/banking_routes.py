from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_account, get_db
from app.models.models import Account
from app.schemas.account_schemas import (
    BalanceResponse,
    DepositRequest,
    FundTransferRequest,
    WithdrawRequest,
)
from app.schemas.transaction_schemas import TransactionsResponse
from app.services.banking_service import BankingService

router = APIRouter(prefix="/api/account", tags=["Banking"])


@router.post("/deposit", response_model=BalanceResponse)
async def deposit(
    payload: DepositRequest,
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = BankingService(db)
    return await service.deposit(account, payload.amount, payload.pin)


@router.post("/withdraw", response_model=BalanceResponse)
async def withdraw(
    payload: WithdrawRequest,
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = BankingService(db)
    return await service.withdraw(account, payload.amount, payload.pin)


@router.post("/fund-transfer", response_model=BalanceResponse)
async def fund_transfer(
    payload: FundTransferRequest,
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = BankingService(db)
    return await service.fund_transfer(
        account,
        payload.target_account_number,
        payload.amount,
        payload.pin,
    )


@router.get("/transactions", response_model=TransactionsResponse)
async def get_transactions(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    service = BankingService(db)
    return await service.get_transactions(account)
