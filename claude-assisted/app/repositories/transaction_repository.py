from sqlalchemy import desc, select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Account, Transaction


class TransactionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def save(self, transaction: Transaction) -> Transaction:
        self._db.add(transaction)
        await self._db.flush()
        await self._db.refresh(transaction)
        return transaction

    async def find_by_account_id_desc(self, account_id: int) -> list:
        """
        Return all transactions for the given account (as source OR target),
        ordered DESC by transaction_date.  Each row is a 3-tuple:
          (Transaction, source_account_number | None, target_account_number | None)
        Resolved via two outer joins — eliminates N+1 queries.
        """
        src = aliased(Account)
        tgt = aliased(Account)
        result = await self._db.execute(
            select(
                Transaction,
                src.account_number,
                tgt.account_number,
            )
            .outerjoin(src, Transaction.source_account_id == src.id)
            .outerjoin(tgt, Transaction.target_account_id == tgt.id)
            .where(
                (Transaction.source_account_id == account_id)
                | (Transaction.target_account_id == account_id)
            )
            .order_by(desc(Transaction.transaction_date))
        )
        return result.all()
