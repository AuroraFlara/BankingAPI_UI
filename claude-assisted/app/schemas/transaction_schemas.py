from datetime import datetime
from typing import Optional

from pydantic import field_serializer

from app.schemas.base import CamelModel


class TransactionOut(CamelModel):
    """
    Single transaction entry in the history response.
    transactionDate is stored as a datetime and serialized to
    "YYYY-MM-DD HH:MM:SS" format per Java ground truth.
    Account numbers are resolved via JOIN in TransactionRepository
    (no N+1 queries).
    """

    id: int
    amount: float
    transactionDate: Optional[datetime] = None
    transactionType: Optional[str] = None
    sourceAccountNumber: Optional[str] = None
    targetAccountNumber: Optional[str] = None

    model_config = {"from_attributes": False}

    @field_serializer("transactionDate")
    def serialize_date(self, v: Optional[datetime]) -> Optional[str]:
        if v is None:
            return None
        return v.strftime("%Y-%m-%d %H:%M:%S")


class TransactionsResponse(CamelModel):
    transactions: list[TransactionOut]
    msg: str
