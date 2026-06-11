import logging

from fastapi import APIRouter, Cookie, Depends, Response, status

from src.api.rest.dependencies.services import get_auth_service
from src.constants.auth_constant import (
    ACCESS_TOKEN_COOKIE,
    ACCESS_TOKEN_EXPIRE_SECONDS,
    REFRESH_TOKEN_COOKIE,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from src.core.services.auth_service import AuthService
from src.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_SECONDS,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path="/")


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    auth_response = await auth_service.login(payload)
    _set_auth_cookies(
        response,
        auth_response.access_token,
        auth_response.refresh_token,
    )
    return auth_response.user


@router.post(
    "/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK
)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
    auth_service: AuthService = Depends(get_auth_service),
) -> RefreshTokenResponse:
    auth_response = await auth_service.refresh(refresh_token)
    if auth_response is None:
        _clear_auth_cookies(response)
        return RefreshTokenResponse()
    _set_auth_cookies(
        response,
        auth_response["access_token"],
        auth_response["refresh_token"],
    )
    return RefreshTokenResponse()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    await auth_service.logout(refresh_token)
    _clear_auth_cookies(response)
