"""
AuthService: handles user registration and login.

Parity targets:
  UserServiceImpl.registerUser()  -> register_user()
  UserServiceImpl.loginUser()     -> login_user()
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Account, Token, User
from app.repositories.account_repository import AccountRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_schemas import LoginResponse, RegisterResponse
from app.security import create_token, hash_password, verify_password

# Java defaults applied at account creation
_DEFAULT_ACCOUNT_TYPE = "Savings"
_DEFAULT_IFSC_CODE = "NIT001"
_DEFAULT_BRANCH = "NIT"


async def _generate_unique_account_number(account_repo: AccountRepository) -> str:
    """
    Replicates Java generateUniqueAccountNumber:
      uuid4 -> remove hyphens -> take first 6 lowercase chars.
    Loops until the generated number is not already in the DB.
    """
    while True:
        candidate = uuid.uuid4().hex[:6]  # uuid4().hex is already lowercase, no hyphens
        existing = await account_repo.find_by_account_number(candidate)
        if existing is None:
            return candidate


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._user_repo = UserRepository(db)
        self._account_repo = AccountRepository(db)
        self._token_repo = TokenRepository(db)

    async def register_user(self, payload: dict) -> RegisterResponse:
        # Duplicate-email guard  -> {"error": "Email already exists"}
        if await self._user_repo.find_by_email(payload["email"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

        # Duplicate-phone guard  -> {"error": "Phone number already exists"}
        if await self._user_repo.find_by_phone_number(payload["phoneNumber"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists",
            )

        user = User(
            name=payload["name"],
            email=payload["email"],
            password=hash_password(payload["password"]),
            address=payload["address"],
            phone_number=payload["phoneNumber"],
            country_code=payload["countryCode"],
        )
        user = await self._user_repo.save(user)

        account_number = await _generate_unique_account_number(self._account_repo)
        account = Account(
            account_number=account_number,
            account_type=_DEFAULT_ACCOUNT_TYPE,
            account_status=None,  # Legacy: NULL at creation
            balance=0.0,
            ifsc_code=_DEFAULT_IFSC_CODE,
            branch=_DEFAULT_BRANCH,
            user_id=user.id,
        )
        account = await self._account_repo.save(account)

        return RegisterResponse(
            name=user.name,
            email=user.email,
            countryCode=user.country_code,
            phoneNumber=user.phone_number,
            address=user.address,
            accountNumber=account.account_number,
            ifscCode=account.ifsc_code,
            branch=account.branch,
            accountType=account.account_type,
            msg="User registered successfully",
        )

    async def login_user(self, identifier: str, password: str) -> LoginResponse:
        # Identifier = account_number; look up account first, then verify password
        account = await self._account_repo.find_by_account_number(identifier)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User not found for the given identifier: {identifier}",
            )

        # Load the linked user to verify password
        from sqlalchemy import select
        from app.models.models import User as UserModel
        result = await self._db.execute(
            select(UserModel).where(UserModel.id == account.user_id)
        )
        user = result.scalars().first()
        if user is None or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid identifier or password",
            )

        jwt_token = create_token(account.account_number)

        # Delete any existing token for this account before inserting the new one.
        # Without this, a second login produces the identical JWT (no iat/jti claims)
        # and the UNIQUE constraint on token.token causes an IntegrityError.
        await self._token_repo.delete_by_account_id(account.id)

        now = datetime.now(tz=timezone.utc)
        token_row = Token(
            token=jwt_token,
            account_id=account.id,
            created_at=now,
            expiry_at=now + timedelta(days=36500),
        )
        await self._token_repo.save(token_row)

        # Ground truth: login response is {"token": "..."} — no msg field
        return LoginResponse(token=jwt_token)

