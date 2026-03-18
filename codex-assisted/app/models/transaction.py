from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import TransactionType


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    transaction_type: Mapped[TransactionType | None] = mapped_column(Enum(TransactionType), nullable=True)
    source_account_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    target_account_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
