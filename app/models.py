"""
Database Models Module
======================
Defines SQLAlchemy ORM models for the application.

Tables:
- Topic: Stores input topics for content generation
- GeneratedPost: Stores generated content with scheduling info
- ErrorLog: Tracks posting failures for debugging

All timestamps are stored in UTC.
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, 
    ForeignKey, Enum, Boolean
)
from sqlalchemy.orm import relationship

from app.database import Base


# =========================================
# Enums for Type Safety
# =========================================
class Platform(str, PyEnum):
    """Supported social media platforms."""
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"


class PostStatus(str, PyEnum):
    """Status of a generated post."""
    DRAFT = "draft"           # Just generated, not yet approved
    PENDING = "pending"       # Approved and scheduled, waiting to post
    POSTED = "posted"         # Successfully posted
    FAILED = "failed"         # Failed to post after all retries


# =========================================
# Topic Model
# =========================================
class Topic(Base):
    """
    Represents an input topic for content generation.
    Each topic can have multiple posts (one per platform).
    """
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)  # Optional additional context
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship: One topic can have many posts
    posts = relationship("GeneratedPost", back_populates="topic", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name='{self.name[:50]}...')>"


# =========================================
# Generated Post Model
# =========================================
class GeneratedPost(Base):
    """
    Represents a piece of generated content for a specific platform.
    Tracks the full lifecycle: generation -> approval -> scheduling -> posting.
    """
    __tablename__ = "generated_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to the topic
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    
    # Platform this content is for
    platform = Column(Enum(Platform), nullable=False, index=True)
    
    # The actual generated content
    content = Column(Text, nullable=False)
    
    # Hashtags (stored as comma-separated string for simplicity)
    hashtags = Column(Text, nullable=True)
    
    # Post status tracking
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT, nullable=False, index=True)
    
    # Scheduling information
    scheduled_time = Column(DateTime, nullable=True, index=True)
    
    # Posting results
    posted_at = Column(DateTime, nullable=True)
    platform_post_id = Column(String(255), nullable=True)  # ID returned by the platform
    
    # Retry tracking
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    topic = relationship("Topic", back_populates="posts")
    error_logs = relationship("ErrorLog", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GeneratedPost(id={self.id}, platform={self.platform.value}, status={self.status.value})>"
    
    @property
    def is_scheduled(self) -> bool:
        """Check if the post is scheduled for future posting."""
        return self.status == PostStatus.PENDING and self.scheduled_time is not None
    
    @property
    def is_ready_to_post(self) -> bool:
        """Check if the post is ready to be posted now."""
        if self.status != PostStatus.PENDING:
            return False
        if self.scheduled_time is None:
            return True
        return datetime.utcnow() >= self.scheduled_time


# =========================================
# Error Log Model
# =========================================
class APIKey(Base):
    """
    Stores encrypted API keys for various services.
    Keys are encrypted before storage for security.
    """
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_type = Column(String(50), nullable=False, unique=True, index=True)  # openai, gemini, linkedin, etc.
    encrypted_key = Column(Text, nullable=False)  # The encrypted API key
    is_valid = Column(Boolean, default=True, nullable=False)  # Whether the key has been tested and is valid
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, key_type='{self.key_type}')>"
    
    @property
    def masked_key(self) -> str:
        """Return a masked version of the key for display."""
        # This is just a placeholder - actual masking happens when decrypting
        return "••••••••••••"


class ErrorLog(Base):
    """
    Tracks errors that occur during posting.
    Useful for debugging and monitoring failed posts.
    """
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to the post that failed
    post_id = Column(Integer, ForeignKey("generated_posts.id"), nullable=False, index=True)
    
    # Error details
    error_message = Column(Text, nullable=False)
    error_type = Column(String(255), nullable=True)  # Exception class name
    
    # Attempt number when this error occurred
    attempt_number = Column(Integer, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    post = relationship("GeneratedPost", back_populates="error_logs")
    
    def __repr__(self):
        return f"<ErrorLog(id={self.id}, post_id={self.post_id}, attempt={self.attempt_number})>"
