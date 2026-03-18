from __future__ import annotations

import re
from typing import Optional

from pydantic import model_validator

from app.schemas.base import CamelModel


# ---------------------------------------------------------------------------
# Inbound request schemas
# ---------------------------------------------------------------------------

class RegisterRequest(CamelModel):
    """
    POST /api/users/register — camelCase input fields (Java parity).
    accountType is NOT in the request; Java defaults it to "Savings".
    """

    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    address: Optional[str] = None
    phoneNumber: Optional[str] = None
    countryCode: Optional[str] = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_all(self) -> RegisterRequest:
        # ---- 1. Collect empty-field errors ("errors" object shape) -----
        empty_errors: dict[str, str] = {}
        for field in ("name", "email", "password", "phoneNumber", "address", "countryCode"):
            v = getattr(self, field)
            if v is None or not str(v).strip():
                empty_errors[field] = "must not be empty"
        if empty_errors:
            raise ValueError({"__type": "field_errors", "errors": empty_errors})

        # ---- 2. Password minimum length ("error" singular shape) -------
        if len(self.password) < 8:
            raise ValueError({"__type": "single_error", "error": "Password must be at least 8 characters long"})

        # ---- 3. Basic email format check --------------------------------
        email_re = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
        if not email_re.match(self.email):
            raise ValueError({"__type": "field_errors", "errors": {"email": "must be a well-formed email address"}})

        return self


class LoginRequest(CamelModel):
    """
    POST /api/users/login — accepts 'identifier' (account_number).
    Empty-field messages are capitalised per ground truth.
    """

    identifier: Optional[str] = None
    password: Optional[str] = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def check_not_empty(self) -> LoginRequest:
        errors: dict[str, str] = {}
        if self.identifier is None or not str(self.identifier).strip():
            errors["identifier"] = "Identifier must not be empty"
        if self.password is None or not str(self.password).strip():
            errors["password"] = "Password must not be empty"
        if errors:
            raise ValueError({"__type": "field_errors", "errors": errors})
        return self


# ---------------------------------------------------------------------------
# Outbound response schemas
# ---------------------------------------------------------------------------

class RegisterResponse(CamelModel):
    """
    Flat response — all user + account fields at the top level.
    Java ground truth: { name, email, countryCode, phoneNumber, address,
                         accountNumber, ifscCode, branch, accountType, msg }
    """
    name: str
    email: str
    countryCode: str
    phoneNumber: str
    address: str
    accountNumber: str
    ifscCode: Optional[str]
    branch: Optional[str]
    accountType: str
    msg: str


class LoginResponse(CamelModel):
    """Login response: token only — no msg field per ground truth."""
    token: str


# UserOutCamel is used by dashboard_service — kept here for import compatibility.
class UserOutCamel(CamelModel):
    """Extended user object used by GET /api/dashboard/user (includes account fields)."""
    name: str
    email: str
    countryCode: str
    phoneNumber: str
    address: str
    accountNumber: str
    ifscCode: Optional[str]
    branch: Optional[str]
    accountType: str

    model_config = {"from_attributes": False}
