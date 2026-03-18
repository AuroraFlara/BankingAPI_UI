"""
User service: Registration and Login.
"""
from __future__ import annotations
import random
import string
import re
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models import User, Account, Token
from app.repositories import UserRepository, AccountRepository, TokenRepository
from app.security import hash_password, verify_password, create_access_token
from app.schemas import RegisterRequest, LoginRequest
from datetime import datetime, timedelta

# Fixed account defaults matching Java
IFSC_CODE = "NIT001"
BRANCH = "NIT"
ACCOUNT_TYPE = "Savings"


def _generate_account_number(length: int = 6) -> str:
    """Generate a random hex account number of given length, matching Java's UUID-based generation."""
    return secrets.token_hex(length // 2)[:length]


def _is_valid_phone(phone: str, country_code: str) -> bool:
    """Basic phone number validation. Returns False for clearly non-numeric values."""
    # Strip common separators
    cleaned = re.sub(r'[\s\-\+\(\)]', '', phone)
    return cleaned.isdigit()


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.account_repo = AccountRepository(db)
        self.token_repo = TokenRepository(db)

    async def register(self, req: RegisterRequest) -> dict:
        # Password length check (returns as {"error": ...} not {"errors": ...})
        if len(req.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Password must be at least 8 characters long"},
            )

        # Phone number format validation
        if not _is_valid_phone(req.phoneNumber, req.countryCode):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": f"Invalid phone number: {req.phoneNumber} for country code: {req.countryCode}"},
            )

        # Duplicate checks – Java returns 400 (not 409)
        if await self.user_repo.find_by_email(req.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Email already exists"},
            )
        if await self.user_repo.find_by_phone(req.phoneNumber):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Phone number already exists"},
            )

        # Create user
        user = User(
            name=req.name,
            email=req.email,
            password=hash_password(req.password),
            phone_number=req.phoneNumber,
            address=req.address,
            country_code=req.countryCode,
        )
        user = await self.user_repo.save(user)

        # Generate unique account number
        account_number = _generate_account_number()
        while await self.account_repo.exists_by_account_number(account_number):
            account_number = _generate_account_number()

        # Create account with fixed branch/ifsc
        account = Account(
            account_number=account_number,
            account_type=ACCOUNT_TYPE,
            balance=0.0,
            ifsc_code=IFSC_CODE,
            branch=BRANCH,
            user_id=user.id,
        )
        await self.account_repo.save(account)
        await self.db.commit()

        return {
            "name": req.name,
            "email": req.email,
            "countryCode": req.countryCode,
            "phoneNumber": req.phoneNumber,
            "address": req.address,
            "accountNumber": account_number,
            "ifscCode": IFSC_CODE,
            "branch": BRANCH,
            "accountType": ACCOUNT_TYPE,
            "msg": "User registered successfully",
        }

    async def login(self, req: LoginRequest) -> dict:
        # identifier = accountNumber in Java
        account = await self.account_repo.find_by_account_number(req.identifier)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": f"User not found for the given identifier: {req.identifier}"},
            )

        user = await self._load_user_for_account(account)

        if not verify_password(req.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid identifier or password"},
            )

        jwt_token = create_access_token(account.account_number)

        # Persist token record
        now = datetime.utcnow()
        token_record = Token(
            token=jwt_token,
            account_id=account.id,
            created_at=now,
            expiry_at=now + timedelta(days=1),
        )
        await self.token_repo.save(token_record)
        await self.db.commit()

        # Java login returns only {"token": "..."} – no msg field
        return {"token": jwt_token}

    async def _load_user_for_account(self, account: Account) -> User:
        from sqlalchemy import select
        result = await self.db.execute(
            select(User).where(User.id == account.user_id)
        )
        return result.scalar_one()

