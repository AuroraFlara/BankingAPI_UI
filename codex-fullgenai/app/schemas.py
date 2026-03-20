from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _reject_extra_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        field_names = set(cls.model_fields.keys())
        alias_names = {
            field.alias
            for field in cls.model_fields.values()
            if isinstance(field.alias, str) and field.alias
        }
        accepted_names = field_names | alias_names
        for key in data.keys():
            if key not in accepted_names:
                raise ValueError(f"Extra field detected: {key}")
        return data


class RegisterRequest(StrictSchema):
    name: str = Field(min_length=1)
    email: EmailStr
    phone_number: str = Field(min_length=1, alias="phoneNumber")
    address: str = Field(min_length=1)
    country_code: str = Field(min_length=1, alias="countryCode")
    password: str = Field(min_length=1)


class LoginRequest(StrictSchema):
    identifier: str = Field(min_length=1)
    password: str = Field(min_length=1)


class PinCreateRequest(StrictSchema):
    pin: str = Field(min_length=1)
    password: str = Field(min_length=1)


class PinUpdateRequest(StrictSchema):
    old_pin: str = Field(min_length=1, alias="oldPin")
    new_pin: str = Field(min_length=1, alias="newPin")
    password: str = Field(min_length=1)


class AmountPinRequest(StrictSchema):
    amount: float
    pin: str = Field(min_length=1)


class TransferRequest(StrictSchema):
    amount: float
    pin: str = Field(min_length=1)
    target_account_number: str = Field(min_length=1, alias="targetAccountNumber")


class MessageResponse(BaseModel):
    msg: str


class TokenResponse(BaseModel):
    token: str
    msg: str


class UserDashboardResponse(BaseModel):
    user: dict


class AccountDashboardResponse(BaseModel):
    account: dict


class PinCheckResponse(BaseModel):
    is_pin_created: bool = Field(alias="isPinCreated")


class TransactionItem(BaseModel):
    id: int
    amount: float
    transaction_type: str = Field(alias="transactionType")
    transaction_date: str = Field(alias="transactionDate")
    source_account_number: str | None = Field(default=None, alias="sourceAccountNumber")
    target_account_number: str | None = Field(default=None, alias="targetAccountNumber")


class TransactionHistoryResponse(BaseModel):
    transactions: list[TransactionItem]


def format_dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")
