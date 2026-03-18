"""
DashboardService: returns the authenticated user's profile and account details.

Parity targets:
  DashboardServiceImpl.getUserDetails()    -> get_user()
  DashboardServiceImpl.getAccountDetails() -> get_account()

GET /api/dashboard/user ground truth response:
  {
    "user": {
      "name", "email", "countryCode", "phoneNumber", "address",
      "accountNumber", "ifscCode", "branch", "accountType"
    },
    "msg": "User details retrieved successfully"
  }
"""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Account, User
from app.schemas.account_schemas import AccountOutCamel
from app.schemas.user_schemas import UserOutCamel


def _map_user_with_account(user: User, account: Account) -> UserOutCamel:
    """Merge user + account fields into the UserOutCamel shape (ground truth)."""
    return UserOutCamel(
        name=user.name,
        email=user.email,
        countryCode=user.country_code,
        phoneNumber=user.phone_number,
        address=user.address,
        accountNumber=account.account_number,
        ifscCode=account.ifsc_code,
        branch=account.branch,
        accountType=account.account_type,
    )


def _map_account(account: Account) -> AccountOutCamel:
    return AccountOutCamel(
        id=account.id,
        accountNumber=account.account_number,
        accountType=account.account_type,
        accountStatus=account.account_status,
        balance=account.balance,
        branch=account.branch,
        ifscCode=account.ifsc_code,
    )


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_user(self, account: Account) -> dict:
        result = await self._db.execute(
            select(User).where(User.id == account.user_id)
        )
        user = result.scalars().first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return {
            "user": _map_user_with_account(user, account),
            "msg": "User details retrieved successfully",
        }

    async def get_account(self, account: Account) -> dict:
        return {
            "account": _map_account(account),
            "msg": "Account details retrieved successfully",
        }
