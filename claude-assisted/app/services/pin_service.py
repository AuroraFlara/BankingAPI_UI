"""
PINService: create and update account PINs.

Parity targets:
  AccountServiceImpl.createPIN() -> create_pin()
  AccountServiceImpl.updatePIN() -> update_pin()
  AccountServiceImpl.isPINCreated() -> is_pin_created()

Phase 2 ground truth:
  create_pin  : auth by password, 409 on duplicate
  update_pin  : verify password THEN oldPin (both 401); newPin already format-validated by schema
  is_pin_created: conditional message strings

Performance: account.user accessed via joinedload set in get_current_account — no extra query.
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Account
from app.repositories.account_repository import AccountRepository
from app.security import hash_password, verify_password


class PINService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._account_repo = AccountRepository(db)

    async def create_pin(self, account: Account, pin: str, password: str) -> dict:
        """
        Auth: verify the account owner’s password (account.user loaded via joinedload).
        Guard: reject with 409 if PIN already set.
        """
        if not verify_password(password, account.user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password",
            )
        if account.pin is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="PIN already created",
            )
        account.pin = hash_password(pin)
        await self._account_repo.save(account)
        return {"hasPIN": True, "msg": "PIN created successfully"}

    async def update_pin(
        self,
        account: Account,
        old_pin: str,
        new_pin: str,
        password: str,
    ) -> dict:
        """
        Auth order (ground truth):
          1. Verify password  → 401 "Invalid password"
          2. Verify oldPin    → 401 "Invalid PIN"
        newPin format (4 digits) already validated by UpdatePINRequest schema.
        """
        if not verify_password(password, account.user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password",
            )
        if account.pin is None or not verify_password(old_pin, account.pin):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid PIN",
            )
        account.pin = hash_password(new_pin)
        await self._account_repo.save(account)
        return {"hasPIN": True, "msg": "PIN updated successfully"}

    async def is_pin_created(self, account: Account) -> dict:
        if account.pin is not None:
            return {"isPinCreated": True, "msg": "PIN has been created for this account"}
        return {"isPinCreated": False, "msg": "PIN has not been created for this account"}
