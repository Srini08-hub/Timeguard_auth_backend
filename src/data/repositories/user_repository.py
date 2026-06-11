import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

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
        query = select(User).where(User.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_user_by_email(self, email: str) -> User | None:
        """Get an active user by email."""
        query = select(User).where(
            and_(
                User.email == email,
                User.is_active.is_(True),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_users(self) -> list[User]:
        """Get all users."""
        query = select(User)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def deactivate_user(self, user_id: uuid.UUID) -> bool:
        """Deactivate a user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        user.is_active = False
        await self.db.flush()
        return True

    async def activate_user(self, user_id: uuid.UUID) -> bool:
        """Activate a user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        user.is_active = True
        await self.db.flush()
        return True

    async def user_exists_by_email(self, email: str) -> bool:
        """Check if a user exists by email."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete a user by user_id."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        await self.db.delete(user)
        await self.db.flush()
        return True
