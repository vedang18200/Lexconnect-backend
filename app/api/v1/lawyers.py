"""Lawyer routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.api.schemas.lawyer import LawyerCreate, LawyerResponse, LawyerUpdate, LawyerCardResponse
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

@router.get("/find-lawyers", response_model=dict)
def find_lawyers(
    query: Optional[str] = Query(None, description="Search by name or specialization"),
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    min_price: Optional[float] = Query(None, description="Minimum fee per hour"),
    max_price: Optional[float] = Query(None, description="Maximum fee per hour"),
    location: Optional[str] = Query(None, description="Filter by location"),
    min_rating: Optional[float] = Query(None, description="Minimum rating"),
    verified_only: bool = Query(True, description="Show only verified lawyers"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Find lawyers with full card data including ratings, reviews, cases won, success rate, etc.

    Query Parameters:
    - query: Search term (name or specialization)
    - specialization: Filter by specialization (e.g., "Criminal Law", "Consumer Rights")
    - min_price: Minimum consultation fee per hour
    - max_price: Maximum consultation fee per hour
    - location: Filter by location
    - min_rating: Minimum rating (0-5)
    - verified_only: Show only verified lawyers (default: true)
    - skip: Number of results to skip (pagination)
    - limit: Number of results to return (default: 10, max: 100)

    Returns:
    - total: Total number of lawyers matching criteria
    - lawyers: List of lawyer cards with full details
    - page: Current page number
    """
    return LawyerService.search_lawyers_with_cards(
        db,
        query=query,
        specialization=specialization,
        min_price=min_price,
        max_price=max_price,
        location=location,
        min_rating=min_rating,
        verified_only=verified_only,
        skip=skip,
        limit=limit
    )

@router.get("/lawyers/{lawyer_id}/card", response_model=dict)
def get_lawyer_card(lawyer_id: int, db: Session = Depends(get_db)):
    """Get lawyer card data with full statistics"""
    lawyer = LawyerService.get_lawyer_by_id(db, lawyer_id)
    return LawyerService.build_lawyer_card_data(db, lawyer)

@router.get("/lawyers/{lawyer_id}/profile", response_model=dict)
def get_lawyer_profile_detailed(lawyer_id: int, db: Session = Depends(get_db)):
    """
    Get detailed lawyer profile with all information

    This endpoint returns comprehensive lawyer information for the 'View Profile' page including:
    - Basic information (name, email, phone, location, bio)
    - Professional details (experience, specializations, languages)
    - Credentials and education
    - Statistics (cases won, success rate, clients satisfied)
    - Reviews summary and recent reviews
    - Achievements

    Can be used for different tabs:
    - Overview: bio, specializations, education, credentials, stats
    - Reviews: reviews_data
    - Achievements: achievements_data
    - Contact: email, phone
    """
    return LawyerService.get_lawyer_detailed_profile(db, lawyer_id)


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
