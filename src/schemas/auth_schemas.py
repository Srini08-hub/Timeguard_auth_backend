from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    user_id: str
    name: str
    email: str
    role: str


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str


class LoginServiceResponse(BaseModel):
    user: LoginResponse
    access_token: str
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
