from pydantic import BaseModel, EmailStr, validator, root_validator
from typing import Optional, List
from datetime import datetime


def to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class CamelModel(BaseModel):
    """Base model that converts snake_case fields to camelCase for output.

    Also forbids extra fields to keep payloads strict and predictable.
    """

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        orm_mode = True
        extra = "forbid"
        json_encoders = {datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")}


class UserRegister(CamelModel):
    name: str
    email: EmailStr
    password: str
    phone_number: str
    address: str
    country_code: str


    @validator("password")
    def password_len(cls, v):
        if not v or len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class LoginRequest(CamelModel):
    identifier: str
    password: str


class TokenResponse(CamelModel):
    token: str
    msg: Optional[str]


class GenericMsg(CamelModel):
    msg: str


class PinRequest(CamelModel):
    password: str
    pin: str

    @validator("pin")
    def pin_digits(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError("PIN must be exactly 4 digits")
        return v


class PinUpdateRequest(CamelModel):
    password: str
    old_pin: str
    new_pin: str

    @validator("old_pin", "new_pin")
    def pins_digits(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError("PIN must be exactly 4 digits")
        return v


class AmountRequest(CamelModel):
    pin: str
    amount: float

    @validator("pin")
    def pin_digits_amount(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError("PIN must be exactly 4 digits")
        return v

    @validator("amount")
    def amount_valid(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if int(v) % 100 != 0:
            raise ValueError("Amount must be in multiples of 100")
        return v


class FundTransferRequest(CamelModel):
    pin: str
    amount: float
    target_account_number: str

    @validator("pin")
    def pin_digits_transfer(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError("PIN must be exactly 4 digits")
        return v


class TransactionDTO(CamelModel):
    id: int
    amount: float
    transaction_date: datetime
    transaction_type: str
    source_account_number: Optional[str]
    target_account_number: Optional[str]


class TransactionsResponse(CamelModel):
    transactions: List[TransactionDTO]
    msg: str


class UserResponse(CamelModel):
    id: int
    name: str
    email: str
    phone_number: str
    address: str
    country_code: str
    account_number: Optional[str]


class AccountResponse(CamelModel):
    id: int
    account_number: str
    account_type: str
    account_status: Optional[str]
    balance: float
    branch: Optional[str]
    ifsc_code: Optional[str]
    user_id: int
