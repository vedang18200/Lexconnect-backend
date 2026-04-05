"""Case routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.api.schemas.case import CaseCreate, CaseResponse, CaseUpdate, CaseStatsResponse, CaseDetailedListResponse
from app.core.security import get_current_user_id
from app.services.case_service import CaseService
from typing import Optional

router = APIRouter()

@router.post("/cases", response_model=CaseResponse)
def create_case(
    case: CaseCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new case"""
    return CaseService.create_case(db, case)


# === MY CASES PORTAL ENDPOINTS - MUST COME BEFORE {case_id} ROUTES ===

@router.get("/cases/my-cases/statistics", response_model=CaseStatsResponse)
def get_my_cases_statistics(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get case statistics for logged-in citizen

    Returns:
    - total_cases: Total number of cases
    - active_cases: Cases with status open, in_progress, or active
    - pending_cases: Cases with status pending
    - closed_cases: Cases with status closed
    - resolved_cases: Cases with status resolved
    """
    stats = CaseService.get_case_statistics(db, user_id)
    return stats


@router.get("/cases/my-cases", response_model=CaseDetailedListResponse)
def get_my_cases(
    status_filter: Optional[str] = Query(None, description="Filter by status (open, in_progress, active, pending, closed, resolved)"),
    priority_filter: Optional[str] = Query(None, description="Filter by priority (low, medium, high)"),
    search: Optional[str] = Query(None, description="Search by title, case number, or category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get detailed list of cases for My Cases portal with filtering and search

    Query Parameters:
    - status_filter: Filter by case status
    - priority_filter: Filter by priority (low, medium, high)
    - search: Search in title, case number, category, or description
    - skip: Pagination offset
    - limit: Number of results per page

    Returns:
    - total: Total number of cases matching criteria
    - cases: Array of detailed case objects
    - page: Current page number

    Each case includes:
    - id, title, description, category, status, priority, case_number
    - lawyer: { id, user_id, name, email, phone, specialization }
    - documents_count, updates_count
    - legal_fees_amount, legal_fees_paid
    - created_at, updated_at
    """
    return CaseService.get_my_cases_detailed(
        db,
        user_id=user_id,
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_query=search,
        skip=skip,
        limit=limit
    )


# === GENERIC CASE ROUTES ===

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
def get_all_cases(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get all cases"""
    return CaseService.get_all_cases(db, skip, limit)
