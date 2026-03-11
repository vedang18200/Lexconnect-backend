"""Lawyer service"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.database.models import Lawyer, User, LawyerReview
from app.api.schemas.lawyer import LawyerCreate, LawyerUpdate
from fastapi import HTTPException, status
from decimal import Decimal


class LawyerService:
    """Lawyer business logic"""

    @staticmethod
    def create_lawyer(db: Session, lawyer: LawyerCreate) -> Lawyer:
        """Create lawyer profile"""
        user = db.query(User).filter(User.id == lawyer.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        db_lawyer = db.query(Lawyer).filter(Lawyer.user_id == lawyer.user_id).first()
        if db_lawyer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lawyer profile already exists"
            )

        db_lawyer = Lawyer(**lawyer.model_dump())
        db.add(db_lawyer)
        db.commit()
        db.refresh(db_lawyer)
        return db_lawyer

    @staticmethod
    def get_lawyer_by_id(db: Session, lawyer_id: int) -> Lawyer:
        """Get lawyer by ID"""
        db_lawyer = db.query(Lawyer).filter(Lawyer.id == lawyer_id).first()
        if not db_lawyer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lawyer not found"
            )
        return db_lawyer

    @staticmethod
    def get_lawyer_by_user_id(db: Session, user_id: int) -> Lawyer:
        """Get lawyer by user ID"""
        db_lawyer = db.query(Lawyer).filter(Lawyer.user_id == user_id).first()
        if not db_lawyer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lawyer profile not found"
            )
        return db_lawyer

    @staticmethod
    def update_lawyer(db: Session, lawyer_id: int, lawyer_update: LawyerUpdate) -> Lawyer:
        """Update lawyer profile"""
        db_lawyer = LawyerService.get_lawyer_by_id(db, lawyer_id)

        update_data = lawyer_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_lawyer, field, value)

        db.commit()
        db.refresh(db_lawyer)
        return db_lawyer

    @staticmethod
    def get_all_lawyers(db: Session, skip: int = 0, limit: int = 10):
        """Get all lawyers"""
        return db.query(Lawyer).offset(skip).limit(limit).all()

    @staticmethod
    def get_verified_lawyers(db: Session, skip: int = 0, limit: int = 10):
        """Get verified lawyers"""
        return db.query(Lawyer).filter(Lawyer.verified == True).offset(skip).limit(limit).all()

    @staticmethod
    def search_lawyers(
        db: Session,
        query: str = None,
        specialization: str = None,
        location: str = None,
        min_rating: float = None,
        max_fee: float = None,
        verified_only: bool = True,
        skip: int = 0,
        limit: int = 10
    ):
        """Search lawyers with filters"""
        q = db.query(Lawyer)

        # Filter by verification status
        if verified_only:
            q = q.filter(Lawyer.verified == True)

        # Search by name, specialization, or location
        if query:
            search_pattern = f"%{query}%"
            q = q.filter(
                or_(
                    Lawyer.name.ilike(search_pattern),
                    Lawyer.specialization.ilike(search_pattern),
                    Lawyer.bio.ilike(search_pattern)
                )
            )

        # Filter by specialization
        if specialization:
            specialization_pattern = f"%{specialization}%"
            q = q.filter(Lawyer.specialization.ilike(specialization_pattern))

        # Filter by location
        if location:
            location_pattern = f"%{location}%"
            q = q.filter(Lawyer.location.ilike(location_pattern))

        # Filter by minimum rating
        if min_rating is not None:
            q = q.filter(Lawyer.rating >= Decimal(str(min_rating)))

        # Filter by maximum fee
        if max_fee is not None:
            # This is a simple string-based filter, in production would need proper parsing
            q = q.filter(~Lawyer.fee_range.ilike(f"%{max_fee}%"))

        total = q.count()
        lawyers = q.order_by(Lawyer.rating.desc()).offset(skip).limit(limit).all()

        return {"total": total, "lawyers": lawyers}

    @staticmethod
    def get_lawyers_by_specialization(
        db: Session, specialization: str, skip: int = 0, limit: int = 10
    ):
        """Get lawyers by specialization"""
        specialization_pattern = f"%{specialization}%"
        total = db.query(Lawyer).filter(
            and_(
                Lawyer.specialization.ilike(specialization_pattern),
                Lawyer.verified == True
            )
        ).count()
        lawyers = db.query(Lawyer).filter(
            and_(
                Lawyer.specialization.ilike(specialization_pattern),
                Lawyer.verified == True
            )
        ).order_by(Lawyer.rating.desc()).offset(skip).limit(limit).all()

        return {"total": total, "lawyers": lawyers}

    @staticmethod
    def get_lawyers_by_location(
        db: Session, location: str, skip: int = 0, limit: int = 10
    ):
        """Get lawyers by location"""
        location_pattern = f"%{location}%"
        total = db.query(Lawyer).filter(
            and_(
                Lawyer.location.ilike(location_pattern),
                Lawyer.verified == True
            )
        ).count()
        lawyers = db.query(Lawyer).filter(
            and_(
                Lawyer.location.ilike(location_pattern),
                Lawyer.verified == True
            )
        ).order_by(Lawyer.rating.desc()).offset(skip).limit(limit).all()

        return {"total": total, "lawyers": lawyers}

    @staticmethod
    def get_top_rated_lawyers(db: Session, limit: int = 10):
        """Get top rated lawyers"""
        return db.query(Lawyer).filter(Lawyer.verified == True).order_by(
            Lawyer.rating.desc()
        ).limit(limit).all()

    @staticmethod
    def get_lawyers_with_details(db: Session, lawyer_id: int) -> dict:
        """Get lawyer profile with detailed information including reviews"""
        lawyer = db.query(Lawyer).filter(Lawyer.id == lawyer_id).first()
        if not lawyer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lawyer not found"
            )

        # Get review statistics
        reviews = db.query(LawyerReview).filter(
            LawyerReview.lawyer_id == lawyer.user_id
        ).all()

        rating_summary = {
            "total_reviews": len(reviews),
            "average_rating": sum(r.rating for r in reviews) / len(reviews) if reviews else 0,
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        }

        for review in reviews:
            rating_summary["rating_distribution"][review.rating] += 1

        return {
            "lawyer": lawyer,
            "reviews": reviews,
            "rating_summary": rating_summary
        }
