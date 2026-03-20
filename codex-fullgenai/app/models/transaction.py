import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TransactionType(str, enum.Enum):
    CASH_CREDIT = "CASH_CREDIT"
    CASH_DEPOSIT = "CASH_DEPOSIT"
    CASH_TRANSFER = "CASH_TRANSFER"
    CASH_WITHDRAWAL = "CASH_WITHDRAWAL"


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    transaction_type: Mapped[TransactionType | None] = mapped_column(Enum(TransactionType), nullable=True)
    source_account_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    target_account_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)

    source_account = relationship("Account", foreign_keys=[source_account_id], back_populates="source_transactions")
    target_account = relationship("Account", foreign_keys=[target_account_id], back_populates="target_transactions")
