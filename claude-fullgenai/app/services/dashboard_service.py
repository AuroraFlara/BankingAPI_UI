"""
Dashboard service: return user and account details.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Account, User


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_details(self, account: Account) -> dict:
        result = await self.db.execute(
            select(User).where(User.id == account.user_id)
        )
        user: User = result.scalar_one()
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

    async def get_account_details(self, account: Account) -> dict:
        return {
            "account": {
                "id": account.id,
                "accountNumber": account.account_number,
                "accountType": account.account_type,
                "accountStatus": account.account_status,
                "balance": account.balance,
                "branch": account.branch,
                "ifscCode": account.ifsc_code,
            },
            "msg": "Account details retrieved successfully",
        }
