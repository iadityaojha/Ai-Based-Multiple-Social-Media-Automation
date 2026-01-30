"""
Authentication Module (Simplified - No Login Required)
=======================================================
Single-user mode for faster development and testing.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


def get_or_create_default_user(db: Session) -> User:
    """Get or create a default user for single-user mode."""
    user = db.query(User).filter(User.email == "default@local.app").first()
    
    if not user:
        user = User(
            email="default@local.app",
            hashed_password="not-used",
            full_name="Default User",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


def get_current_user(db: Session = Depends(get_db)) -> User:
    """
    Get the current user (always returns default user in single-user mode).
    No authentication required.
    """
    return get_or_create_default_user(db)


# Alias for compatibility
get_current_active_user = get_current_user
