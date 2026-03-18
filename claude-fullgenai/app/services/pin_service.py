"""
PIN management service: create, update, check.

Note on create_pin validation:
  Java returns {"errors": {"pin":..,"password":..}} when BOTH are missing,
  but {"error": "PIN cannot be empty"} (400) or {"error": "Password cannot be empty"} (401)
  when only one is missing. We replicate this split behavior here.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from app.models import Account, User
from app.repositories import AccountRepository
from app.security import hash_pin, verify_pin, verify_password
from app.schemas import PinCreateRequest, PinUpdateRequest


class PinService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)

    async def _load_user(self, account: Account) -> User:
        result = await self.db.execute(
            select(User).where(User.id == account.user_id)
        )
        return result.scalar_one()

    async def create_pin(self, account: Account, req: PinCreateRequest) -> dict:
        pin_missing = not req.pin or not req.pin.strip()
        pw_missing = not req.password or not req.password.strip()

        # Both missing → {"errors": {}}
        if pin_missing and pw_missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": {
                    "pin": "PIN cannot be empty",
                    "password": "Password cannot be empty",
                }},
            )

        # Only pin missing → {"error": "PIN cannot be empty"} 400
        if pin_missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "PIN cannot be empty"},
            )

        # Only password missing → {"error": "Password cannot be empty"} 401
        if pw_missing:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Password cannot be empty"},
            )

        user = await self._load_user(account)
        if not verify_password(req.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid password"},
            )

        if account.pin is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "PIN already created"},
            )

        account.pin = hash_pin(req.pin)
        await self.account_repo.save(account)
        await self.db.commit()
        return {"hasPIN": True, "msg": "PIN created successfully"}

    async def update_pin(self, account: Account, req: PinUpdateRequest) -> dict:
        if account.pin is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "PIN not set"},
            )

        if not verify_pin(req.oldPin, account.pin):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid PIN"},
            )

        user = await self._load_user(account)
        if not verify_password(req.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid password"},
            )

        account.pin = hash_pin(req.newPin)
        await self.account_repo.save(account)
        await self.db.commit()
        return {"hasPIN": True, "msg": "PIN updated successfully"}

    async def check_pin(self, account: Account) -> dict:
        pin_created = account.pin is not None
        if pin_created:
            msg = "PIN has been created for this account"
        else:
            msg = "PIN has not been created for this account"
        return {"isPinCreated": pin_created, "msg": msg}


