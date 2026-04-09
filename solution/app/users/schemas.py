from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from ..enums.enums import Gender, MaritalStatus, UserRole
from ..utils.validators import validate_password

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=72)
    fullName: str = Field(..., min_length=2, max_length=200)
    age: Optional[int] = Field(None, ge=18, le=120)
    region: Optional[str] = Field(None, max_length=32)
    gender: Optional[Gender] = None
    maritalStatus: Optional[MaritalStatus] = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return validate_password(cls, v)

class UserResponse(BaseModel):
    id: str
    email: str
    fullName: str
    age: Optional[int] = None
    region: Optional[str] = None
    gender: Optional[Gender] = None
    maritalStatus: Optional[MaritalStatus] = None
    role: UserRole
    isActive: bool
    createdAt: str
    updatedAt: str

class AuthResponse(BaseModel):
    accessToken: str
    expiresIn: int = 3600
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=72)
