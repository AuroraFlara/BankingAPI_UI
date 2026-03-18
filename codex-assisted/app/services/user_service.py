import re
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_errors import ApiError
from app.core.security import create_access_token, hash_value, token_db_expiry, verify_value
from app.models.account import Account
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.users import LoginRequest, RegisterRequest


class UserService:
    def __init__(self) -> None:
        self.users = UserRepository()
        self.accounts = AccountRepository()
        self.tokens = TokenRepository()

    async def _generate_account_number(self, db: AsyncSession) -> str:
        while True:
            generated = str(uuid4()).replace("-", "")[:6].lower()
            existing = await self.accounts.get_by_account_number(db, generated)
            if not existing:
                return generated

    @staticmethod
    def _is_email_valid(email: str) -> bool:
        return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None

    @staticmethod
    def _is_phone_valid(phone_number: str, country_code: str) -> bool:
        digits = phone_number.replace(" ", "")
        if country_code.upper() == "SG":
            return digits.isdigit() and len(digits) == 8
        return digits.isdigit() and len(digits) >= 6

    def validate_register_payload(self, payload: dict) -> RegisterRequest:
        required_fields = ["name", "email", "password", "phoneNumber", "address", "countryCode"]
        allowed_fields = set(required_fields)

        for key in payload.keys():
            if key not in allowed_fields:
                raise ApiError(status_code=400, payload={"error": f"Extra field detected: {key}"})

        if payload == {}:
            raise ApiError(
                status_code=400,
                payload={
                    "errors": {
                        "name": "must not be empty",
                        "email": "must not be empty",
                        "password": "must not be empty",
                        "phoneNumber": "must not be empty",
                        "address": "must not be empty",
                        "countryCode": "must not be empty",
                    }
                },
            )

        errors: dict[str, str] = {}
        for field in required_fields:
            value = payload.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                if field == "email":
                    errors[field] = "must not be empty"
                else:
                    errors[field] = "must not be empty"

        email_value = payload.get("email")
        if email_value is not None and str(email_value).strip() != "" and not self._is_email_valid(str(email_value)):
            errors["email"] = "must be a well-formed email address"

        if errors:
            raise ApiError(status_code=400, payload={"errors": errors})

        password = str(payload["password"]).strip()
        if len(password) < 8:
            raise ApiError(status_code=400, payload={"error": "Password must be at least 8 characters long"})

        phone_number = str(payload["phoneNumber"]).strip()
        country_code = str(payload["countryCode"]).strip()
        if not self._is_phone_valid(phone_number, country_code):
            raise ApiError(
                status_code=400,
                payload={"error": f"Invalid phone number: {phone_number} for country code: {country_code}"},
            )

        return RegisterRequest.model_validate(
            {
                "name": str(payload["name"]).strip(),
                "email": str(payload["email"]).strip(),
                "password": password,
                "address": str(payload["address"]).strip(),
                "phoneNumber": phone_number,
                "countryCode": country_code,
            }
        )

    def validate_login_payload(self, payload: dict) -> LoginRequest:
        required_fields = ["identifier", "password"]
        allowed_fields = set(required_fields)

        for key in payload.keys():
            if key not in allowed_fields:
                raise ApiError(status_code=400, payload={"error": f"Extra field detected: {key}"})

        if payload == {}:
            raise ApiError(
                status_code=400,
                payload={
                    "errors": {
                        "identifier": "Identifier must not be empty",
                        "password": "Password must not be empty",
                    }
                },
            )

        errors: dict[str, str] = {}
        identifier = payload.get("identifier")
        password = payload.get("password")

        if identifier is None or (isinstance(identifier, str) and identifier.strip() == ""):
            errors["identifier"] = "Identifier must not be empty"
        if password is None or (isinstance(password, str) and password.strip() == ""):
            errors["password"] = "Password must not be empty"

        if errors:
            raise ApiError(status_code=400, payload={"errors": errors})

        return LoginRequest.model_validate(
            {
                "identifier": str(identifier).strip(),
                "password": str(password).strip(),
            }
        )

    async def register_user(self, db: AsyncSession, payload: RegisterRequest) -> dict:
        existing = await self.users.get_by_email(db, payload.email)
        if existing:
            raise ApiError(status_code=400, payload={"error": "Email already exists"})

        existing_phone = await self.users.get_by_phone_number(db, payload.phone_number)
        if existing_phone:
            raise ApiError(status_code=400, payload={"error": "Phone number already exists"})

        user = User(
            name=payload.name.strip(),
            email=payload.email,
            password=hash_value(payload.password),
            phone_number=payload.phone_number.strip(),
            address=payload.address.strip(),
            country_code=payload.country_code.strip(),
        )
        user = await self.users.create_user(db, user)

        account = Account(
            account_number=await self._generate_account_number(db),
            account_status=None,
            account_type="Savings",
            balance=0.0,
            branch="NIT",
            ifsc_code="NIT001",
            user_id=user.id,
        )
        account = await self.accounts.create_account(db, account)
        await db.commit()

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

    async def login_user(self, db: AsyncSession, payload: LoginRequest) -> dict:
        account = await self.accounts.get_by_account_number(db, payload.identifier)
        user = None
        if account:
            user = await self.users.get_by_id(db, account.user_id)
        else:
            user = await self.users.get_by_email(db, payload.identifier)
            if user:
                account = await self.accounts.get_by_user_id(db, user.id)

        if not user or not account:
            raise ApiError(
                status_code=400,
                payload={"error": f"User not found for the given identifier: {payload.identifier}"},
            )

        if not verify_value(payload.password, user.password):
            raise ApiError(status_code=401, payload={"error": "Invalid identifier or password"})

        token = create_access_token(account.account_number)
        existing_token = await self.tokens.get_by_token(db, token)
        if not existing_token:
            await self.tokens.create_token(db, account_id=account.id, token=token, expiry_at=token_db_expiry())
        await db.commit()

        return {"token": token}

    async def dashboard_user(self, db: AsyncSession, account_number: str) -> dict:
        account = await self.accounts.get_by_account_number(db, account_number)
        if not account:
            raise ApiError(status_code=404, payload={"error": "Account not found"})

        user = await self.users.get_by_id(db, account.user_id)
        if not user:
            raise ApiError(status_code=404, payload={"error": "User not found"})

        return {
            "user": {
                "name": user.name,
                "email": user.email,
                "countryCode": user.country_code,
                "phoneNumber": user.phone_number,
                "address": user.address,
                "accountNumber": account.account_number,
                "ifscCode": account.ifsc_code,
                "branch": account.branch,
                "accountType": account.account_type,
            },
            "msg": "User details retrieved successfully",
        }
