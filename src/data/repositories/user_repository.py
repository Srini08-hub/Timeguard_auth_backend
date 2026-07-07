import uuid

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.custom_exception import DatabaseException
from src.data.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(
        self,
        email: str,
        password_hash: str,
        name: str,
        role: UserRole,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get a user by user_id."""
        try:
            query = select(User).where(User.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as err:
            raise DatabaseException("Failed to fetch user") from err

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        try:
            query = select(User).where(User.email == email)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as err:
            raise DatabaseException("Failed to fetch user") from err

    async def get_active_user_by_email(self, email: str) -> User | None:
        """Get an active user by email."""
        try:
            query = select(User).where(
                and_(
                    User.email == email,
                    User.is_active.is_(True),
                )
            )
            result = await self.db.execute(query)
        except SQLAlchemyError as err:
            raise DatabaseException("Failed to fetch user") from err
        return result.scalar_one_or_none()

    async def get_all_users(self) -> list[User]:
        """Get all users."""
        try:
            query = select(User).where(User.is_active.is_(True))
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as err:
            raise DatabaseException("Failed to fetch users") from err

    async def deactivate_user(self, user: User) -> bool:
        """Deactivate a user."""
        try:
            user.is_active = False
            await self.db.flush()
            return True
        except SQLAlchemyError as err:
            raise DatabaseException("Failed to deactivate user") from err

    async def activate_user(self, user_id: uuid.UUID) -> bool:
        """Activate a user."""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            user.is_active = True
            await self.db.flush()
            return True
        except SQLAlchemyError as err:
            raise DatabaseException("Failed to activate user") from err

    # async def user_exists_by_email(self, email: str) -> bool:
    #     """Check if a user exists by email."""
    #     try:
    #         query = select(User).where(User.email == email)
    #         result = await self.db.execute(query)
    #         return result.scalar_one_or_none() is not None
    #     except SQLAlchemyError as err:
    #         raise DatabaseException("Failed to check user existence") from err

    async def update_user(
        self,
        user_id: uuid.UUID,
        name: str | None = None,
        email: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> User | None:
        """Update a user by user_id."""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            if name is not None:
                user.name = name
            if email is not None:
                user.email = email
            if role is not None:
                user.role = role
            if is_active is not None:
                user.is_active = is_active
            await self.db.flush()
            return user
        except SQLAlchemyError as err:
            raise DatabaseException("Failed to update user") from err

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete a user by user_id."""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            await self.db.delete(user)
            await self.db.flush()
            return True
        except SQLAlchemyError as err:
            raise DatabaseException("Failed to delete user") from err
