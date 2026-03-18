from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request_parser import parse_json_object
from app.db.database import get_db
from app.services.user_service import UserService


router = APIRouter(prefix="/api/users", tags=["users"])
service = UserService()


@router.post("/register")
async def register(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await parse_json_object(request)
    validated = service.validate_register_payload(payload)
    return await service.register_user(db, validated)


@router.post("/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await parse_json_object(request)
    validated = service.validate_login_payload(payload)
    return await service.login_user(db, validated)
