"""Authentication schemas"""
from pydantic import BaseModel

class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str
