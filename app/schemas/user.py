from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserProfileResponse(BaseModel):
    id: UUID
    fullname: str
    email: EmailStr
    phone: str | None
    role: str
    is_active: bool
    photo_url: str | None = None

    model_config = {
        "from_attributes": True
    }


class UpdateProfileRequest(BaseModel):
    fullname: str | None = None
    phone: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)


class UserResponse(BaseModel):
    id: UUID
    fullname: str
    email: EmailStr
    phone: str | None
    photo_url: str | None = None

    class Config:
        from_attributes = True