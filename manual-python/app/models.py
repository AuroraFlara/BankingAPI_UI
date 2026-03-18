"""SQLAlchemy models for users, accounts, transactions and tokens.

Keep models simple and closely aligned to the original Java schema.
Field names use snake_case internally; responses are converted to
camelCase in the Pydantic layer.
"""

from sqlalchemy import Column, BigInteger, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
import enum
from datetime import datetime

Base = declarative_base()


class TransactionType(enum.Enum):
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
    account = relationship("Account", uselist=False, back_populates="user")


class Account(Base):
    __tablename__ = "account"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pin = Column(String(255), nullable=True)
    account_number = Column(String(255), nullable=False, unique=True)
    account_status = Column(String(255), nullable=True)
    account_type = Column(String(255), nullable=False)
    balance = Column(Float, nullable=False, default=0.0)
    branch = Column(String(255), nullable=True)
    ifsc_code = Column(String(255), nullable=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True)
    user = relationship("User", back_populates="account")
    source_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.source_account_id",
        back_populates="source_account",
    )
    target_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.target_account_id",
        back_populates="target_account",
    )


class Transaction(Base):
    __tablename__ = "transaction"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    transaction_date = Column(DateTime, default=datetime.utcnow)
    transaction_type = Column(Enum(TransactionType), nullable=True)
    source_account_id = Column(BigInteger, ForeignKey("account.id"), nullable=True)
    target_account_id = Column(BigInteger, ForeignKey("account.id"), nullable=True)
    source_account = relationship(
        "Account",
        foreign_keys=[source_account_id],
        back_populates="source_transactions",
    )
    target_account = relationship(
        "Account",
        foreign_keys=[target_account_id],
        back_populates="target_transactions",
    )


class Token(Base):
    __tablename__ = "token"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expiry_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    token = Column(String(255), nullable=False, unique=True)
    account_id = Column(BigInteger, ForeignKey("account.id"), nullable=False)
