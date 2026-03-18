"""Application business logic.

Keep service functions small and explicit. They validate inputs, call
repository helpers, and return tuples of `(body, status_code)` where the
body is already shaped to match the Java API responses.
"""

import secrets
from .auth import hash_password, verify_password, create_token
from .repositories import (
    create_user,
    create_account,
    get_account_by_number,
    get_user_by_email,
    get_user_by_phone,
    save_token,
    save_transaction,
    list_transactions_for_account,
    get_account_by_id,
    revoke_token,
)
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from .models import TransactionType


async def register_user(
    db: AsyncSession,
    name: str,
    email: str,
    password: str,
    phone_number: str,
    address: str,
    country_code: str,
):
    existing = await get_user_by_email(db, email)
    if existing:
        return {"error": "Email already exists"}, 400
    existing_phone = await get_user_by_phone(db, phone_number)
    if existing_phone:
        return {"error": "Phone number already exists"}, 400

    # Validate phone number format: must be numeric for this service.
    # If it's not numeric, return the Java-shaped error message.
    if not phone_number.isdigit():
        return {"error": f"Invalid phone number: {phone_number} for country code: {country_code}"}, 400

    hashed = hash_password(password)
    user = await create_user(
        db,
        name=name,
        email=email,
        password=hashed,
        phone_number=phone_number,
        address=address,
        country_code=country_code,
    )
    # create account
    acc_num = secrets.token_hex(3)
    account = await create_account(
        db,
        account_number=acc_num,
        account_type="Savings",
        balance=0.0,
        user_id=user.id,
        branch="NIT",
        ifsc_code="NIT001",
    )
    await db.commit()
    return {
        "name": user.name,
        "email": user.email,
        "countryCode": user.country_code,
        "phoneNumber": user.phone_number,
        "address": user.address,
        "accountNumber": acc_num,
        "ifscCode": "NIT001",
        "branch": "NIT",
        "accountType": "Savings",
        "msg": "User registered successfully",
    }, 200


async def login(db: AsyncSession, identifier: str, password: str):
    account = await get_account_by_number(db, identifier)
    if not account:
        return {"error": f"User not found for the given identifier: {identifier}"}, 400
    user = account.user
    if not verify_password(password, user.password):
        return {"error": "Invalid identifier or password"}, 401
    token = create_token(account.account_number)
    await save_token(db, token, account.id)
    await db.commit()
    return {"token": token}, 200


async def create_pin(db: AsyncSession, account_number: str, password: str, pin: str):
    account = await get_account_by_number(db, account_number)
    if not account:
        return {"error": "Account not found"}, 404
    if not verify_password(password, account.user.password):
        return {"error": "Invalid password"}, 401
    if account.pin:
        return {"error": "PIN already created"}, 409
    hashed_pin = hash_password(pin)
    account.pin = hashed_pin
    await db.commit()
    return {"hasPIN": True, "msg": "PIN created successfully"}, 200


async def verify_pin_and_deposit(
    db: AsyncSession, account_number: str, pin: str, amount: float
):
    account = await get_account_by_number(db, account_number)
    if not account:
        return {"error": "Account not found"}, 404
    if not account.pin or not verify_password(pin, account.pin):
        return {"error": "Invalid PIN"}, 401
    account.balance = float(account.balance) + float(amount)
    tx = await save_transaction(
        db,
        amount=amount,
        transaction_type=TransactionType.CASH_DEPOSIT,
        target_account_id=account.id,
        transaction_date=datetime.utcnow(),
    )
    await db.commit()
    return {
        "hasPIN": True,
        "currentBalance": float(account.balance),
        "msg": "Cash deposited successfully",
    }, 200


async def verify_pin_and_withdraw(
    db: AsyncSession, account_number: str, pin: str, amount: float
):
    account = await get_account_by_number(db, account_number)
    if not account:
        return {"error": "Account not found"}, 404
    if not account.pin or not verify_password(pin, account.pin):
        return {"error": "Invalid PIN"}, 401
    if float(account.balance) < float(amount):
        return {"error": "Insufficient balance"}, 400
    account.balance = float(account.balance) - float(amount)
    tx = await save_transaction(
        db,
        amount=amount,
        transaction_type=TransactionType.CASH_WITHDRAWAL,
        source_account_id=account.id,
        transaction_date=datetime.utcnow(),
    )
    await db.commit()
    return {
        "hasPIN": True,
        "currentBalance": float(account.balance),
        "msg": "Cash withdrawn successfully",
    }, 200


