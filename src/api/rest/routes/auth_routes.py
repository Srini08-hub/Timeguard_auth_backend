import logging

from fastapi import APIRouter, Cookie, Depends, status

from src.api.rest.dependencies.services import get_auth_service
from src.core.services.auth_service import AuthService
from src.schemas.auth_schemas import (
    LoginRequest,
    LoginServiceResponse,
    RefreshTokenResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login", response_model=LoginServiceResponse, status_code=status.HTTP_200_OK
)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginServiceResponse:
    auth_response = await auth_service.login(payload)

    return auth_response


@router.post(
    "/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK
)
async def refresh(
    refresh_token: str = Cookie(),
    auth_service: AuthService = Depends(get_auth_service),
) -> RefreshTokenResponse:
    auth_response = await auth_service.refresh(refresh_token)
    return auth_response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: str = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    await auth_service.logout(refresh_token)
    return
