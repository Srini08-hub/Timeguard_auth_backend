from pydantic import BaseModel

from src.data.models.user import UserRole


class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    role: str


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
