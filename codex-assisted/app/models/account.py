from sqlalchemy import BigInteger, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_number: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    account_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_type: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ifsc_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True)

    user = relationship("User", back_populates="account")
