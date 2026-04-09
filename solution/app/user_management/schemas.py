from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
import uuid
from ..enums.enums import Gender, MaritalStatus, UserRole
from ..utils.validators import validate_password

class User(BaseModel):
    id: uuid.UUID
    email: EmailStr
    fullName: str = Field(..., min_length=2, max_length=200)
    age: Optional[int] = None
    region: Optional[str] = Field(None, max_length=32)
    gender: Optional[Gender] = None
    maritalStatus: Optional[MaritalStatus] = None
    role: UserRole
    isActive: bool = Field(default=True)
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class UserCreateRequest(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=72)
    fullName: str = Field(..., min_length=2, max_length=200)
    age: Optional[int] = Field(None, ge=18, le=120)
    region: Optional[str] = Field(None, max_length=32)
    gender: Optional[Gender] = None
    maritalStatus: Optional[MaritalStatus] = None
    role: UserRole

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return validate_password(cls, v)

class UserUpdateRequest(BaseModel):
    fullName: Optional[str] = Field(None, min_length=2, max_length=200)
    age: Optional[int] = Field(None, ge=18, le=120)
    region: Optional[str] = Field(None, max_length=32)
    gender: Optional[Gender] = None
    maritalStatus: Optional[MaritalStatus] = None
    role: Optional[UserRole] = None
    isActive: Optional[bool] = None

class PagedUsers(BaseModel):
    items: list[User]
    total: int
    page: int
    size: int
