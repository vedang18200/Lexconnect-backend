"""Case routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.api.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.core.security import get_current_user_id
from app.services.case_service import CaseService

router = APIRouter()

@router.post("/cases", response_model=CaseResponse)
def create_case(
    case: CaseCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new case"""
    return CaseService.create_case(db, case)

@router.get("/cases/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    """Get case by ID"""
    return CaseService.get_case_by_id(db, case_id)

@router.put("/cases/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: int,
    case_update: CaseUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update case"""
    return CaseService.update_case(db, case_id, case_update)

@router.get("/users/{user_id}/cases", response_model=list[CaseResponse])
def get_user_cases(
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all cases for a user"""
    return CaseService.get_user_cases(db, user_id, skip, limit)

@router.get("/lawyers/{lawyer_id}/cases", response_model=list[CaseResponse])
def get_lawyer_cases(
    lawyer_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all cases assigned to a lawyer"""
    return CaseService.get_lawyer_cases(db, lawyer_id, skip, limit)

@router.get("/cases", response_model=list[CaseResponse])
def get_cases(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get all cases"""
    return CaseService.get_all_cases(db, skip, limit)
