from datetime import datetime

from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TransactionType
from app.models.transaction import Transaction


class TransactionRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        amount: float,
        tx_type: TransactionType,
        source_account_id: int | None,
        target_account_id: int | None,
    ) -> Transaction:
        transaction = Transaction(
            amount=amount,
            transaction_date=datetime.utcnow(),
            transaction_type=tx_type,
            source_account_id=source_account_id,
            target_account_id=target_account_id,
        )
        db.add(transaction)
        await db.flush()
        await db.refresh(transaction)
        return transaction

    async def list_for_account(self, db: AsyncSession, account_id: int) -> list[Transaction]:
        result = await db.execute(
            select(Transaction)
            .where(
                or_(
                    Transaction.source_account_id == account_id,
                    Transaction.target_account_id == account_id,
                )
            )
            .order_by(desc(Transaction.transaction_date))
        )
        return list(result.scalars().all())
