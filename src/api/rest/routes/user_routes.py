from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, status

from src.api.rest.dependencies.services import get_user_service
from src.constants.auth_constant import (
    ACCESS_TOKEN_COOKIE,
)
from src.core.services.user_service import UserService
from src.schemas.user_schema import UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.get("/users/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user(
    user_service: UserService = Depends(get_user_service),
    access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
) -> UserResponse:
    return await user_service.get_current_user(access_token)


@router.get("/user", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_users(
    user_service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    return await user_service.get_all_users()


@router.post("/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await user_service.create_user(payload)


@router.patch(
    "/user/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK
)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await user_service.update_user(user_id, payload)
