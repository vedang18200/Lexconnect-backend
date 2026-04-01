"""User service"""
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database.models import User, Lawyer
from app.api.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException, status

class UserService:
    """User business logic"""

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create a new user"""
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            password=hashed_password,
            user_type=user.user_type,
            phone=user.phone,
            location=user.location,
            language=user.language,
        )
        db.add(db_user)

        # Ensure we have user ID available before creating linked profile rows.
        db.flush()

        # Auto-create base lawyer profile when a lawyer user registers.
        if user.user_type == "lawyer":
            db_lawyer = Lawyer(
                user_id=db_user.id,
                name=user.username,
                email=user.email,
                phone=user.phone,
                location=user.location,
            )
            db.add(db_lawyer)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return db_user

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_username_or_email(db: Session, identifier: str) -> User:
        """Get user by username or email."""
        return db.query(User).filter(
            or_(User.username == identifier, User.email == identifier)
        ).first()

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> User:
        """Authenticate user by username or email."""
        user = UserService.get_user_by_username_or_email(db, username)
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        return user

    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User:
        """Update user"""
        db_user = UserService.get_user_by_id(db, user_id)

        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 10):
        """Get all users"""
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def get_lawyers(db: Session, skip: int = 0, limit: int = 10):
        """Get all lawyers"""
        return db.query(User).filter(User.user_type == "lawyer").offset(skip).limit(limit).all()
