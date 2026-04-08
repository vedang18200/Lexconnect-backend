"""Messaging service"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
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
        ).order_by(DirectMessage.sent_at.asc()).offset(skip).limit(limit).all()

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
    def mark_conversation_read(db: Session, user_id: int, other_user_id: int) -> int:
        """Mark all unread incoming messages in a conversation as read."""
        unread_messages = db.query(DirectMessage).filter(
            DirectMessage.sender_id == other_user_id,
            DirectMessage.receiver_id == user_id,
            DirectMessage.read_at.is_(None),
        ).all()

        now = datetime.now(timezone.utc)
        for message in unread_messages:
            message.read_at = now

        db.commit()
        return len(unread_messages)

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

    @staticmethod
    def get_conversations(db: Session, user_id: int):
        """Get all unique conversations for a user with latest message preview."""
        from app.database.models import Lawyer, Case

        # Get all messages for this user
        messages = (
            db.query(DirectMessage)
            .filter(
                or_(
                    DirectMessage.sender_id == user_id,
                    DirectMessage.receiver_id == user_id,
                )
            )
            .order_by(DirectMessage.sent_at.desc())
            .all()
        )

        latest_by_counterpart: dict[int, DirectMessage] = {}
        counterparts_from_messages: set[int] = set()

        for msg in messages:
            counterpart_id = msg.receiver_id if msg.sender_id == user_id else msg.sender_id
            if counterpart_id not in latest_by_counterpart:
                latest_by_counterpart[counterpart_id] = msg
                counterparts_from_messages.add(counterpart_id)

        # Get all lawyers from cases assigned to this user
        cases = db.query(Case).filter(
            (Case.user_id == user_id) & (Case.lawyer_id.isnot(None))
        ).all()

        counterparts_from_cases: set[int] = {case.lawyer_id for case in cases}

        # Combine both sets - lawyers from messages and from cases
        all_counterpart_ids = counterparts_from_messages | counterparts_from_cases

        if not all_counterpart_ids:
            return []

        counterparts = (
            db.query(User, Lawyer)
            .outerjoin(Lawyer, Lawyer.user_id == User.id)
            .filter(User.id.in_(all_counterpart_ids))
            .all()
        )

        counterpart_map = {
            user.id: {
                "name": lawyer.name if lawyer and lawyer.name else user.username,
                "specialization": lawyer.specialization if lawyer else None,
                "user_type": user.user_type,
                "location": user.location,
            }
            for user, lawyer in counterparts
        }

        unread_counts = {
            counterpart_id: db.query(DirectMessage).filter(
                DirectMessage.sender_id == counterpart_id,
                DirectMessage.receiver_id == user_id,
                DirectMessage.read_at.is_(None),
            ).count()
            for counterpart_id in all_counterpart_ids
        }

        case_context_map = {}
        for counterpart_id in all_counterpart_ids:
            case = db.query(Case).filter(
                Case.user_id == user_id,
                Case.lawyer_id == counterpart_id,
            ).order_by(Case.updated_at.desc().nullslast(), Case.created_at.desc()).first()
            case_context_map[counterpart_id] = {
                "case_id": case.id if case else None,
                "case_title": case.title if case else None,
            }

        # Sort: conversations with messages first (by last message time), then case lawyers (alphabetically)
        result = []

        # Add conversations with messages (sorted by last message time)
        for counterpart_id in sorted(counterparts_from_messages, key=lambda x: latest_by_counterpart[x].sent_at, reverse=True):
            result.append({
                "id": counterpart_id,
                "name": counterpart_map.get(counterpart_id, {}).get("name"),
                "specialization": counterpart_map.get(counterpart_id, {}).get("specialization"),
                "user_type": counterpart_map.get(counterpart_id, {}).get("user_type"),
                "location": counterpart_map.get(counterpart_id, {}).get("location"),
                "case_id": case_context_map.get(counterpart_id, {}).get("case_id"),
                "case_title": case_context_map.get(counterpart_id, {}).get("case_title"),
                "last_message": latest_by_counterpart[counterpart_id].message,
                "last_message_at": latest_by_counterpart[counterpart_id].sent_at,
                "unread_count": unread_counts.get(counterpart_id, 0),
                "is_online": False,
            })

        # Add case lawyers without messages
        for counterpart_id in sorted(counterparts_from_cases - counterparts_from_messages, key=lambda x: counterpart_map.get(x, {}).get("name") or ""):
            result.append({
                "id": counterpart_id,
                "name": counterpart_map.get(counterpart_id, {}).get("name"),
                "specialization": counterpart_map.get(counterpart_id, {}).get("specialization"),
                "user_type": counterpart_map.get(counterpart_id, {}).get("user_type"),
                "location": counterpart_map.get(counterpart_id, {}).get("location"),
                "case_id": case_context_map.get(counterpart_id, {}).get("case_id"),
                "case_title": case_context_map.get(counterpart_id, {}).get("case_title"),
                "last_message": None,
                "last_message_at": None,
                "unread_count": unread_counts.get(counterpart_id, 0),
                "is_online": False,
            })

        return result

    @staticmethod
    def get_conversation_with_user(db: Session, user_id: int, other_user_id: int) -> dict:
        """Get or initiate a conversation with a specific user"""
        from app.database.models import Lawyer, Case

        # Verify the other user exists
        other_user = db.query(User).filter(User.id == other_user_id).first()
        if not other_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get lawyer details if available
        lawyer = db.query(Lawyer).filter(Lawyer.user_id == other_user_id).first()

        # Get existing messages (if any)
        existing_messages = db.query(DirectMessage).filter(
            ((DirectMessage.sender_id == user_id) & (DirectMessage.receiver_id == other_user_id)) |
            ((DirectMessage.sender_id == other_user_id) & (DirectMessage.receiver_id == user_id))
        ).order_by(DirectMessage.sent_at.desc()).all()

        # Get last message if exists
        last_message = existing_messages[0] if existing_messages else None

        unread_count = db.query(DirectMessage).filter(
            DirectMessage.sender_id == other_user_id,
            DirectMessage.receiver_id == user_id,
            DirectMessage.read_at.is_(None),
        ).count()

        case = db.query(Case).filter(
            Case.user_id == user_id,
            Case.lawyer_id == other_user_id,
        ).order_by(Case.updated_at.desc().nullslast(), Case.created_at.desc()).first()

        return {
            "id": other_user_id,
            "name": lawyer.name if lawyer and lawyer.name else other_user.username,
            "email": other_user.email,
            "specialization": lawyer.specialization if lawyer else None,
            "experience": lawyer.experience if lawyer else None,
            "rating": float(lawyer.rating) if lawyer and lawyer.rating else None,
            "user_type": other_user.user_type,
            "location": other_user.location,
            "case_id": case.id if case else None,
            "case_title": case.title if case else None,
            "last_message": last_message.message if last_message else None,
            "last_message_at": last_message.sent_at if last_message else None,
            "unread_count": unread_count,
            "is_online": False,
        }
