"""Messaging and chat routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.api.schemas.message import DirectMessageCreate, DirectMessageResponse, ChatMessageCreate, ChatMessageResponse
from app.core.security import get_current_user_id, verify_token
from app.services.messaging_service import MessagingService
from app.services.chatbot_service import ChatbotService

router = APIRouter()

# Direct Messaging Routes
@router.post("/messages/direct", response_model=DirectMessageResponse)
def send_message(
    message: DirectMessageCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Send a direct message"""
    return MessagingService.send_direct_message(db, user_id, message)

@router.get("/messages/direct/{other_user_id}", response_model=list[DirectMessageResponse])
def get_messages(
    other_user_id: int,
    user_id: int = Depends(get_current_user_id),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get direct messages between two users"""
    return MessagingService.get_direct_messages(db, user_id, other_user_id, skip, limit)

@router.put("/messages/{message_id}/read")
def mark_message_read(
    message_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Mark a message as read"""
    return MessagingService.mark_message_read(db, message_id)


@router.get("/messages/conversations")
def get_conversations(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get list of active conversations for the user"""
    user_id = int(credentials.get("sub"))
    return MessagingService.get_conversations(db, user_id)

@router.get("/messages/conversation/{other_user_id}")
def get_conversation_with_user(
    other_user_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get or initiate a conversation with a specific user"""
    return MessagingService.get_conversation_with_user(db, user_id, other_user_id)

# Chat Routes
@router.post("/chat", response_model=ChatMessageResponse)
def create_chat_message(
    message: ChatMessageCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a chat message with AI chatbot"""
    db_message = MessagingService.create_chat_message(db, user_id, message)

    # Generate AI response
    response = ChatbotService.generate_response(message.message, message.language)
    db_message.response = response
    db.commit()
    db.refresh(db_message)

    return db_message

@router.get("/chat/history", response_model=list[ChatMessageResponse])
def get_chat_history(
    user_id: int = Depends(get_current_user_id),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get chat history for a user"""
    return MessagingService.get_user_chat_messages(db, user_id, skip, limit)
