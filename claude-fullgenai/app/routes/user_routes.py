"""
User routes: Register + Login  (2 endpoints)
POST /api/users/register
POST /api/users/login
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import RegisterRequest, LoginRequest
from app.services import UserService

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register", status_code=200)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.register(req)


@router.post("/login", status_code=200)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.login(req)
