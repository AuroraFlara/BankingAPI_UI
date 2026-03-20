class DashboardService:
    @staticmethod
    def user_dashboard(account) -> dict:
        user = account.user
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
            }
            ,
            "msg": "User details retrieved successfully",
        }

    @staticmethod
    def account_dashboard(account) -> dict:
        return {
            "account": {
                "id": account.id,
                "accountNumber": account.account_number,
                "accountType": account.account_type,
                "accountStatus": account.account_status,
                "balance": float(account.balance),
                "branch": account.branch,
                "ifscCode": account.ifsc_code,
            },
            "msg": "Account details retrieved successfully",
        }
