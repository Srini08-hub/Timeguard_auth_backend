import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext

from src.config.settings import settings
from src.constants.auth_constant import (
    ACCESS_TOKEN_EXPIRE_SECONDS,
    JWT_ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from src.core.exceptions.custom_exception import (
    ApplicationException,
    UnauthorizedException,
)
from src.data.repositories.user_repository import UserRepository
from src.data.repositories.user_session_repository import UserSessionRepository
from src.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    LoginServiceResponse,
    RefreshTokenResponse,
)

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        user_session_repository: UserSessionRepository,
    ) -> None:
        self.user_repository = user_repository
        self.user_session_repository = user_session_repository

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Verify a plain text password against a hashed password."""
        return bool(pwd_context.verify(plain, hashed))

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token using bcrypt."""
        return str(pwd_context.hash(token))

    @staticmethod
    def create_access_token(data: dict) -> str:
        payload = data.copy()
        payload["exp"] = datetime.now(UTC) + timedelta(
            seconds=ACCESS_TOKEN_EXPIRE_SECONDS
        )
        return str(jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM))

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        payload = data.copy()
        payload["exp"] = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        return str(jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM))

    async def login(self, payload: LoginRequest) -> LoginServiceResponse:
        """Login a user and create a session."""
        user = await self.user_repository.get_active_user_by_email(payload.email)
        if user is None:
            raise UnauthorizedException("Invalid email or password")

        verify = self.verify_password(payload.password, user.password_hash)
        if not verify:
            raise UnauthorizedException("Invalid email or password")

        # Create a session record first to get session_id
        expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token_hash_temp = self.hash_token("temp")
        session = await self.user_session_repository.create_session(
            user_id=user.user_id,
            refresh_token_hash=refresh_token_hash_temp,
            expires_at=expires_at,
        )

        # Include session_id in token data
        data = {
            "sub": str(user.user_id),
            "role": user.role.value,
            "session_id": str(session.session_id),
        }

        access_token = self.create_access_token(data)
        refresh_token = self.create_refresh_token(data)
        refresh_token_hash = self.hash_token(refresh_token)

        # Update session with actual refresh token hash
        await self.user_session_repository.update_session(
            session.session_id, refresh_token_hash=refresh_token_hash
        )

        logger.info(
            f"User {user.email} logged in successfully."
            f" Session ID: {session.session_id}"
        )

        return LoginServiceResponse(
            user=LoginResponse(
                user_id=str(user.user_id),
                name=user.name,
                email=user.email,
                role=user.role.value,
            ),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, refresh_token: str) -> RefreshTokenResponse:
        """Refresh access and refresh tokens with validation."""
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
            )
            user_id_str = payload.get("sub")
            session_id_str = payload.get("session_id")

            logger.info(
                f"Attempting to refresh token for user ID: {user_id_str}, "
                f"Session ID: {session_id_str}"
            )

            user_id = UUID(user_id_str)
            session_id = UUID(session_id_str)

            # Get user from database
            user = await self.user_repository.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise UnauthorizedException("User not found or inactive")

            # Get the specific session
            session = await self.user_session_repository.get_session_by_id(session_id)
            if not session or session.user_id != user_id or session.revoked:
                raise UnauthorizedException("Invalid or revoked session")

            # Verify the refresh token hash
            if not self.verify_password(refresh_token, session.refresh_token_hash):
                raise UnauthorizedException("Invalid refresh token")

            # Include session_id in new token data
            data = {
                "sub": str(user.user_id),
                "role": user.role.value,
                "session_id": str(session_id),
            }
            new_access_token = self.create_access_token(data)
            new_refresh_token = self.create_refresh_token(data)
            new_refresh_token_hash = self.hash_token(new_refresh_token)

            # Update session with new refresh token hash
            await self.user_session_repository.update_session(
                session_id, refresh_token_hash=new_refresh_token_hash
            )

            logger.info("Token refreshed successfully")

            return RefreshTokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
            )

        except ExpiredSignatureError as err:
            logger.warning("Refresh token has expired")
            raise UnauthorizedException("Token expired") from err

        except JWTError as err:
            logger.warning(f"Invalid refresh token: {str(err)}")
            raise UnauthorizedException("Invalid token") from err

    async def logout(self, refresh_token: str | None) -> None:
        """Logout a user by revoking their specific session."""
        if not refresh_token:
            return
        try:
            # Decode refresh token to get session_id
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
            )
            session_id_str = payload.get("session_id")

            session_id = UUID(session_id_str)

            # Verify session exists
            session = await self.user_session_repository.get_session_by_id(session_id)
            if not session:
                raise UnauthorizedException("Session not found")

            # Revoke the specific session
            revoked = await self.user_session_repository.revoke_session(session_id)

            if revoked:
                logger.info(
                    f"Session {session_id} revoked "
                    f"successfully for user {session.user_id}"
                )
            else:
                raise ApplicationException("Failed to revoke session", status_code=500)
        except JWTError as err:
            raise UnauthorizedException("Invalid access token") from err
        except Exception as err:
            logger.error(f"Error during logout: {str(err)}")
            raise ApplicationException(
                f"Logout failed: {str(err)}", status_code=500
            ) from err
