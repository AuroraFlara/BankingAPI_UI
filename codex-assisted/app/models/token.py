from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Token(Base):
    __tablename__ = "token"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    expiry_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=False)
