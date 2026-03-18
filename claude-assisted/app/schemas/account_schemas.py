from __future__ import annotations

from typing import Optional

from pydantic import model_validator

from app.schemas.base import CamelModel


# ---------------------------------------------------------------------------
# Inbound request schemas
# ---------------------------------------------------------------------------

class CreatePINRequest(CamelModel):
    """
    POST /api/account/pin/create
    Ground truth: { "pin": "1234", "password": "Password123!" }
    Auth is password-verified (not account_number match).
    Empty checks use singular 'error' key except empty-JSON which uses 'errors'.
    """
    pin: Optional[str] = None
    password: Optional[str] = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def check_not_empty(self) -> "CreatePINRequest":
        errors: dict[str, str] = {}
        if self.pin is None or not str(self.pin).strip():
            errors["pin"] = "PIN cannot be empty"
        if self.password is None or not str(self.password).strip():
            errors["password"] = "Password cannot be empty"
        if errors:
            raise ValueError({"__type": "field_errors", "errors": errors})
        return self


class UpdatePINRequest(CamelModel):
    """
    POST /api/account/pin/update
    Ground truth: { "oldPin": "1234", "newPin": "4321", "password": "Password123!" }
    - Verifies both oldPin (BCrypt) and password before allowing change.
    - newPin must be exactly 4 digits.
    """
    oldPin: Optional[str] = None
    newPin: Optional[str] = None
    password: Optional[str] = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_fields(self) -> "UpdatePINRequest":
        import re
        errors: dict[str, str] = {}
        if self.oldPin is None or not str(self.oldPin).strip():
            errors["oldPin"] = "Old PIN cannot be empty"
        if self.newPin is None or not str(self.newPin).strip():
            errors["newPin"] = "New PIN cannot be empty"
        if self.password is None or not str(self.password).strip():
            errors["password"] = "Password cannot be empty"
        if errors:
            raise ValueError({"__type": "field_errors", "errors": errors})
        # 4-digit format validation (only reached when all fields are present)
        if not re.match(r'^\d{4}$', str(self.newPin)):
            raise ValueError({"__type": "field_errors", "errors": {"newPin": "PIN must be exactly 4 digits"}})
        return self


class DepositRequest(CamelModel):
    """
    POST /api/account/deposit
    amount accepts both string ("200") and numeric (200) — Pydantic v2 coerces str→float.
    Account identified via JWT Bearer token; no account_number in request.
    Business validations (> 0, multiples of 100) applied in service layer.
    """
    amount: Optional[float] = None
    pin: Optional[str] = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def check_not_empty(self) -> "DepositRequest":
        errors: dict[str, str] = {}
        if self.amount is None:
            errors["amount"] = "Amount cannot be empty"
        if self.pin is None or not str(self.pin).strip():
            errors["pin"] = "PIN cannot be empty"
        if errors:
            raise ValueError({"__type": "field_errors", "errors": errors})
        return self


class WithdrawRequest(CamelModel):
    """POST /api/account/withdraw — same shape as DepositRequest."""
    amount: Optional[float] = None
    pin: Optional[str] = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def check_not_empty(self) -> "WithdrawRequest":
        errors: dict[str, str] = {}
        if self.amount is None:
            errors["amount"] = "Amount cannot be empty"
        if self.pin is None or not str(self.pin).strip():
            errors["pin"] = "PIN cannot be empty"
        if errors:
            raise ValueError({"__type": "field_errors", "errors": errors})
        return self


class FundTransferRequest(CamelModel):
    """
    POST /api/account/fund-transfer
    Source account is identified via JWT Bearer token — not in the request body.
    Ground truth:
      - Missing/empty fields      → {"errors": {...}}  (field_errors)
      - Negative amount           → {"errors": {"amount": "Amount must be greater than 0"}}
      - Non-multiple-of-100       → {"error": "..."}   (service-level)
    """
    target_account_number: Optional[str] = None   # alias: targetAccountNumber
    amount: Optional[float] = None
    pin: Optional[str] = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_fields(self) -> "FundTransferRequest":
        errors: dict[str, str] = {}
        if self.target_account_number is None or not str(self.target_account_number).strip():
            errors["targetAccountNumber"] = "Target account number cannot be empty"
        if self.amount is None:
            errors["amount"] = "Amount cannot be empty"
        elif self.amount <= 0:
            errors["amount"] = "Amount must be greater than 0"
        if self.pin is None or not str(self.pin).strip():
            errors["pin"] = "PIN cannot be empty"
        if errors:
            raise ValueError({"__type": "field_errors", "errors": errors})
        return self


# ---------------------------------------------------------------------------
# Outbound response schemas
# ---------------------------------------------------------------------------

class AccountOutCamel(CamelModel):
    """camelCase account object for JSON responses."""

    id: int
    accountNumber: str
    accountType: str
    accountStatus: Optional[str]
    balance: float
    branch: Optional[str]
    ifscCode: Optional[str]

    model_config = {"from_attributes": False}


class PINCheckResponse(CamelModel):
    isPinCreated: bool
    msg: str


class PINCreateUpdateResponse(CamelModel):
    hasPIN: bool
    msg: str


class BalanceResponse(CamelModel):
    hasPIN: bool
    currentBalance: float
    msg: str


class FundTransferResponse(CamelModel):
    msg: str


class DashboardAccountResponse(CamelModel):
    account: AccountOutCamel
    msg: str


class DashboardUserResponse(CamelModel):
    user: UserOutCamel
    msg: str


# ---------------------------------------------------------------------------
# Forward reference resolution
# ---------------------------------------------------------------------------
from app.schemas.user_schemas import UserOutCamel  # noqa: E402

DashboardUserResponse.model_rebuild()
