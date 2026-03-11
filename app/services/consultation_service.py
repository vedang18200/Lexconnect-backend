"""Consultation service"""
from sqlalchemy.orm import Session
from app.database.models import Consultation, User
from app.api.schemas.consultation import ConsultationCreate, ConsultationUpdate
from fastapi import HTTPException, status

class ConsultationService:
    """Consultation business logic"""

    @staticmethod
    def create_consultation(db: Session, consultation: ConsultationCreate) -> Consultation:
        """Create a new consultation"""
        user = db.query(User).filter(User.id == consultation.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        lawyer = db.query(User).filter(User.id == consultation.lawyer_id).first()
        if not lawyer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lawyer not found"
            )

        db_consultation = Consultation(**consultation.model_dump())
        db.add(db_consultation)
        db.commit()
        db.refresh(db_consultation)
        return db_consultation

    @staticmethod
    def get_consultation_by_id(db: Session, consultation_id: int) -> Consultation:
        """Get consultation by ID"""
        db_consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
        if not db_consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        return db_consultation

    @staticmethod
    def update_consultation(db: Session, consultation_id: int, consultation_update: ConsultationUpdate) -> Consultation:
        """Update consultation"""
        db_consultation = ConsultationService.get_consultation_by_id(db, consultation_id)

        update_data = consultation_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_consultation, field, value)

        db.commit()
        db.refresh(db_consultation)
        return db_consultation

    @staticmethod
    def get_user_consultations(db: Session, user_id: int, skip: int = 0, limit: int = 10):
        """Get all consultations for a user"""
        return db.query(Consultation).filter(Consultation.user_id == user_id).offset(skip).limit(limit).all()

    @staticmethod
    def get_lawyer_consultations(db: Session, lawyer_id: int, skip: int = 0, limit: int = 10):
        """Get all consultations for a lawyer"""
        return db.query(Consultation).filter(Consultation.lawyer_id == lawyer_id).offset(skip).limit(limit).all()

    @staticmethod
    def get_all_consultations(db: Session, skip: int = 0, limit: int = 10):
        """Get all consultations"""
        return db.query(Consultation).offset(skip).limit(limit).all()
