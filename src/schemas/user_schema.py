from pydantic import BaseModel


class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
