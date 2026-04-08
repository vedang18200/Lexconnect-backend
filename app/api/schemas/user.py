"""User schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: EmailStr
    user_type: str  # citizen, lawyer, admin
    phone: Optional[str] = None
    location: Optional[str] = None
    language: Optional[str] = None

class UserCreate(UserBase):
    """User creation schema"""
    password: str

class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    language: Optional[str] = None

class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """User list response"""
    id: int
    username: str
    email: str
    user_type: str
    is_active: bool
    created_at: datetime


class ChangePasswordRequest(BaseModel):
    """Change password request payload"""
    current_password: str
    new_password: str


class MessageResponse(BaseModel):
    """Generic success message"""
    success: bool
    message: str
