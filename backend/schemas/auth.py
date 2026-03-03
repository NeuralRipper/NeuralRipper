from pydantic import BaseModel, ConfigDict


class GoogleLoginRequest(BaseModel):
    token: str  # Google ID token from frontend


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    id: int
    email: str
    name: str | None
    avatar_url: str | None
    model_config = ConfigDict(from_attributes=True)
