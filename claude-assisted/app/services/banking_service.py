"""
BankingService: deposit, withdraw, fund transfer, transaction history.

Parity targets:
  AccountServiceImpl.cashDeposit()    -> deposit()
  AccountServiceImpl.cashWithdrawal() -> withdraw()
  AccountServiceImpl.fundTransfer()   -> fund_transfer()
  TransactionRepository queries       -> get_transactions()
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Account, Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction_schemas import TransactionOut, TransactionsResponse
from app.security import verify_password


def _map_tx(row) -> TransactionOut:
    """
    Map a (Transaction, src_account_number, tgt_account_number) row
    returned by TransactionRepository.find_by_account_id_desc().
    transactionDate is passed as a raw datetime; @field_serializer in
    TransactionOut formats it to "YYYY-MM-DD HH:MM:SS".
    """
    tx, src_num, tgt_num = row
    return TransactionOut(
        id=tx.id,
        amount=tx.amount,
        transactionDate=tx.transaction_date,
        transactionType=tx.transaction_type,
        sourceAccountNumber=src_num,
        targetAccountNumber=tgt_num,
    )


class BankingService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._account_repo = AccountRepository(db)
        self._tx_repo = TransactionRepository(db)

    # ------------------------------------------------------------------
    # Deposit
    # ------------------------------------------------------------------
    async def deposit(self, account: Account, amount: float, pin: str) -> dict:
        # 1. Auth: verify PIN (401 on failure — ground truth parity)
        if account.pin is None or not verify_password(pin, account.pin):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN")
        # 2. Amount > 0
        if amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than 0")
        # 3. Multiple of 100
        if amount % 100 != 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be in multiples of 100")

        account.balance += amount
        await self._account_repo.save(account)

        tx = Transaction(
            amount=amount,
            transaction_type="CASH_DEPOSIT",
            transaction_date=datetime.now(tz=timezone.utc),
            # Ground truth: CASH_DEPOSIT → sourceAccountNumber=null, targetAccountNumber=<account>
            target_account_id=account.id,
        )
        await self._tx_repo.save(tx)

        return {"hasPIN": True, "currentBalance": account.balance, "msg": "Cash deposited successfully"}

    # ------------------------------------------------------------------
    # Withdraw
    # ------------------------------------------------------------------
    async def withdraw(self, account: Account, amount: float, pin: str) -> dict:
        # 1. Auth: verify PIN (401 on failure)
        if account.pin is None or not verify_password(pin, account.pin):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN")
        # 2. Amount > 0
        if amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than 0")
        # 3. Multiple of 100
        if amount % 100 != 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be in multiples of 100")
        # 4. Sufficient balance
        if account.balance < amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")

        account.balance -= amount
        await self._account_repo.save(account)

        tx = Transaction(
            amount=amount,
            transaction_type="CASH_WITHDRAWAL",
            transaction_date=datetime.now(tz=timezone.utc),
            source_account_id=account.id,
        )
        await self._tx_repo.save(tx)

        return {"hasPIN": True, "currentBalance": account.balance, "msg": "Cash withdrawn successfully"}

    # ------------------------------------------------------------------
    # Fund Transfer  (atomic — caller wraps in async with db.begin())
    # ------------------------------------------------------------------
    async def fund_transfer(
        self,
        account: Account,
        target_account_number: str,
        amount: float,
        pin: str,
    ) -> dict:
        """
        Validation order (per ground truth):
          1. PIN              → 401 "Invalid PIN"
          2. Same account     → 400 "Source and target account cannot be the same"
          3. Amount % 100     → 400 "Amount must be in multiples of 100"
          4. Target exists    → 404 "Account does not exist"   (after row locks)
          5. Sufficient funds → 400 "Insufficient balance"

        Row-level locking with SELECT ... FOR UPDATE prevents race conditions
        under high concurrency without locking the full table.
        """
        # --- Cheap checks before acquiring DB locks ---
        if account.pin is None or not verify_password(pin, account.pin):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN"
            )
        if account.account_number == target_account_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and target account cannot be the same",
            )
        if amount % 100 != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be in multiples of 100",
            )

        # --- Acquire row-level locks (within the transaction started by the route) ---
        src_row = await self._db.execute(
            select(Account).where(Account.id == account.id).with_for_update()
        )
        source = src_row.scalars().first()

        tgt_row = await self._db.execute(
            select(Account)
            .where(Account.account_number == target_account_number)
            .with_for_update()
        )
        target = tgt_row.scalars().first()

        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account does not exist"
            )
        if source.balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance"
            )

        source.balance -= amount
        target.balance += amount
        await self._account_repo.save(source)
        await self._account_repo.save(target)

        tx = Transaction(
            amount=amount,
            transaction_type="CASH_TRANSFER",
            transaction_date=datetime.now(tz=timezone.utc),
            source_account_id=source.id,
            target_account_id=target.id,
        )
        await self._tx_repo.save(tx)

        return {
            "hasPIN": True,
            "currentBalance": source.balance,
            "msg": "Fund transferred successfully",
        }

    # ------------------------------------------------------------------
    # Transaction History
    # ------------------------------------------------------------------
    async def get_transactions(self, account: Account) -> TransactionsResponse:
        rows = await self._tx_repo.find_by_account_id_desc(account.id)
        txs = [_map_tx(row) for row in rows]
        msg = "Transactions retrieved successfully" if txs else "No transactions found"
        return TransactionsResponse(transactions=txs, msg=msg)
