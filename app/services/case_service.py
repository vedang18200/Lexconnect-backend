"""Case service"""
from sqlalchemy.orm import Session
from app.database.models import Case, User
from app.api.schemas.case import CaseCreate, CaseUpdate
from fastapi import HTTPException, status

class CaseService:
    """Case business logic"""

    @staticmethod
    def create_case(db: Session, case: CaseCreate) -> Case:
        """Create a new case"""
        user = db.query(User).filter(User.id == case.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        db_case = Case(**case.model_dump())
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        return db_case

    @staticmethod
    def get_case_by_id(db: Session, case_id: int) -> Case:
        """Get case by ID"""
        db_case = db.query(Case).filter(Case.id == case_id).first()
        if not db_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
        return db_case

    @staticmethod
    def update_case(db: Session, case_id: int, case_update: CaseUpdate) -> Case:
        """Update case"""
        db_case = CaseService.get_case_by_id(db, case_id)

        update_data = case_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_case, field, value)

        db.commit()
        db.refresh(db_case)
        return db_case

    @staticmethod
    def get_user_cases(db: Session, user_id: int, skip: int = 0, limit: int = 10):
        """Get all cases for a user"""
        return db.query(Case).filter(Case.user_id == user_id).offset(skip).limit(limit).all()

    @staticmethod
    def get_lawyer_cases(db: Session, lawyer_id: int, skip: int = 0, limit: int = 10):
        """Get all cases for a lawyer"""
        return db.query(Case).filter(Case.lawyer_id == lawyer_id).offset(skip).limit(limit).all()

    @staticmethod
    def get_all_cases(db: Session, skip: int = 0, limit: int = 10):
        """Get all cases"""
        return db.query(Case).offset(skip).limit(limit).all()
