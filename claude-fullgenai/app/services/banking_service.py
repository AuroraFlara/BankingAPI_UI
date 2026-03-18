"""
Banking service: Deposit, Withdraw, Transfer, Transaction History.
"""
from __future__ import annotations
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models import Account, Transaction
from app.repositories import AccountRepository, TransactionRepository
from app.security import verify_pin
from app.schemas import DepositRequest, WithdrawRequest, TransferRequest


def _format_date(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _parse_amount(raw: str) -> float:
    """Parse the amount string to float. Raises HTTPException on invalid format."""
    try:
        val = float(raw)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Invalid amount: {raw}"},
        )
    return val


def _validate_amount(amount: float) -> None:
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Amount must be greater than 0"},
        )
    # Use round to handle floating-point precision
    if round(amount % 100, 10) != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Amount must be in multiples of 100"},
        )


def _validate_pin(plain_pin: str, account: Account) -> None:
    if account.pin is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "PIN not set"},
        )
    if not verify_pin(plain_pin, account.pin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid PIN"},
        )


class BankingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.txn_repo = TransactionRepository(db)

    async def deposit(self, account: Account, req: DepositRequest) -> dict:
        amount = _parse_amount(req.amount)
        _validate_amount(amount)
        _validate_pin(req.pin, account)

        account.balance = account.balance + amount
        await self.account_repo.save(account)

        txn = Transaction(
            amount=amount,
            transaction_date=datetime.utcnow(),
            transaction_type="CASH_DEPOSIT",
            target_account_id=account.id,
        )
        await self.txn_repo.save(txn)
        await self.db.commit()
        return {
            "hasPIN": True,
            "currentBalance": account.balance,
            "msg": "Cash deposited successfully",
        }

    async def withdraw(self, account: Account, req: WithdrawRequest) -> dict:
        amount = _parse_amount(req.amount)
        _validate_amount(amount)
        _validate_pin(req.pin, account)

        if account.balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Insufficient balance"},
            )

        account.balance = account.balance - amount
        await self.account_repo.save(account)

        txn = Transaction(
            amount=amount,
            transaction_date=datetime.utcnow(),
            transaction_type="CASH_WITHDRAWAL",
            source_account_id=account.id,
        )
        await self.txn_repo.save(txn)
        await self.db.commit()
        return {
            "hasPIN": True,
            "currentBalance": account.balance,
            "msg": "Cash withdrawn successfully",
        }

    async def transfer(self, account: Account, req: TransferRequest) -> dict:
        amount = _parse_amount(req.amount)
        _validate_amount(amount)
        _validate_pin(req.pin, account)

        if account.account_number == req.targetAccountNumber:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Source and target account cannot be the same"},
            )

        target = await self.account_repo.find_by_account_number(req.targetAccountNumber)
        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Account does not exist"},
            )

        if account.balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Insufficient balance"},
            )

        account.balance = account.balance - amount
        target.balance = target.balance + amount

        await self.account_repo.save(account)
        await self.account_repo.save(target)

        txn = Transaction(
            amount=amount,
            transaction_date=datetime.utcnow(),
            transaction_type="CASH_TRANSFER",
            source_account_id=account.id,
            target_account_id=target.id,
        )
        await self.txn_repo.save(txn)
        await self.db.commit()
        return {
            "hasPIN": True,
            "currentBalance": account.balance,
            "msg": "Fund transferred successfully",
        }

    async def get_transactions(self, account: Account) -> dict:
        txns = await self.txn_repo.find_by_account_id_ordered(account.id)

        if not txns:
            return {"transactions": [], "msg": "No transactions found"}

        # Build a map of account_id → account_number for all referenced accounts
        account_ids = set()
        for t in txns:
            if t.source_account_id:
                account_ids.add(t.source_account_id)
            if t.target_account_id:
                account_ids.add(t.target_account_id)

        id_to_number: dict[int, str] = {}
        if account_ids:
            result = await self.db.execute(
                select(Account.id, Account.account_number).where(
                    Account.id.in_(account_ids)
                )
            )
            for row in result.all():
                id_to_number[row[0]] = row[1]

        items = []
        for t in txns:
            items.append({
                "id": t.id,
                "amount": t.amount,
                "transactionDate": _format_date(t.transaction_date),
                "transactionType": t.transaction_type,
                "sourceAccountNumber": id_to_number.get(t.source_account_id) if t.source_account_id else None,
                "targetAccountNumber": id_to_number.get(t.target_account_id) if t.target_account_id else None,
            })

        return {"transactions": items, "msg": "Transactions retrieved successfully"}

