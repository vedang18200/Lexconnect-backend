"""Lawyer review and rating service"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException, status
from datetime import datetime, timezone
from decimal import Decimal
from app.database.models import LawyerReview, User, Lawyer, Consultation, Case
from app.api.schemas.citizen import LawyerReviewCreate, LawyerReviewResponse


class ReviewService:
    """Service for managing lawyer reviews and ratings"""

    @staticmethod
    def create_review(db: Session, citizen_id: int, review: LawyerReviewCreate) -> LawyerReview:
        """Create a new review for a lawyer"""
        # Verify lawyer exists
        lawyer_user = db.query(User).filter(
            and_(User.id == review.lawyer_id, User.user_type == "lawyer")
        ).first()
        if not lawyer_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lawyer not found"
            )

        # Verify citizen is not reviewing their own profile
        if citizen_id == review.lawyer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot review yourself"
            )

        # Check if review already exists
        existing_review = db.query(LawyerReview).filter(
            and_(
                LawyerReview.lawyer_id == review.lawyer_id,
                LawyerReview.citizen_id == citizen_id,
                LawyerReview.case_id == review.case_id
            )
        ).first()
        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reviewed this lawyer for this case"
            )

        # If case_id provided, verify citizen has a consultation with this lawyer
        if review.case_id:
            case = db.query(Case).filter(
                and_(Case.id == review.case_id, Case.user_id == citizen_id)
            ).first()
            if not case:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Case not found or you do not have access to it"
                )

        db_review = LawyerReview(
            lawyer_id=review.lawyer_id,
            citizen_id=citizen_id,
            case_id=review.case_id,
            rating=review.rating,
            title=review.title,
            review_text=review.review_text,
            communication_rating=review.communication_rating,
            professionalism_rating=review.professionalism_rating,
            effectiveness_rating=review.effectiveness_rating,
            is_verified_client=True,
        )
        db.add(db_review)
        db.commit()
        db.refresh(db_review)

        # Update lawyer's average rating
        ReviewService._update_lawyer_rating(db, review.lawyer_id)

        return db_review

    @staticmethod
    def get_review(db: Session, review_id: int) -> LawyerReview:
        """Get a specific review"""
        review = db.query(LawyerReview).filter(LawyerReview.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        return review

    @staticmethod
    def get_lawyer_reviews(
        db: Session, lawyer_id: int, skip: int = 0, limit: int = 10
    ):
        """Get all reviews for a lawyer"""
        total = db.query(LawyerReview).filter(LawyerReview.lawyer_id == lawyer_id).count()
        reviews = (
            db.query(LawyerReview)
            .filter(LawyerReview.lawyer_id == lawyer_id)
            .order_by(LawyerReview.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {"total": total, "reviews": reviews}

    @staticmethod
    def get_citizen_reviews(db: Session, citizen_id: int, skip: int = 0, limit: int = 10):
        """Get all reviews written by a citizen"""
        total = db.query(LawyerReview).filter(LawyerReview.citizen_id == citizen_id).count()
        reviews = (
            db.query(LawyerReview)
            .filter(LawyerReview.citizen_id == citizen_id)
            .order_by(LawyerReview.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {"total": total, "reviews": reviews}

    @staticmethod
    def update_review(
        db: Session, review_id: int, citizen_id: int, review_update: dict
    ) -> LawyerReview:
        """Update a review"""
        review = db.query(LawyerReview).filter(LawyerReview.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        if review.citizen_id != citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own reviews"
            )

        for field, value in review_update.items():
            if value is not None and hasattr(review, field):
                setattr(review, field, value)

        db.commit()
        db.refresh(review)

        # Update lawyer's average rating
        ReviewService._update_lawyer_rating(db, review.lawyer_id)

        return review

    @staticmethod
    def delete_review(db: Session, review_id: int, citizen_id: int) -> None:
        """Delete a review"""
        review = db.query(LawyerReview).filter(LawyerReview.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        if review.citizen_id != citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own reviews"
            )

        lawyer_id = review.lawyer_id
        db.delete(review)
        db.commit()

        # Update lawyer's average rating
        ReviewService._update_lawyer_rating(db, lawyer_id)

    @staticmethod
    def mark_helpful(db: Session, review_id: int) -> LawyerReview:
        """Mark a review as helpful"""
        review = db.query(LawyerReview).filter(LawyerReview.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        review.helpful_count += 1
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def mark_unhelpful(db: Session, review_id: int) -> LawyerReview:
        """Mark a review as unhelpful"""
        review = db.query(LawyerReview).filter(LawyerReview.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        review.unhelpful_count += 1
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def _update_lawyer_rating(db: Session, lawyer_id: int) -> None:
        """Update lawyer's average rating in Lawyer profile"""
        avg_rating = db.query(func.avg(LawyerReview.rating)).filter(
            LawyerReview.lawyer_id == lawyer_id
        ).scalar()

        lawyer = db.query(Lawyer).filter(Lawyer.user_id == lawyer_id).first()
        if lawyer:
            lawyer.rating = Decimal(str(avg_rating)) if avg_rating else None
            db.commit()

    @staticmethod
    def get_lawyer_rating_summary(db: Session, lawyer_id: int) -> dict:
        """Get detailed rating summary for a lawyer"""
        reviews = db.query(LawyerReview).filter(LawyerReview.lawyer_id == lawyer_id).all()

        if not reviews:
            return {
                "total_reviews": 0,
                "average_rating": 0,
                "communication_rating": 0,
                "professionalism_rating": 0,
                "effectiveness_rating": 0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

        # Calculate averages
        communication_ratings = [r.communication_rating for r in reviews if r.communication_rating]
        professionalism_ratings = [r.professionalism_rating for r in reviews if r.professionalism_rating]
        effectiveness_ratings = [r.effectiveness_rating for r in reviews if r.effectiveness_rating]

        # Calculate rating distribution
        rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating_dist[review.rating] += 1

        return {
            "total_reviews": len(reviews),
            "average_rating": sum(r.rating for r in reviews) / len(reviews),
            "communication_rating": sum(communication_ratings) / len(communication_ratings) if communication_ratings else 0,
            "professionalism_rating": sum(professionalism_ratings) / len(professionalism_ratings) if professionalism_ratings else 0,
            "effectiveness_rating": sum(effectiveness_ratings) / len(effectiveness_ratings) if effectiveness_ratings else 0,
            "rating_distribution": rating_dist
        }
