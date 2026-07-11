from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class CreatePakarRequest(BaseModel):
    fullname: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: str = Field(..., min_length=10)


class ApproveDeviceRequest(BaseModel):
    silo_id: UUID
    nama: str = Field(..., min_length=3)
    tipe: str = Field(default="esp32")