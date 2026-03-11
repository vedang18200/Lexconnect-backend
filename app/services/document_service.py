"""Document upload service"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timezone
from app.database.models import DocumentUpload, Case
from app.api.schemas.citizen import DocumentUploadCreate, DocumentUploadResponse


class DocumentService:
    """Service for managing document uploads"""

    @staticmethod
    def upload_document(
        db: Session,
        user_id: int,
        document: DocumentUploadCreate,
        file_url: str,
        file_size: int,
        mime_type: str,
        uploaded_by_id: int,
    ) -> DocumentUpload:
        """Upload a new document"""
        # Verify case exists if case_id is provided
        if document.case_id:
            case = db.query(Case).filter(Case.id == document.case_id).first()
            if not case:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Case not found"
                )
            if case.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to upload documents for this case"
                )

        db_document = DocumentUpload(
            user_id=user_id,
            case_id=document.case_id,
            document_type=document.document_type,
            file_name=document.file_name,
            file_url=file_url,
            file_size=file_size,
            mime_type=mime_type,
            description=document.description,
            uploaded_by=uploaded_by_id,
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document

    @staticmethod
    def get_document(db: Session, document_id: int, user_id: int) -> DocumentUpload:
        """Get a specific document"""
        document = db.query(DocumentUpload).filter(DocumentUpload.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Check if user has access to this document
        if document.user_id != user_id and document.uploaded_by != user_id:
            # Check if it's a case document and user is the lawyer
            if document.case_id:
                case = db.query(Case).filter(Case.id == document.case_id).first()
                if case and case.lawyer_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You do not have permission to access this document"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this document"
                )

        return document

    @staticmethod
    def get_documents_by_case(db: Session, case_id: int, user_id: int, skip: int = 0, limit: int = 10):
        """Get all documents for a case"""
        # Verify user has access to the case
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        if case.user_id != user_id and case.lawyer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access documents for this case"
            )

        total = db.query(DocumentUpload).filter(DocumentUpload.case_id == case_id).count()
        documents = (
            db.query(DocumentUpload)
            .filter(DocumentUpload.case_id == case_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {"total": total, "documents": documents}

    @staticmethod
    def get_documents_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 10):
        """Get all documents uploaded by a user"""
        total = db.query(DocumentUpload).filter(DocumentUpload.user_id == user_id).count()
        documents = (
            db.query(DocumentUpload)
            .filter(DocumentUpload.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {"total": total, "documents": documents}

    @staticmethod
    def delete_document(db: Session, document_id: int, user_id: int) -> None:
        """Delete a document"""
        document = db.query(DocumentUpload).filter(DocumentUpload.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        if document.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this document"
            )

        db.delete(document)
        db.commit()

    @staticmethod
    def verify_document(db: Session, document_id: int) -> DocumentUpload:
        """Verify/approve a document (admin only)"""
        document = db.query(DocumentUpload).filter(DocumentUpload.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        document.is_verified = True
        document.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(document)
        return document
