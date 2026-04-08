"""User routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.api.schemas.user import (
    UserResponse,
    UserUpdate,
    UserListResponse,
    ChangePasswordRequest,
    MessageResponse,
)
from app.core.security import get_current_user_id
from app.services.user_service import UserService

router = APIRouter()

@router.get("/users/me", response_model=UserResponse)
def get_current_user(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get current user profile"""
    return UserService.get_user_by_id(db, user_id)

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    return UserService.get_user_by_id(db, user_id)

@router.put("/users/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update current user"""
    return UserService.update_user(db, user_id, user_update)

@router.get("/users", response_model=list[UserListResponse])
def get_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get all users"""
    return UserService.get_all_users(db, skip, limit)

@router.get("/users/list/lawyers", response_model=list[UserListResponse])
def get_lawyers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get all lawyers"""
    return UserService.get_lawyers(db, skip, limit)


@router.post("/users/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Change current user's password."""
    UserService.change_password(db, user_id, payload.current_password, payload.new_password)
    return {"success": True, "message": "Password updated successfully"}
