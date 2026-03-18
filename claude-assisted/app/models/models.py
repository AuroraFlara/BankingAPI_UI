from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Double,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    country_code: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    account: Mapped[Optional["Account"]] = relationship(
        "Account", back_populates="user", uselist=False
    )


class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pin: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_number: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    account_status: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_type: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[float] = mapped_column(Double, nullable=False)
    branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ifsc_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, unique=True
    )

    user: Mapped["User"] = relationship("User", back_populates="account")
    tokens: Mapped[list["Token"]] = relationship("Token", back_populates="account")
    source_transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="Transaction.source_account_id",
        back_populates="source_account",
    )
    target_transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="Transaction.target_account_id",
        back_populates="target_account",
    )


class Token(Base):
    __tablename__ = "token"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    expiry_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("account.id"), nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="tokens")


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Double, nullable=False)
    transaction_date: Mapped[Optional[datetime]] = mapped_column(
        DATETIME(fsp=6), nullable=True
    )
    transaction_type: Mapped[Optional[str]] = mapped_column(
        Enum(
            "CASH_CREDIT",
            "CASH_DEPOSIT",
            "CASH_TRANSFER",
            "CASH_WITHDRAWAL",
            name="transaction_type_enum",
        ),
        nullable=True,
    )
    source_account_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("account.id"), nullable=True
    )
    target_account_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("account.id"), nullable=True
    )

    source_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[source_account_id],
        back_populates="source_transactions",
    )
    target_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[target_account_id],
        back_populates="target_transactions",
    )
