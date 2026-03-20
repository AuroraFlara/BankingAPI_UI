from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import APIError, ValidationAPIError
from app.core.security import hash_value, verify_hash
from app.repositories import AccountRepository
from app.schemas import PinCreateRequest, PinUpdateRequest


class PinService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)

    async def create_pin(self, account, payload: PinCreateRequest) -> dict:
        if not verify_hash(payload.password, account.user.password):
            raise APIError(status_code=401, message="Invalid password")

        if account.pin:
            raise APIError(status_code=409, message="PIN already created")

        account.pin = hash_value(payload.pin)
        await self.account_repo.save(account)
        await self._commit_or_rollback()

        return {"hasPIN": True, "msg": "PIN created successfully"}

    async def update_pin(self, account, payload: PinUpdateRequest) -> dict:
        if not account.pin:
            raise APIError(status_code=404, message="PIN not found")

        if not verify_hash(payload.password, account.user.password):
            raise APIError(status_code=401, message="Invalid password")

        if not payload.new_pin.isdigit() or len(payload.new_pin) != 4:
            raise ValidationAPIError(status_code=400, errors={"newPin": "PIN must be exactly 4 digits"})

        if not verify_hash(payload.old_pin, account.pin):
            raise APIError(status_code=401, message="Invalid PIN")

        account.pin = hash_value(payload.new_pin)
        await self.account_repo.save(account)
        await self._commit_or_rollback()

        return {"hasPIN": True, "msg": "PIN updated successfully"}

    @staticmethod
    def check_pin(account) -> dict:
        is_created = bool(account.pin)
        return {
            "isPinCreated": is_created,
            "msg": "PIN has been created for this account" if is_created else "PIN has not been created for this account",
        }

    async def _commit_or_rollback(self) -> None:
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
