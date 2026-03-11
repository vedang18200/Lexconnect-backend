"""Messaging service"""
from sqlalchemy.orm import Session
from app.database.models import DirectMessage, ChatMessage, User
from app.api.schemas.message import DirectMessageCreate, ChatMessageCreate
from fastapi import HTTPException, status
from datetime import datetime, timezone

class MessagingService:
    """Messaging business logic"""

    @staticmethod
    def send_direct_message(db: Session, sender_id: int, message: DirectMessageCreate) -> DirectMessage:
        """Send a direct message"""
        receiver = db.query(User).filter(User.id == message.receiver_id).first()
        if not receiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receiver not found"
            )

        db_message = DirectMessage(
            sender_id=sender_id,
            receiver_id=message.receiver_id,
            message=message.message
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    def get_direct_messages(db: Session, user_id: int, other_user_id: int, skip: int = 0, limit: int = 10):
        """Get direct messages between two users"""
        return db.query(DirectMessage).filter(
            ((DirectMessage.sender_id == user_id) & (DirectMessage.receiver_id == other_user_id)) |
            ((DirectMessage.sender_id == other_user_id) & (DirectMessage.receiver_id == user_id))
        ).offset(skip).limit(limit).all()

    @staticmethod
    def mark_message_read(db: Session, message_id: int) -> DirectMessage:
        """Mark a message as read"""
        db_message = db.query(DirectMessage).filter(DirectMessage.id == message_id).first()
        if not db_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        db_message.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    def create_chat_message(db: Session, user_id: int, message: ChatMessageCreate) -> ChatMessage:
        """Create a chat message"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        db_message = ChatMessage(
            user_id=user_id,
            message=message.message,
            language=message.language
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    def get_user_chat_messages(db: Session, user_id: int, skip: int = 0, limit: int = 10):
        """Get all chat messages for a user"""
        return db.query(ChatMessage).filter(ChatMessage.user_id == user_id).offset(skip).limit(limit).all()
