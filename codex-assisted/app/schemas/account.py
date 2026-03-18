from datetime import datetime

from pydantic import field_serializer, field_validator

from app.schemas.common import StrictCamelModel


class PinCreateRequest(StrictCamelModel):
    pin: str
    password: str


class PinUpdateRequest(StrictCamelModel):
    old_pin: str
    new_pin: str

    @field_validator("old_pin", "new_pin")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("cannot be empty")
        return value


class AmountRequest(StrictCamelModel):
    amount: float

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Amount must be greater than zero")
        return value


class FundTransferRequest(StrictCamelModel):
    target_account_number: str
    amount: float

    @field_validator("target_account_number")
    @classmethod
    def validate_target(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("cannot be empty")
        return value


class TransactionOut(StrictCamelModel):
    id: int
    amount: float
    transaction_date: datetime | None
    transaction_type: str | None
    source_account_number: str | None
    target_account_number: str | None

    @field_serializer("transaction_date")
    def serialize_date(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.strftime("%Y-%m-%d %H:%M:%S")
