"""
Database Models for Multi-User SaaS
====================================
All models with user isolation and encrypted API key storage.
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, 
    ForeignKey, Enum, Boolean, Float
)
from sqlalchemy.orm import relationship

from app.database import Base


# =========================================
# Enums
# =========================================
class Platform(str, PyEnum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"


class PostStatus(str, PyEnum):
    DRAFT = "draft"
    PENDING = "pending"
    POSTED = "posted"
    FAILED = "failed"


class ToneStyle(str, PyEnum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    EDUCATIONAL = "educational"
    INSPIRATIONAL = "inspirational"


class ApiKeyType(str, PyEnum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"


# =========================================
# User Model
# =========================================
class User(Base):
    """User account for the SaaS platform."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships - each user has their own data
    api_keys = relationship("UserApiKey", back_populates="user", cascade="all, delete-orphan")
    topics = relationship("Topic", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("GeneratedPost", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


# =========================================
# User API Keys Model (Encrypted Storage)
# =========================================
class UserApiKey(Base):
    """
    Stores encrypted API keys for each user.
    Keys are encrypted before storage and decrypted on retrieval.
    """
    __tablename__ = "user_api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Key type (openai, linkedin, etc.)
    key_type = Column(Enum(ApiKeyType), nullable=False, index=True)
    
    # Encrypted API key value
    encrypted_key = Column(Text, nullable=False)
    
    # Additional credentials (encrypted JSON for complex auth like OAuth)
    encrypted_credentials = Column(Text, nullable=True)
    
    # Key metadata
    key_name = Column(String(255), nullable=True)  # User-friendly name
    is_valid = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<UserApiKey(id={self.id}, type={self.key_type.value}, user_id={self.user_id})>"


# =========================================
# Topic Model (Per-User)
# =========================================
class Topic(Base):
    """Topic for content generation, owned by a user."""
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    tone = Column(Enum(ToneStyle), default=ToneStyle.PROFESSIONAL, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="topics")
    posts = relationship("GeneratedPost", back_populates="topic", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name='{self.name[:30]}...')>"


# =========================================
# Generated Post Model (Per-User)
# =========================================
class GeneratedPost(Base):
    """Generated content for a platform, owned by a user."""
    __tablename__ = "generated_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    
    # Content
    platform = Column(Enum(Platform), nullable=False, index=True)
    content = Column(Text, nullable=False)
    hashtags = Column(Text, nullable=True)
    tone = Column(Enum(ToneStyle), default=ToneStyle.PROFESSIONAL, nullable=False)
    
    # Status
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT, nullable=False, index=True)
    
    # Scheduling
    scheduled_time = Column(DateTime, nullable=True, index=True)
    posted_at = Column(DateTime, nullable=True)
    platform_post_id = Column(String(255), nullable=True)
    
    # Retry tracking
    retry_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="posts")
    topic = relationship("Topic", back_populates="posts")
    error_logs = relationship("ErrorLog", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GeneratedPost(id={self.id}, platform={self.platform.value})>"


# =========================================
# Error Log Model
# =========================================
class ErrorLog(Base):
    """Error logs for failed posting attempts."""
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("generated_posts.id"), nullable=False, index=True)
    
    error_message = Column(Text, nullable=False)
    error_type = Column(String(255), nullable=True)
    attempt_number = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    post = relationship("GeneratedPost", back_populates="error_logs")
    
    def __repr__(self):
        return f"<ErrorLog(id={self.id}, post_id={self.post_id})>"
