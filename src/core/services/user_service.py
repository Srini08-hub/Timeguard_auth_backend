import logging
from uuid import UUID

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from src.config.settings import settings
from src.constants.auth_constant import JWT_ALGORITHM
from src.core.exceptions.custom_exception import (
    UnauthorizedException,
)
from src.data.repositories.user_repository import UserRepository
from src.schemas.user_schema import UserResponse

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def get_current_user(self, access_token: str | None) -> UserResponse:
        """Get the current user from the access token."""
        if not access_token:
            raise UnauthorizedException("Access token is missing")
        try:
            payload = jwt.decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
            )
        except ExpiredSignatureError as err:
            raise UnauthorizedException("Token expired") from err
        except JWTError as err:
            raise UnauthorizedException("Invalid token") from err
        user_id_str = payload.get("sub")
        user_id = UUID(user_id_str)

        user = await self.user_repository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")
        return UserResponse(
            user_id=str(user.user_id),
            name=user.name,
            email=user.email,
            role=user.role.value,
        )
