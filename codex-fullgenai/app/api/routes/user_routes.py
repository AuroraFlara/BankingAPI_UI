from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import APIError
from app.db.session import get_db
from app.schemas import LoginRequest, RegisterRequest
from app.services import UserService


router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register", status_code=status.HTTP_200_OK)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.register(payload)


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    if getattr(request.state, "login_invalid_structure", False):
        raise APIError(status_code=400, message="Invalid request structure")
    service = UserService(db)
    return await service.login(payload)
