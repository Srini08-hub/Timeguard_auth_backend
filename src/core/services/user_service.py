import logging
from uuid import UUID

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext

from src.config.settings import settings
from src.constants.auth_constant import JWT_ALGORITHM
from src.core.exceptions.custom_exception import (
    ConflictException,
    ResourceNotFound,
    UnauthorizedException,
)
from src.data.repositories.user_repository import UserRepository
from src.schemas.user_schema import UserCreate, UserResponse, UserUpdate

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def get_current_user(self, access_token: str) -> UserResponse:
        """Get the current user from the access token."""
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

    async def get_all_users(self) -> list[UserResponse]:
        """Get all users from repository."""
        users = await self.user_repository.get_all_users()
        return [
            UserResponse(
                user_id=str(user.user_id),
                name=user.name,
                email=user.email,
                role=user.role.value,
            )
            for user in users
        ]

    async def create_user(self, payload: UserCreate) -> UserResponse:
        """Create a new user with hashed password."""
        existing_user = await self.user_repository.get_user_by_email(payload.email)
        if existing_user:
            raise ConflictException("Email already exists")
        hashed_password = pwd_context.hash(payload.password)
        user = await self.user_repository.create_user(
            email=payload.email,
            password_hash=hashed_password,
            name=payload.name,
            role=payload.role,
        )
        logger.info(f"User created with ID: {user.user_id}")
        return UserResponse(
            user_id=str(user.user_id),
            name=user.name,
            email=user.email,
            role=user.role.value,
        )

    async def update_user(self, user_id: UUID, payload: UserUpdate) -> UserResponse:
        """Update user details."""
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFound("User not found")

        if payload.name is not None:
            user.name = payload.name
        if payload.email is not None:
            user.email = payload.email
        if payload.role is not None:
            user.role = payload.role
        if payload.is_active is not None:
            user.is_active = payload.is_active

        await self.user_repository.db.flush()

        return UserResponse(
            user_id=str(user.user_id),
            name=user.name,
            email=user.email,
            role=user.role.value,
        )

    async def delete_user(self, user_id: UUID) -> None:
        """Delete a user."""
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFound("User not found")
        await self.user_repository.deactivate_user(user)
        logger.info(f"User deleted with ID: {user_id}")
        return None
