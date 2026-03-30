"""
Chat API endpoints for managing conversations and messages.
Supports text messages, system messages (for future AI agent), and read status.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    SystemMessageCreate,
)
from app.models.chat import Conversation, Message

router = APIRouter()


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all conversations for the current user."""
    # Find conversations where user is either participant
    query = (
        select(Conversation)
        .where(or_(Conversation.user_id_1 == current_user.id, Conversation.user_id_2 == current_user.id))
        .where(Conversation.is_active == True)
        .order_by(desc(Conversation.last_message_at))
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific conversation by ID."""
    query = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(
            or_(
                Conversation.user_id_1 == current_user.id,
                Conversation.user_id_2 == current_user.id,
            )
        )
    )
    
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or you don't have access",
        )
    
    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get messages for a specific conversation."""
    # Verify user has access to conversation
    conv_query = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(
            or_(
                Conversation.user_id_1 == current_user.id,
                Conversation.user_id_2 == current_user.id,
            )
        )
    )
    
    result = await db.execute(conv_query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or you don't have access",
        )
    
    # Get messages
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.deleted_at == None)
        .order_by(desc(Message.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # Mark messages as read
    unread_messages = [m for m in messages if not m.is_read and m.sender_id != current_user.id]
    if unread_messages:
        for message in unread_messages:
            message.is_read = True
        await db.commit()
    
    return list(reversed(messages))  # Return in chronological order


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message in a conversation."""
    # Verify user has access to conversation
    conv_query = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(
            or_(
                Conversation.user_id_1 == current_user.id,
                Conversation.user_id_2 == current_user.id,
            )
        )
    )
    
    result = await db.execute(conv_query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or you don't have access",
        )
    
    if not conversation.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This conversation is no longer active",
        )
    
    # Create message
    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=message_data.content,
        message_type="text",
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return message


@router.post("/conversations/{conversation_id}/system-messages", response_model=MessageResponse)
async def send_system_message(
    conversation_id: int,
    message_data: SystemMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a system message in a conversation.
    Reserved for future AI agent questions and system notifications.
    Currently only available to admin users.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can send system messages",
        )
    
    # Verify conversation exists
    conv_query = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(conv_query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    # Create system message
    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,  # Admin who sends it
        content=message_data.content,
        message_type="system",
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return message


@router.websocket("/ws/conversations/{conversation_id}")
async def websocket_conversation(
    websocket: WebSocket,
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    WebSocket endpoint for real-time chat.
    Supports sending and receiving messages in real-time.
    """
    # Verify user has access to conversation
    conv_query = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(
            or_(
                Conversation.user_id_1 == current_user.id,
                Conversation.user_id_2 == current_user.id,
            )
        )
    )
    
    result = await db.execute(conv_query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        await websocket.close(code=status.HTTP_404_NOT_FOUND)
        return
    
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_content = data.get("content")
            
            if not message_content:
                continue
            
            # Create message in database
            message = Message(
                conversation_id=conversation_id,
                sender_id=current_user.id,
                content=message_content,
                message_type="text",
            )
            
            db.add(message)
            await db.commit()
            await db.refresh(message)
            
            # Send message to all connected clients in this conversation
            # In production, you'd use a connection manager to broadcast to specific conversation
            await websocket.send_json({
                "id": message.id,
                "sender_id": message.sender_id,
                "content": message.content,
                "message_type": message.message_type,
                "created_at": message.created_at.isoformat(),
            })
            
    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Handle other errors
        await websocket.close()


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a message (only the sender can delete their own message)."""
    query = select(Message).where(Message.id == message_id)
    result = await db.execute(query)
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    if message.sender_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages",
        )
    
    message.deleted_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Message deleted successfully"}
