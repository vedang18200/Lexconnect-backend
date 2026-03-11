"""Lawyer routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.api.schemas.lawyer import LawyerCreate, LawyerResponse, LawyerUpdate
from app.core.security import get_current_user_id
from app.services.lawyer_service import LawyerService
from typing import Optional

router = APIRouter()

@router.post("/lawyers", response_model=LawyerResponse)
def create_lawyer(
    lawyer: LawyerCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create lawyer profile"""
    return LawyerService.create_lawyer(db, lawyer)

@router.get("/lawyers/{lawyer_id}", response_model=LawyerResponse)
def get_lawyer(lawyer_id: int, db: Session = Depends(get_db)):
    """Get lawyer by ID"""
    return LawyerService.get_lawyer_by_id(db, lawyer_id)

@router.get("/users/{user_id}/lawyer", response_model=LawyerResponse)
def get_user_lawyer(user_id: int, db: Session = Depends(get_db)):
    """Get lawyer profile by user ID"""
    return LawyerService.get_lawyer_by_user_id(db, user_id)

@router.put("/lawyers/{lawyer_id}", response_model=LawyerResponse)
def update_lawyer(
    lawyer_id: int,
    lawyer_update: LawyerUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update lawyer profile"""
    return LawyerService.update_lawyer(db, lawyer_id, lawyer_update)

@router.get("/lawyers", response_model=list[LawyerResponse])
def get_lawyers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get all lawyers"""
    return LawyerService.get_all_lawyers(db, skip, limit)

@router.get("/lawyers/verified/list", response_model=list[LawyerResponse])
def get_verified_lawyers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get verified lawyers"""
    return LawyerService.get_verified_lawyers(db, skip, limit)


# === LAWYER DISCOVERY & SEARCH ENDPOINTS ===

@router.get("/lawyers/search", response_model=dict)
def search_lawyers(
    query: Optional[str] = Query(None),
    specialization: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    max_fee: Optional[float] = Query(None),
    verified_only: bool = Query(True),
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Search lawyers with filters"""
    return LawyerService.search_lawyers(
        db,
        query=query,
        specialization=specialization,
        location=location,
        min_rating=min_rating,
        max_fee=max_fee,
        verified_only=verified_only,
        skip=skip,
        limit=limit
    )


@router.get("/lawyers/specialization/{specialization}", response_model=dict)
def get_lawyers_by_specialization(
    specialization: str,
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Get lawyers by specialization"""
    return LawyerService.get_lawyers_by_specialization(db, specialization, skip, limit)


@router.get("/lawyers/location/{location}", response_model=dict)
def get_lawyers_by_location(
    location: str,
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Get lawyers by location"""
    return LawyerService.get_lawyers_by_location(db, location, skip, limit)


@router.get("/lawyers/top-rated", response_model=list[LawyerResponse])
def get_top_rated_lawyers(
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Get top-rated lawyers"""
    return LawyerService.get_top_rated_lawyers(db, limit)


@router.get("/lawyers/{lawyer_id}/details", response_model=dict)
def get_lawyer_details(
    lawyer_id: int,
    db: Session = Depends(get_db)
):
    """Get lawyer profile with detailed information including reviews"""
    return LawyerService.get_lawyers_with_details(db, lawyer_id)
