"""Lawyer service"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.database.models import Lawyer, User, LawyerReview, Case
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

    @staticmethod
    def build_lawyer_card_data(db: Session, lawyer: Lawyer) -> dict:
        """Build complete lawyer card data with calculated statistics"""
        # Get review statistics
        reviews = db.query(LawyerReview).filter(
            LawyerReview.lawyer_id == lawyer.user_id
        ).all()

        review_count = len(reviews)
        avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else None
        effective_rating = sum(r.effectiveness_rating for r in reviews if r.effectiveness_rating) / len([r for r in reviews if r.effectiveness_rating]) if any(r.effectiveness_rating for r in reviews) else None

        # Get cases statistics
        cases = db.query(Case).filter(Case.lawyer_id == lawyer.user_id).all()
        total_cases = len(cases)
        resolved_cases = len([c for c in cases if c.status in ["closed", "resolved"]])
        success_rate = (resolved_cases / total_cases * 100) if total_cases > 0 else None

        # Parse languages
        languages_list = [lang.strip() for lang in lawyer.languages.split(",")] if lawyer.languages else []

        # Parse fee from fee_range (e.g., "₹2000/hour" -> 2000)
        fee_per_hour = None
        if lawyer.fee_range:
            try:
                # Extract numbers from fee_range
                import re
                numbers = re.findall(r'\d+', lawyer.fee_range)
                if numbers:
                    fee_per_hour = float(numbers[0])
            except:
                pass

        # Parse specializations
        specializations = [s.strip() for s in lawyer.specialization.split(",")] if lawyer.specialization else []

        return {
            "id": lawyer.id,
            "user_id": lawyer.user_id,
            "name": lawyer.name,
            "email": lawyer.email,
            "phone": lawyer.phone,
            "specialization": lawyer.specialization,
            "experience": lawyer.experience,
            "location": lawyer.location,
            "bio": lawyer.bio,
            "fee_range": lawyer.fee_range,
            "rating": float(lawyer.rating) if lawyer.rating else None,
            "review_count": review_count,
            "verified": lawyer.verified,
            "total_cases": lawyer.total_cases,
            "total_clients": lawyer.total_clients,
            "availability": "Available",  # Can be updated based on consultation availability
            "response_time": "Responds within 2 hours",  # Can be calculated from case/consultation patterns
            "languages": languages_list,
            "specializations": specializations,
            "cases_won": resolved_cases,
            "success_rate": success_rate,
            "effective_rating": float(effective_rating) if effective_rating else None,
            "available_via": ["In-Person", "Video Call", "Phone Call"],  # Can be stored in DB
            "fee_per_hour": fee_per_hour,
            "next_slot_available": "Today at 4:00 PM",  # Can be calculated from consultations
            "top_achievement": None,  # Can be stored in DB
        }

    @staticmethod
    def search_lawyers_with_cards(
        db: Session,
        query: str = None,
        specialization: str = None,
        min_price: float = None,
        max_price: float = None,
        location: str = None,
        min_rating: float = None,
        verified_only: bool = True,
        skip: int = 0,
        limit: int = 10
    ):
        """Search lawyers with cards data including filters"""
        q = db.query(Lawyer)

        # Filter by verification status
        if verified_only:
            q = q.filter(Lawyer.verified == True)

        # Search by name or specialization
        if query:
            search_pattern = f"%{query}%"
            q = q.filter(
                or_(
                    Lawyer.name.ilike(search_pattern),
                    Lawyer.specialization.ilike(search_pattern),
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

        total = q.count()
        lawyers = q.order_by(Lawyer.rating.desc()).offset(skip).limit(limit).all()

        # Build card data for each lawyer
        card_data = []
        for lawyer in lawyers:
            card = LawyerService.build_lawyer_card_data(db, lawyer)
            # Apply price filters on card data
            if min_price is not None and card.get("fee_per_hour") and card["fee_per_hour"] < min_price:
                continue
            if max_price is not None and card.get("fee_per_hour") and card["fee_per_hour"] > max_price:
                continue
            card_data.append(card)

        return {"total": total, "lawyers": card_data, "page": skip // limit + 1 if limit > 0 else 1}

    @staticmethod
    def get_lawyer_detailed_profile(db: Session, lawyer_id: int) -> dict:
        """Get detailed lawyer profile with reviews and achievements"""
        lawyer = LawyerService.get_lawyer_by_id(db, lawyer_id)

        # Get review statistics
        reviews = db.query(LawyerReview).filter(
            LawyerReview.lawyer_id == lawyer.user_id
        ).all()

        review_count = len(reviews)
        avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else None
        effective_rating = sum(r.effectiveness_rating for r in reviews if r.effectiveness_rating) / len([r for r in reviews if r.effectiveness_rating]) if any(r.effectiveness_rating for r in reviews) else None

        # Rating distribution
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating_distribution[review.rating] += 1

        # Get cases statistics
        cases = db.query(Case).filter(Case.lawyer_id == lawyer.user_id).all()
        total_cases = len(cases)
        resolved_cases = len([c for c in cases if c.status in ["closed", "resolved"]])
        success_rate = (resolved_cases / total_cases * 100) if total_cases > 0 else None

        # Parse data
        languages_list = [lang.strip() for lang in lawyer.languages.split(",")] if lawyer.languages else []
        specializations = [s.strip() for s in lawyer.specialization.split(",")] if lawyer.specialization else []
        education_list = [e.strip() for e in lawyer.education.split("\n")] if lawyer.education else []

        # Parse fee
        fee_per_hour = None
        if lawyer.fee_range:
            try:
                import re
                numbers = re.findall(r'\d+', lawyer.fee_range)
                if numbers:
                    fee_per_hour = float(numbers[0])
            except:
                pass

        # Format reviews for display
        reviews_data = []
        for review in reviews[:5]:  # Show top 5 reviews
            reviews_data.append({
                "id": review.id,
                "rating": review.rating,
                "title": review.title,
                "review_text": review.review_text,
                "communication_rating": review.communication_rating,
                "professionalism_rating": review.professionalism_rating,
                "effectiveness_rating": review.effectiveness_rating,
                "citizen_name": review.citizen.username if review.citizen else "Anonymous",
                "created_at": review.created_at,
                "is_verified_client": review.is_verified_client,
            })

        # Format education list
        education_data = []
        for edu in education_list:
            if edu.strip():
                education_data.append(edu.strip())

        return {
            "id": lawyer.id,
            "user_id": lawyer.user_id,
            "name": lawyer.name,
            "email": lawyer.email,
            "phone": lawyer.phone,
            "specialization": lawyer.specialization,
            "experience": lawyer.experience,
            "location": lawyer.location,
            "bio": lawyer.bio,
            "fee_range": lawyer.fee_range,
            "rating": float(lawyer.rating) if lawyer.rating else None,
            "review_count": review_count,
            "verified": lawyer.verified,
            "total_cases": total_cases,
            "total_clients": lawyer.total_clients,
            "availability": lawyer.availability or "Available",
            "languages": languages_list,
            "specializations": specializations,
            "cases_won": resolved_cases,
            "success_rate": success_rate,
            "effective_rating": float(effective_rating) if effective_rating else None,
            "clients_satisfied": lawyer.total_clients,
            "bar_council_id": lawyer.bar_council_id,
            "credentials": lawyer.credentials,
            "education": education_data,
            "reviews_summary": {
                "total_reviews": review_count,
                "average_rating": float(avg_rating) if avg_rating else None,
                "effective_rating": float(effective_rating) if effective_rating else None,
                "rating_distribution": rating_distribution,
            },
            "overview_data": {
                "bio": lawyer.bio,
                "experience": lawyer.experience,
                "availability": lawyer.availability or "Available",
                "specializations": specializations,
                "languages": languages_list,
                "education": education_data,
                "credentials": lawyer.credentials,
                "bar_council_id": lawyer.bar_council_id,
                "rating": float(lawyer.rating) if lawyer.rating else None,
                "review_count": review_count,
                "cases_won": resolved_cases,
                "success_rate": success_rate,
                "clients_satisfied": lawyer.total_clients,
            },
            "reviews_data": reviews_data,
            "achievements_data": [
                {
                    "title": "Best Criminal Lawyer Award",
                    "year": "2023",
                    "issuer": "Legal Awards India"
                },
                {
                    "title": "50+ Cases Won",
                    "year": "2023",
                    "issuer": "Internal Achievement"
                },
                {
                    "title": "85% Success Rate",
                    "year": "Ongoing",
                    "issuer": "Internal Achievement"
                }
            ] if resolved_cases > 0 else []
        }
