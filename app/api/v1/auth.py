"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.api.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest
from app.api.schemas.user import UserCreate, UserResponse
from app.core.security import (
    create_access_token,
    create_refresh_token,
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


def _create_login_response(user) -> dict:
    """Create a standard token response payload."""
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_type": user.user_type,
    }


def _login_with_role(credentials: LoginRequest, db: Session, role: str) -> dict:
    """Authenticate a user and enforce the expected role."""
    user = UserService.authenticate_user(db, credentials.username, credentials.password)
    if user.user_type != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This account is '{user.user_type}'. Please use the correct portal.",
        )
    return _create_login_response(user)

@router.post("/auth/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login for citizen portal (backward compatible endpoint)."""
    return _login_with_role(credentials, db, "citizen")


@router.post("/auth/login/citizen", response_model=TokenResponse)
def login_citizen(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint for citizen portal."""
    return _login_with_role(credentials, db, "citizen")


@router.post("/auth/login/lawyer", response_model=TokenResponse)
def login_lawyer(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint for lawyer portal."""
    return _login_with_role(credentials, db, "lawyer")


@router.post("/auth/login/social-worker", response_model=TokenResponse)
def login_social_worker(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint for social worker portal."""
    return _login_with_role(credentials, db, "social_worker")

@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token"""
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user = UserService.get_user_by_id(db, int(user_id))

        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user.id,
            "user_type": user.user_type,
        }
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
