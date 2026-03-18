from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_errors import ApiError
from app.core.security import hash_value, verify_value
from app.models.enums import TransactionType
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.account import TransactionOut


class AccountService:
    def __init__(self) -> None:
        self.accounts = AccountRepository()
        self.transactions = TransactionRepository()
        self.users = UserRepository()

    async def _get_user_and_account(self, db: AsyncSession, account_number: str):
        user = await self.users.get_with_account_by_account_number(db, account_number)
        if not user or not user.account:
            raise ApiError(status_code=404, payload={"error": "Account not found"})
        return user, user.account

    async def dashboard_account(self, db: AsyncSession, account_number: str) -> dict:
        account = await self.accounts.get_by_account_number(db, account_number)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        return {
            "account": {
                "id": account.id,
                "accountNumber": account.account_number,
                "accountStatus": account.account_status,
                "accountType": account.account_type,
                "balance": float(account.balance),
                "branch": account.branch,
                "ifscCode": account.ifsc_code,
            },
            "msg": "Account details retrieved successfully",
        }

    async def validate_create_pin_payload(self, payload: dict) -> tuple[str, str]:
        required_fields = ["pin", "password"]
        allowed_fields = set(required_fields)

        for key in payload.keys():
            if key not in allowed_fields:
                raise ApiError(status_code=400, payload={"error": f"Extra field detected: {key}"})

        if payload == {}:
            raise ApiError(
                status_code=400,
                payload={
                    "errors": {
                        "pin": "PIN cannot be empty",
                        "password": "Password cannot be empty",
                    }
                },
            )

        pin = payload.get("pin")
        password = payload.get("password")

        if pin is None or str(pin).strip() == "":
            raise ApiError(status_code=400, payload={"error": "PIN cannot be empty"})
        if password is None or str(password).strip() == "":
            raise ApiError(status_code=401, payload={"error": "Password cannot be empty"})

        return str(pin).strip(), str(password).strip()

    async def create_pin(self, db: AsyncSession, account_number: str, pin: str, password: str) -> dict:
        account = await self.accounts.get_by_account_number(db, account_number)
        if not account:
            raise ApiError(status_code=404, payload={"error": "Account not found"})

        user = await self.users.get_by_id(db, account.user_id)
        if not user:
            raise ApiError(status_code=404, payload={"error": "User not found"})
        if not verify_value(password, user.password):
            raise ApiError(status_code=401, payload={"error": "Invalid password"})

        if account.pin:
            raise ApiError(status_code=409, payload={"error": "PIN already created"})

        account.pin = hash_value(pin)
        await db.commit()
        return {"hasPIN": True, "msg": "PIN created successfully"}

    async def validate_update_pin_payload(self, payload: dict) -> tuple[str, str, str]:
        required_fields = ["oldPin", "newPin", "password"]
        allowed_fields = set(required_fields)

        for key in payload.keys():
            if key not in allowed_fields:
                raise ApiError(status_code=400, payload={"error": f"Extra field detected: {key}"})

        if payload == {}:
            raise ApiError(
                status_code=400,
                payload={
                    "errors": {
                        "oldPin": "Old PIN cannot be empty",
                        "password": "Password cannot be empty",
                        "newPin": "New PIN cannot be empty",
                    }
                },
            )

        errors: dict[str, str] = {}
        old_pin = payload.get("oldPin")
        new_pin = payload.get("newPin")
        password = payload.get("password")

        if old_pin is None or str(old_pin).strip() == "":
            errors["oldPin"] = "Old PIN cannot be empty"
        if new_pin is None or str(new_pin).strip() == "":
            errors["newPin"] = "New PIN cannot be empty"
        if password is None or str(password).strip() == "":
            errors["password"] = "Password cannot be empty"

        if errors:
            raise ApiError(status_code=400, payload={"errors": errors})

        old_pin_clean = str(old_pin).strip()
        new_pin_clean = str(new_pin).strip()
        password_clean = str(password).strip()

        if not new_pin_clean.isdigit() or len(new_pin_clean) != 4:
            raise ApiError(status_code=400, payload={"errors": {"newPin": "PIN must be exactly 4 digits"}})

        return old_pin_clean, new_pin_clean, password_clean

    async def update_pin(
        self,
        db: AsyncSession,
        account_number: str,
        old_pin: str,
        new_pin: str,
        password: str,
    ) -> dict:
        user, account = await self._get_user_and_account(db, account_number)

        if not verify_value(password, user.password):
            raise ApiError(status_code=401, payload={"error": "Invalid password"})
        if not account.pin or not verify_value(old_pin, account.pin):
            raise ApiError(status_code=401, payload={"error": "Invalid PIN"})

        account.pin = hash_value(new_pin)
        await db.commit()
        return {"hasPIN": True, "msg": "PIN updated successfully"}

    async def check_pin(self, db: AsyncSession, account_number: str) -> dict:
        _, account = await self._get_user_and_account(db, account_number)
        has_pin = bool(account.pin)
        if has_pin:
            return {"isPinCreated": True, "msg": "PIN has been created for this account"}
        return {"isPinCreated": False, "msg": "PIN has not been created for this account"}

    async def validate_cash_payload(self, payload: dict) -> tuple[float, str]:
        required_fields = ["amount", "pin"]
        allowed_fields = set(required_fields)

        for key in payload.keys():
            if key not in allowed_fields:
                raise ApiError(status_code=400, payload={"error": f"Extra field detected: {key}"})

        if payload == {}:
            raise ApiError(
                status_code=400,
                payload={
                    "errors": {
                        "pin": "PIN cannot be empty",
                        "amount": "Amount cannot be empty",
                    }
                },
            )

        errors: dict[str, str] = {}
        amount_raw = payload.get("amount")
        pin_raw = payload.get("pin")

        if pin_raw is None or str(pin_raw).strip() == "":
            errors["pin"] = "PIN cannot be empty"
        if amount_raw is None or (isinstance(amount_raw, str) and amount_raw.strip() == ""):
            errors["amount"] = "Amount cannot be empty"

        if errors:
            raise ApiError(status_code=400, payload={"errors": errors})

        pin = str(pin_raw).strip()
        amount_input = amount_raw
        if isinstance(amount_raw, str):
            amount_input = amount_raw.strip()
        try:
            amount = float(str(amount_input))
        except (TypeError, ValueError) as exc:
            raise ApiError(status_code=400, payload={"error": "Amount cannot be empty"}) from exc

        if amount <= 0:
            raise ApiError(status_code=400, payload={"error": "Amount must be greater than 0"})

        # Enforce Java parity rule for ATM denominations.
        if amount % 100 != 0:
            raise ApiError(status_code=400, payload={"error": "Amount must be in multiples of 100"})

        return amount, pin

    async def deposit(self, db: AsyncSession, account_number: str, amount: float, pin: str) -> dict:
        _, account = await self._get_user_and_account(db, account_number)
        if not account.pin or not verify_value(pin, account.pin):
            raise ApiError(status_code=401, payload={"error": "Invalid PIN"})

        account.balance = float(account.balance) + float(amount)
        await self.transactions.create(
            db,
            amount=float(amount),
            tx_type=TransactionType.CASH_DEPOSIT,
            source_account_id=None,
            target_account_id=account.id,
        )
        await db.commit()
        return {
            "hasPIN": True,
            "currentBalance": float(account.balance),
            "msg": "Cash deposited successfully",
        }

    async def withdraw(self, db: AsyncSession, account_number: str, amount: float, pin: str) -> dict:
        _, account = await self._get_user_and_account(db, account_number)
        if not account.pin or not verify_value(pin, account.pin):
            raise ApiError(status_code=401, payload={"error": "Invalid PIN"})
        if float(account.balance) < float(amount):
            raise ApiError(status_code=400, payload={"error": "Insufficient balance"})

        account.balance = float(account.balance) - float(amount)
        await self.transactions.create(
            db,
            amount=float(amount),
            tx_type=TransactionType.CASH_WITHDRAWAL,
            source_account_id=account.id,
            target_account_id=None,
        )
        await db.commit()
        return {
            "hasPIN": True,
            "currentBalance": float(account.balance),
            "msg": "Cash withdrawn successfully",
        }

    async def validate_fund_transfer_payload(self, payload: dict) -> tuple[float, str, str]:
        required_fields = ["amount", "pin", "targetAccountNumber"]
        allowed_fields = set(required_fields)

        for key in payload.keys():
            if key not in allowed_fields:
                raise ApiError(status_code=400, payload={"error": f"Extra field detected: {key}"})

        if payload == {}:
            raise ApiError(
                status_code=400,
                payload={
                    "errors": {
                        "targetAccountNumber": "Target account number cannot be empty",
                        "pin": "PIN cannot be empty",
                        "amount": "Amount cannot be empty",
                    }
                },
            )

        errors: dict[str, str] = {}
        amount_raw = payload.get("amount")
        pin_raw = payload.get("pin")
        target_raw = payload.get("targetAccountNumber")

        if target_raw is None or str(target_raw).strip() == "":
            errors["targetAccountNumber"] = "Target account number cannot be empty"
        if pin_raw is None or str(pin_raw).strip() == "":
            errors["pin"] = "PIN cannot be empty"
        if amount_raw is None or (isinstance(amount_raw, str) and amount_raw.strip() == ""):
            errors["amount"] = "Amount cannot be empty"

        if errors:
            raise ApiError(status_code=400, payload={"errors": errors})

        amount_input = amount_raw
        if isinstance(amount_raw, str):
            amount_input = amount_raw.strip()
        try:
            amount = float(str(amount_input))
        except (TypeError, ValueError) as exc:
            raise ApiError(status_code=400, payload={"errors": {"amount": "Amount cannot be empty"}}) from exc

        if amount <= 0:
            raise ApiError(status_code=400, payload={"errors": {"amount": "Amount must be greater than 0"}})
        if amount % 100 != 0:
            raise ApiError(status_code=400, payload={"error": "Amount must be in multiples of 100"})

        return amount, str(pin_raw).strip(), str(target_raw).strip()

    async def transfer(
        self,
        db: AsyncSession,
        source_account_number: str,
        target_account_number: str,
        amount: float,
        pin: str,
    ) -> dict:
        if source_account_number == target_account_number:
            raise ApiError(status_code=400, payload={"error": "Source and target account cannot be the same"})

        async with db.begin():
            source = await self.accounts.get_by_account_number_for_update(db, source_account_number)
            if not source:
                raise ApiError(status_code=404, payload={"error": "Account does not exist"})
            if not source.pin or not verify_value(pin, source.pin):
                raise ApiError(status_code=401, payload={"error": "Invalid PIN"})

            target = await self.accounts.get_by_account_number_for_update(db, target_account_number)
            if not target:
                raise ApiError(status_code=404, payload={"error": "Account does not exist"})
            if float(source.balance) < float(amount):
                raise ApiError(status_code=400, payload={"error": "Insufficient balance"})

            source.balance = float(source.balance) - float(amount)
            target.balance = float(target.balance) + float(amount)

            await self.transactions.create(
                db,
                amount=float(amount),
                tx_type=TransactionType.CASH_TRANSFER,
                source_account_id=source.id,
                target_account_id=target.id,
            )

        return {
            "hasPIN": True,
            "currentBalance": float(source.balance),
            "msg": "Fund transferred successfully",
        }

    async def transactions_for_account(self, db: AsyncSession, account_number: str) -> dict:
        account = await self.accounts.get_by_account_number(db, account_number)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        transactions = await self.transactions.list_for_account(db, account.id)

        account_ids: set[int] = set()
        for tx in transactions:
            if tx.source_account_id is not None:
                account_ids.add(tx.source_account_id)
            if tx.target_account_id is not None:
                account_ids.add(tx.target_account_id)

        account_rows = await self.accounts.get_by_ids(db, account_ids)
        account_number_map = {row.id: row.account_number for row in account_rows}

        serialized = [
            TransactionOut.model_validate(
                {
                    "id": tx.id,
                    "amount": float(tx.amount),
                    "transactionDate": tx.transaction_date,
                    "transactionType": tx.transaction_type.value if tx.transaction_type else None,
                    "sourceAccountNumber": account_number_map.get(tx.source_account_id),
                    "targetAccountNumber": account_number_map.get(tx.target_account_id),
                }
            ).model_dump(by_alias=True)
            for tx in transactions
        ]

        if not serialized:
            return {"transactions": [], "msg": "No transactions found"}

        return {"transactions": serialized, "msg": "Transactions retrieved successfully"}
