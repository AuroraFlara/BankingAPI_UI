from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import APIError, ValidationAPIError
from app.core.security import verify_hash
from app.models import Transaction, TransactionType
from app.repositories import AccountRepository, TransactionRepository
from app.schemas import AmountPinRequest, TransferRequest, format_dt


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.tx_repo = TransactionRepository(db)

    async def deposit(self, account, payload: AmountPinRequest) -> dict:
        self._validate_pin(account, payload.pin)
        self._validate_amount(payload.amount)

        account.balance = float(account.balance) + float(payload.amount)
        tx = Transaction(
            amount=float(payload.amount),
            transaction_date=datetime.utcnow(),
            transaction_type=TransactionType.CASH_DEPOSIT,
            source_account_id=None,
            target_account_id=account.id,
        )

        await self.account_repo.save(account)
        await self.tx_repo.create(tx)
        await self._commit_or_rollback()

        return {
            "hasPIN": True,
            "currentBalance": float(account.balance),
            "msg": "Cash deposited successfully",
        }

    async def withdraw(self, account, payload: AmountPinRequest) -> dict:
        self._validate_pin(account, payload.pin)
        self._validate_amount(payload.amount)

        if float(account.balance) < float(payload.amount):
            raise APIError(status_code=400, message="Insufficient balance")

        account.balance = float(account.balance) - float(payload.amount)
        tx = Transaction(
            amount=float(payload.amount),
            transaction_date=datetime.utcnow(),
            transaction_type=TransactionType.CASH_WITHDRAWAL,
            source_account_id=account.id,
            target_account_id=None,
        )

        await self.account_repo.save(account)
        await self.tx_repo.create(tx)
        await self._commit_or_rollback()

        return {
            "hasPIN": True,
            "currentBalance": float(account.balance),
            "msg": "Cash withdrawn successfully",
        }

    async def transfer(self, account, payload: TransferRequest) -> dict:
        self._validate_pin(account, payload.pin)
        self._validate_amount(payload.amount, transfer_mode=True)

        if account.account_number == payload.target_account_number:
            raise APIError(status_code=400, message="Source and target account cannot be the same")

        target = await self.account_repo.get_by_account_number(payload.target_account_number)
        if not target:
            raise APIError(status_code=404, message="Account does not exist")

        if float(account.balance) < float(payload.amount):
            raise APIError(status_code=400, message="Insufficient balance")

        account.balance = float(account.balance) - float(payload.amount)
        target.balance = float(target.balance) + float(payload.amount)

        transfer_tx = Transaction(
            amount=float(payload.amount),
            transaction_date=datetime.utcnow(),
            transaction_type=TransactionType.CASH_TRANSFER,
            source_account_id=account.id,
            target_account_id=target.id,
        )

        await self.account_repo.save(account)
        await self.account_repo.save(target)
        await self.tx_repo.create(transfer_tx)
        await self._commit_or_rollback()

        return {
            "hasPIN": True,
            "currentBalance": float(account.balance),
            "msg": "Fund transferred successfully",
        }

    async def history(self, account) -> dict:
        rows = await self.tx_repo.list_by_account_id(account.id)
        transactions = []
        for row in rows:
            tx = row["transaction"]
            transactions.append(
                {
                    "id": tx.id,
                    "amount": float(tx.amount),
                    "transactionType": tx.transaction_type.value if tx.transaction_type else None,
                    "transactionDate": format_dt(tx.transaction_date),
                    "sourceAccountNumber": row["source_account_number"],
                    "targetAccountNumber": row["target_account_number"],
                }
            )
        if not transactions:
            return {"transactions": [], "msg": "No transactions found"}
        return {"transactions": transactions, "msg": "Transactions retrieved successfully"}

    @staticmethod
    def _validate_pin(account, raw_pin: str) -> None:
        if not account.pin:
            raise APIError(status_code=401, message="PIN not created")
        if not verify_hash(raw_pin, account.pin):
            raise APIError(status_code=401, message="Invalid PIN")

    @staticmethod
    def _validate_amount(amount: float, transfer_mode: bool = False) -> None:
        if amount <= 0:
            if transfer_mode:
                raise ValidationAPIError(status_code=400, errors={"amount": "Amount must be greater than 0"})
            raise APIError(status_code=400, message="Amount must be greater than 0")
        if amount % 100 != 0:
            raise APIError(status_code=400, message="Amount must be in multiples of 100")

    async def _commit_or_rollback(self) -> None:
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
