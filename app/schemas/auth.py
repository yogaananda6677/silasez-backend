from uuid import UUID

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    fullname: str
    email: EmailStr
    password: str
    phone: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    fullname: str
    email: EmailStr
    phone: str | None
    role: str

    model_config = {
        "from_attributes": True
    }

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

