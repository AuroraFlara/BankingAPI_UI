from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_account_number_from_token
from app.core.request_parser import parse_json_object
from app.db.database import get_db
from app.services.account_service import AccountService


router = APIRouter(prefix="/api/account", tags=["account"])
service = AccountService()


@router.post("/pin/create")
async def create_pin(
    request: Request,
    account_number: str = Depends(get_account_number_from_token),
    db: AsyncSession = Depends(get_db),
):
    payload = await parse_json_object(request)
    pin, password = await service.validate_create_pin_payload(payload)
    return await service.create_pin(db, account_number, pin, password)


@router.post("/pin/update")
async def update_pin(
    request: Request,
    account_number: str = Depends(get_account_number_from_token),
    db: AsyncSession = Depends(get_db),
):
    payload = await parse_json_object(request)
    old_pin, new_pin, password = await service.validate_update_pin_payload(payload)
    return await service.update_pin(db, account_number, old_pin, new_pin, password)


@router.get("/pin/check")
async def check_pin(
    account_number: str = Depends(get_account_number_from_token),
    db: AsyncSession = Depends(get_db),
):
    return await service.check_pin(db, account_number)


@router.post("/deposit")
async def deposit(
    request: Request,
    account_number: str = Depends(get_account_number_from_token),
    db: AsyncSession = Depends(get_db),
):
    payload = await parse_json_object(request)
    amount, pin = await service.validate_cash_payload(payload)
    return await service.deposit(db, account_number, amount, pin)


@router.post("/withdraw")
async def withdraw(
    request: Request,
    account_number: str = Depends(get_account_number_from_token),
    db: AsyncSession = Depends(get_db),
):
    payload = await parse_json_object(request)
    amount, pin = await service.validate_cash_payload(payload)
    return await service.withdraw(db, account_number, amount, pin)


@router.post("/fund-transfer")
async def fund_transfer(
    request: Request,
    account_number: str = Depends(get_account_number_from_token),
    db: AsyncSession = Depends(get_db),
):
    payload = await parse_json_object(request)
    amount, pin, target_account_number = await service.validate_fund_transfer_payload(payload)
    return await service.transfer(db, account_number, target_account_number, amount, pin)


@router.get("/transactions")
async def transactions(
    account_number: str = Depends(get_account_number_from_token),
    db: AsyncSession = Depends(get_db),
):
    return await service.transactions_for_account(db, account_number)
