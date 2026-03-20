from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models import Account, Transaction


class TransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction

    async def list_by_account_id(self, account_id: int) -> list[dict]:
        src = aliased(Account)
        tgt = aliased(Account)
        stmt = (
            select(
                Transaction,
                src.account_number.label("source_account_number"),
                tgt.account_number.label("target_account_number"),
            )
            .outerjoin(src, Transaction.source_account_id == src.id)
            .outerjoin(tgt, Transaction.target_account_id == tgt.id)
            .where(or_(Transaction.source_account_id == account_id, Transaction.target_account_id == account_id))
            .order_by(Transaction.transaction_date.desc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "transaction": row[0],
                "source_account_number": row[1],
                "target_account_number": row[2],
            }
            for row in rows
        ]
