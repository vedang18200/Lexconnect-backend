"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database.db import get_db
from app.api.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest
from app.api.schemas.user import UserCreate, UserResponse
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user_id
)
from app.services.user_service import UserService
from jose import JWTError, jwt
from app.core.config import settings

router = APIRouter()

@router.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    db_user = UserService.create_user(db, user)
    return db_user

@router.post("/auth/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""
    user = UserService.authenticate_user(db, credentials.username, credentials.password)

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(request: RefreshTokenRequest):
    """Refresh access token"""
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
