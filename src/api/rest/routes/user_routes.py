from fastapi import APIRouter, Cookie, Depends, status

from src.api.rest.dependencies.services import get_user_service
from src.constants.auth_constant import (
    ACCESS_TOKEN_COOKIE,
)
from src.core.services.user_service import UserService
from src.schemas.user_schema import UserResponse

router = APIRouter()


@router.get("/users/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user(
    user_service: UserService = Depends(get_user_service),
    access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
) -> UserResponse:
    return await user_service.get_current_user(access_token)