async def verify_pin_and_transfer(
    db: AsyncSession,
    account_number: str,
    pin: str,
    target_account_number: str,
    amount: float,
):
    source = await get_account_by_number(db, account_number)
    target = await get_account_by_number(db, target_account_number)
    if not source or not target:
        return {"error": "Account does not exist"}, 404
    if source.account_number == target.account_number:
        return {"error": "Source and target account cannot be the same"}, 400
    if not source.pin or not verify_password(pin, source.pin):
        return {"error": "Invalid PIN"}, 401
    if float(source.balance) < float(amount):
        return {"error": "Insufficient balance"}, 400
    source.balance = float(source.balance) - float(amount)
    target.balance = float(target.balance) + float(amount)
    await save_transaction(
        db,
        amount=amount,
        transaction_type=TransactionType.CASH_TRANSFER,
        source_account_id=source.id,
        target_account_id=target.id,
        transaction_date=datetime.utcnow(),
    )
    await db.commit()
    return {
        "hasPIN": True,
        "currentBalance": float(source.balance),
        "msg": "Fund transferred successfully",
    }, 200


async def list_transactions(db: AsyncSession, account_number: str):
    account = await get_account_by_number(db, account_number)
    if not account:
        return {"error": "Account not found"}, 404
    txs = await list_transactions_for_account(db, account.id)
    results = []
    for t in txs:
        src_acc = None
        tgt_acc = None
        if t.source_account_id:
            sa = await get_account_by_id(db, t.source_account_id)
            src_acc = sa.account_number if sa else None
        if t.target_account_id:
            ta = await get_account_by_id(db, t.target_account_id)
            tgt_acc = ta.account_number if ta else None
        results.append(
            {
                "id": int(t.id),
                "amount": float(t.amount),
                "transactionDate": t.transaction_date.strftime("%Y-%m-%d %H:%M:%S"),
                "transactionType": (
                    t.transaction_type.value if t.transaction_type else None
                ),
                "sourceAccountNumber": src_acc,
                "targetAccountNumber": tgt_acc,
            }
        )
    if not results:
        return {"transactions": [], "msg": "No transactions found"}, 200
    return {"transactions": results, "msg": "Transactions retrieved successfully"}, 200


async def is_pin_created(db: AsyncSession, account_number: str):
    account = await get_account_by_number(db, account_number)
    if not account:
        return {"error": "Account not found"}, 404
    if account.pin:
        return {
            "isPinCreated": True,
            "msg": "PIN has been created for this account",
        }, 200
    return {
        "isPinCreated": False,
        "msg": "PIN has not been created for this account",
    }, 200


async def update_pin(
    db: AsyncSession, account_number: str, password: str, old_pin: str, new_pin: str
):
    account = await get_account_by_number(db, account_number)
    if not account:
        return {"error": "Account not found"}, 404
    if not verify_password(password, account.user.password):
        return {"error": "Invalid password"}, 401
    if not account.pin or not verify_password(old_pin, account.pin):
        return {"error": "Invalid PIN"}, 401
    account.pin = hash_password(new_pin)
    await db.commit()
    return {"hasPIN": True, "msg": "PIN updated successfully"}, 200


async def dashboard_user(db: AsyncSession, account_number: str):
    account = await get_account_by_number(db, account_number)
    if not account:
        return {"error": "Account not found"}, 404
    user = account.user
    data = {
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
    return {"user": data, "msg": "User details retrieved successfully"}, 200


async def dashboard_account(db: AsyncSession, account_number: str):
    account = await get_account_by_number(db, account_number)
    if not account:
        return {"error": "Account not found"}, 404
    data = {
        "id": int(account.id),
        "accountNumber": account.account_number,
        "accountType": account.account_type,
        "accountStatus": account.account_status,
        "balance": float(account.balance),
        "branch": account.branch,
        "ifscCode": account.ifsc_code,
    }
    return {"account": data, "msg": "Account details retrieved successfully"}, 200


async def logout_user(db: AsyncSession, token_str: str):
    # revoke persisted token
    obj = await revoke_token(db, token_str)
    if not obj:
        return {"error": "Token not found"}, 404
    await db.commit()
    return {"msg": "Logged out"}, 200
