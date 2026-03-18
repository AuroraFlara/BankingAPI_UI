from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.user_schemas import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/register", response_model=RegisterResponse, status_code=200)
async def register_user(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.register_user(payload.model_dump())


@router.post("/login", response_model=LoginResponse)
async def login_user(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.login_user(payload.identifier, payload.password)
