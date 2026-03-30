"""
Pydantic schemas for chat functionality.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.chat import MessageType


class MessageBase(BaseModel):
    """Base schema for messages."""
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    pass


class SystemMessageCreate(BaseModel):
    """Schema for creating a system message (admin/AI only)."""
    content: str = Field(..., min_length=1, max_length=5000, description="System message content")
    message_type: MessageType = Field(default=MessageType.SYSTEM)


class MessageResponse(MessageBase):
    """Schema for message response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    conversation_id: int
    sender_id: int
    message_type: MessageType
    is_read: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class ConversationBase(BaseModel):
    """Base schema for conversations."""
    pass


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation (internal use)."""
    user_id_1: int
    user_id_2: int


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id_1: int
    user_id_2: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    is_active: bool
    
    # Optional: include last message preview
    last_message: Optional[MessageResponse] = None
    unread_count: Optional[int] = None


class ChatNotification(BaseModel):
    """Schema for real-time chat notifications via WebSocket."""
    type: str = Field(..., description="Notification type: 'new_message', 'message_read', 'match'")
    conversation_id: Optional[int] = None
    message: Optional[MessageResponse] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
