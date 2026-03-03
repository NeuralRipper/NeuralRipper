from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    google_id: str
    email: str
    name: str | None = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    model_config = ConfigDict(from_attributes=True)     # for pydantic to convert it to ORM
