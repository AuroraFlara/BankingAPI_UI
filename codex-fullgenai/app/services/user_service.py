import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import APIError
from app.core.security import create_access_token, hash_value, verify_hash
from app.models import Account, Token, User
from app.repositories import AccountRepository, TokenRepository, UserRepository
from app.schemas import LoginRequest, RegisterRequest


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.account_repo = AccountRepository(db)
        self.token_repo = TokenRepository(db)

    async def register(self, payload: RegisterRequest) -> dict:
        if len(payload.password) < 8:
            raise APIError(status_code=400, message="Password must be at least 8 characters long")

        phone_normalized = payload.phone_number.replace(" ", "")
        if not phone_normalized.isdigit() or any(ch not in "0123456789 " for ch in payload.phone_number):
            raise APIError(
                status_code=400,
                message=f"Invalid phone number: {payload.phone_number} for country code: {payload.country_code}",
            )

        if payload.country_code.upper() == "SG" and len(phone_normalized) != 8:
            raise APIError(
                status_code=400,
                message=f"Invalid phone number: {payload.phone_number} for country code: {payload.country_code}",
            )

        if await self.user_repo.get_by_email(payload.email):
            raise APIError(status_code=400, message="Email already exists")

        if await self.user_repo.get_by_phone_normalized(payload.phone_number):
            raise APIError(status_code=400, message="Phone number already exists")

        user = User(
            name=payload.name,
            email=payload.email,
            phone_number=payload.phone_number,
            address=payload.address,
            country_code=payload.country_code,
            password=hash_value(payload.password),
        )

        user = await self.user_repo.create(user)
        account = Account(
            user_id=user.id,
            account_number=await self._generate_account_number(),
            account_status=None,
            account_type="Savings",
            balance=0.0,
            branch="NIT",
            ifsc_code="NIT001",
        )
        await self.account_repo.create(account)
        await self._commit_or_rollback()

        return {
            "name": user.name,
            "email": user.email,
            "countryCode": user.country_code,
            "phoneNumber": user.phone_number,
            "address": user.address,
            "accountNumber": account.account_number,
            "ifscCode": account.ifsc_code,
            "branch": account.branch,
            "accountType": account.account_type,
            "msg": "User registered successfully",
        }

    async def login(self, payload: LoginRequest) -> dict:
        account = await self.account_repo.get_by_account_number(payload.identifier)
        if not account or not account.user:
            raise APIError(status_code=400, message=f"User not found for the given identifier: {payload.identifier}")

        if not verify_hash(payload.password, account.user.password):
            raise APIError(status_code=401, message="Invalid identifier or password")

        token_value = create_access_token(account.account_number)
        token_row = Token(
            token=token_value,
            account_id=account.id,
            created_at=datetime.utcnow(),
            expiry_at=datetime.utcnow() + timedelta(days=1),
        )

        await self.token_repo.create(token_row)
        await self._commit_or_rollback()

        return {"token": token_value}

    async def _generate_account_number(self) -> str:
        # Java data shows 6-char lowercase hex account numbers (0-9, a-f).
        alphabet = "0123456789abcdef"
        while True:
            generated = "".join(random.choice(alphabet) for _ in range(6))
            if not await self.account_repo.account_number_exists(generated):
                return generated

    async def _commit_or_rollback(self) -> None:
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
