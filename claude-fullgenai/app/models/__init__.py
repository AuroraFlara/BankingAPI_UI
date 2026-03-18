from app.database import Base
from sqlalchemy import (
    BigInteger, String, Double, Enum, ForeignKey, Column
)
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import relationship
import enum


class TransactionType(str, enum.Enum):
    CASH_CREDIT = "CASH_CREDIT"
    CASH_DEPOSIT = "CASH_DEPOSIT"
    CASH_TRANSFER = "CASH_TRANSFER"
    CASH_WITHDRAWAL = "CASH_WITHDRAWAL"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    address = Column(String(255), nullable=False)
    country_code = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False, unique=True)

    account = relationship("Account", back_populates="user", uselist=False)


class Account(Base):
    __tablename__ = "account"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pin = Column(String(255), nullable=True)
    account_number = Column(String(255), nullable=False, unique=True)
    account_status = Column(String(255), nullable=True)
    account_type = Column(String(255), nullable=False)
    balance = Column(Double, nullable=False, default=0.0)
    branch = Column(String(255), nullable=True)
    ifsc_code = Column(String(255), nullable=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True)

    user = relationship("User", back_populates="account")
    tokens = relationship("Token", back_populates="account")
    outgoing_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.source_account_id",
        back_populates="source_account"
    )
    incoming_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.target_account_id",
        back_populates="target_account"
    )


class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    amount = Column(Double, nullable=False)
    transaction_date = Column(DATETIME(fsp=6), nullable=True)
    transaction_type = Column(
        Enum(
            "CASH_CREDIT", "CASH_DEPOSIT", "CASH_TRANSFER", "CASH_WITHDRAWAL",
            name="transaction_type_enum"
        ),
        nullable=True
    )
    source_account_id = Column(BigInteger, ForeignKey("account.id"), nullable=True)
    target_account_id = Column(BigInteger, ForeignKey("account.id"), nullable=True)

    source_account = relationship(
        "Account",
        foreign_keys=[source_account_id],
        back_populates="outgoing_transactions"
    )
    target_account = relationship(
        "Account",
        foreign_keys=[target_account_id],
        back_populates="incoming_transactions"
    )


class Token(Base):
    __tablename__ = "token"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DATETIME(fsp=6), nullable=False)
    expiry_at = Column(DATETIME(fsp=6), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    account_id = Column(BigInteger, ForeignKey("account.id"), nullable=False)

    account = relationship("Account", back_populates="tokens")
