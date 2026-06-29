from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Path, status

from src.api.rest.dependencies.services import get_user_service
from src.core.services.user_service import UserService
from src.schemas.user_schema import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user(
    user_service: UserService = Depends(get_user_service),
    access_token: str = Cookie(),
) -> UserResponse:
    return await user_service.get_current_user(access_token)


@router.get("", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_users(
    user_service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    return await user_service.get_all_users()


# @router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
# async def get_user(
#     user_id: UUID=Path(..., description="User ID to get"),
#     user_service: UserService = Depends(get_user_service),
# ) -> UserResponse:
#     return await user_service.get_user(user_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await user_service.create_user(payload)


@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    payload: UserUpdate,
    user_id: UUID = Path(..., description="User ID to update"),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await user_service.update_user(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID = Path(..., description="User ID to delete"),
    user_service: UserService = Depends(get_user_service),
) -> None:
    await user_service.delete_user(user_id)
