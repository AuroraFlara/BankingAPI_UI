from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Optional, List, Union
import re


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    email: str
    password: str
    phoneNumber: str
    address: str
    countryCode: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty")
        # Basic RFC-like email check matching Java's @Email constraint
        pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
        if not re.match(pattern, v.strip()):
            raise ValueError("must be a well-formed email address")
        return v

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("phoneNumber")
    @classmethod
    def phone_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("address")
    @classmethod
    def address_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("countryCode")
    @classmethod
    def country_code_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    model_config = {"extra": "forbid"}

    identifier: str
    password: str

    @field_validator("identifier")
    @classmethod
    def identifier_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Identifier must not be empty")
        return v

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password must not be empty")
        return v


# ---------------------------------------------------------------------------
# PIN – Create
# ---------------------------------------------------------------------------
class PinCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    # Optional so that missing-field behavior can be controlled in service
    pin: Optional[str] = None
    password: Optional[str] = None


# ---------------------------------------------------------------------------
# PIN – Update
# ---------------------------------------------------------------------------
class PinUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    oldPin: str
    newPin: str
    password: str

    @field_validator("oldPin")
    @classmethod
    def old_pin_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Old PIN cannot be empty")
        return v

    @field_validator("newPin")
    @classmethod
    def new_pin_valid(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("New PIN cannot be empty")
        if not re.fullmatch(r'\d{4}', v.strip()):
            raise ValueError("PIN must be exactly 4 digits")
        return v

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password cannot be empty")
        return v


# ---------------------------------------------------------------------------
# Banking – Deposit
# ---------------------------------------------------------------------------
class DepositRequest(BaseModel):
    """
    amount accepts string ("200") or numeric (100) — Java accepts both.
    We coerce to str for uniform downstream parsing.
    """
    model_config = {"extra": "forbid"}

    amount: Union[str, int, float]
    pin: str

    @field_validator("amount", mode="before")
    @classmethod
    def amount_not_empty(cls, v) -> str:
        if v is None or str(v).strip() == "":
            raise ValueError("Amount cannot be empty")
        return str(v)

    @field_validator("pin")
    @classmethod
    def pin_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("PIN cannot be empty")
        return v


# ---------------------------------------------------------------------------
# Banking – Withdraw
# ---------------------------------------------------------------------------
class WithdrawRequest(BaseModel):
    model_config = {"extra": "forbid"}

    amount: Union[str, int, float]
    pin: str

    @field_validator("amount", mode="before")
    @classmethod
    def amount_not_empty(cls, v) -> str:
        if v is None or str(v).strip() == "":
            raise ValueError("Amount cannot be empty")
        return str(v)

    @field_validator("pin")
    @classmethod
    def pin_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("PIN cannot be empty")
        return v


# ---------------------------------------------------------------------------
# Banking – Transfer
# ---------------------------------------------------------------------------
class TransferRequest(BaseModel):
    model_config = {"extra": "forbid"}

    amount: Union[str, int, float]
    pin: str
    targetAccountNumber: str

    @field_validator("amount", mode="before")
    @classmethod
    def amount_not_empty(cls, v) -> str:
        if v is None or str(v).strip() == "":
            raise ValueError("Amount cannot be empty")
        # Negative amount validation at schema level for transfer → returns {"errors": {"amount": ...}}
        try:
            num = float(str(v))
            if num <= 0:
                raise ValueError("Amount must be greater than 0")
        except (ValueError, TypeError) as e:
            if "Amount must be greater than 0" in str(e):
                raise
        return str(v)

    @field_validator("pin")
    @classmethod
    def pin_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("PIN cannot be empty")
        return v

    @field_validator("targetAccountNumber")
    @classmethod
    def target_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Target account number cannot be empty")
        return v


# ---------------------------------------------------------------------------
# Transaction History
# ---------------------------------------------------------------------------
class TransactionItem(BaseModel):
    model_config = {"extra": "ignore"}

    id: int
    amount: float
    transactionDate: Optional[str]
    transactionType: Optional[str]
    sourceAccountNumber: Optional[str]
    targetAccountNumber: Optional[str]
