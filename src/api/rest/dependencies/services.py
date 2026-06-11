from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies.session import get_async_db
from src.core.services.auth_service import AuthService
from src.core.services.user_service import UserService
from src.data.repositories.user_repository import UserRepository
from src.data.repositories.user_session_repository import UserSessionRepository


async def get_auth_service(
    db: AsyncSession = Depends(get_async_db),
) -> AuthService:
    return AuthService(UserRepository(db), UserSessionRepository(db))


async def get_user_service(
    db: AsyncSession = Depends(get_async_db),
) -> UserService:
    return UserService(UserRepository(db))
