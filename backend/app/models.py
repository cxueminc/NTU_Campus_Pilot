# Add this to your existing database.py or create a new models.py

from sqlalchemy import Column, Integer, String, Boolean, Text, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'core'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    preferences = Column(JSONB, default={})

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = {'schema': 'core'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('core.users.id'), nullable=False)
    title = Column(String, nullable=True)  # Auto-generated from first message
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = {'schema': 'core'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('core.chat_sessions.id'), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB, default={})  # For storing extra info like facility mentions
    mentioned_facilities = Column(JSONB, default=[])  # Array of facility IDs