"""
Authentication Routes (Simplified)
===================================
Single-user mode - no login required.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/me")
async def get_profile(user = Depends(get_current_user)):
    """Get the current user's profile."""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name or "Default User",
        "is_active": user.is_active
    }


@router.get("/status")
async def auth_status():
    """Check authentication status - always authenticated in single-user mode."""
    return {
        "authenticated": True,
        "mode": "single-user"
    }
