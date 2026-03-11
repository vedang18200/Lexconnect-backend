"""Consultation routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.api.schemas.consultation import ConsultationCreate, ConsultationResponse, ConsultationUpdate
from app.core.security import get_current_user_id
from app.services.consultation_service import ConsultationService

router = APIRouter()

@router.post("/consultations", response_model=ConsultationResponse)
def create_consultation(
    consultation: ConsultationCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new consultation"""
    return ConsultationService.create_consultation(db, consultation)

@router.get("/consultations/{consultation_id}", response_model=ConsultationResponse)
def get_consultation(consultation_id: int, db: Session = Depends(get_db)):
    """Get consultation by ID"""
    return ConsultationService.get_consultation_by_id(db, consultation_id)

@router.put("/consultations/{consultation_id}", response_model=ConsultationResponse)
def update_consultation(
    consultation_id: int,
    consultation_update: ConsultationUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update consultation"""
    return ConsultationService.update_consultation(db, consultation_id, consultation_update)

@router.get("/users/{user_id}/consultations", response_model=list[ConsultationResponse])
def get_user_consultations(
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all consultations for a user"""
    return ConsultationService.get_user_consultations(db, user_id, skip, limit)

@router.get("/lawyers/{lawyer_id}/consultations", response_model=list[ConsultationResponse])
def get_lawyer_consultations(
    lawyer_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all consultations for a lawyer"""
    return ConsultationService.get_lawyer_consultations(db, lawyer_id, skip, limit)

@router.get("/consultations", response_model=list[ConsultationResponse])
def get_consultations(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get all consultations"""
    return ConsultationService.get_all_consultations(db, skip, limit)
