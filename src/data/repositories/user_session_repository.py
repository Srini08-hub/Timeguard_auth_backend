import uuid
from datetime import datetime
from typing import Any, cast

from sqlalchemy import CursorResult, and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.user_session import UserSession


class UserSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        user_id: uuid.UUID,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> UserSession:
        """Create a new user session."""
        session = UserSession(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session_by_id(self, session_id: uuid.UUID) -> UserSession | None:
        """Get a session by session_id."""
        query = select(UserSession).where(UserSession.session_id == session_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_sessions_by_user_id(self, user_id: uuid.UUID) -> list[UserSession]:
        """Get all sessions for a specific user."""
        query = select(UserSession).where(UserSession.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_sessions_by_user(
        self, user_id: uuid.UUID
    ) -> list[UserSession]:
        """Get active (non-revoked and non-expired) sessions for a user."""
        query = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.revoked.is_(False),
                UserSession.expires_at > datetime.utcnow(),
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def revoke_session(self, session_id: uuid.UUID) -> bool:
        """Mark a session as revoked."""
        session = await self.get_session_by_id(session_id)
        if not session:
            return False
        session.revoked = True
        await self.db.flush()
        return True

    async def revoke_all_user_sessions(self, user_id: uuid.UUID) -> int:
        """Revoke all sessions for a user."""
        query = (
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.revoked.is_(False))
        )
        result = await self.db.execute(query)
        sessions = result.scalars().all()
        for session in sessions:
            session.revoked = True
        await self.db.flush()
        return len(sessions)

    async def delete_session(self, session_id: uuid.UUID) -> bool:
        """Delete a session."""
        query = delete(UserSession).where(UserSession.session_id == session_id)
        result = cast(
            CursorResult,
            await self.db.execute(query),
        )
        await self.db.flush()
        return result.rowcount > 0

    async def delete_expired_sessions(self) -> int:
        """Delete all expired sessions."""
        query = delete(UserSession).where(UserSession.expires_at <= datetime.utcnow())
        result = cast(
            CursorResult,
            await self.db.execute(query),
        )

        await self.db.flush()
        return result.rowcount

    async def check_session_exists(self, session_id: uuid.UUID) -> bool:
        """Check if a session exists."""
        query = select(UserSession).where(UserSession.session_id == session_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def update_session(
        self,
        session_id: uuid.UUID,
        **kwargs: Any,
    ) -> UserSession | None:
        """Update a session by session_id.
        Accepts keyword arguments for fields to update."""
        session = await self.get_session_by_id(session_id)
        if not session:
            return None
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        await self.db.flush()
        return session
