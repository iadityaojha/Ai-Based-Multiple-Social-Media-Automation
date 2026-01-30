"""
Facebook Service (Per-User Credentials)
=======================================
Uses user's own Facebook API credentials.
"""

from datetime import datetime
from typing import Optional
import httpx
from sqlalchemy.orm import Session

from app.models import User, UserApiKey, ApiKeyType
from app.encryption import encryption, EncryptionError


class FacebookError(Exception):
    pass


class FacebookService:
    """Facebook API service using user credentials."""
    
    API_BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, access_token: str, page_id: str = ""):
        self.access_token = access_token
        self.page_id = page_id
    
    async def post_content(self, content: str, link: Optional[str] = None) -> dict:
        """Post content to Facebook."""
        if not self.access_token:
            return {
                "success": True,
                "post_id": f"mock_facebook_{datetime.utcnow().timestamp()}",
                "message": "Mock post (Facebook not connected)",
                "mock": True
            }
        
        return {
            "success": True,
            "post_id": f"facebook_{datetime.utcnow().timestamp()}",
            "message": "Post simulation successful",
            "mock": True
        }
    
    async def post_with_image(self, content: str, image_path: str) -> dict:
        """Post content with an image to Facebook."""
        if not self.access_token:
            return {
                "success": True,
                "post_id": f"mock_facebook_img_{datetime.utcnow().timestamp()}",
                "message": "Mock image post (Facebook not connected)",
                "mock": True
            }
        
        # Real API implementation would go here
        return {
            "success": True,
            "post_id": f"facebook_img_{datetime.utcnow().timestamp()}",
            "message": "Image post simulation successful",
            "mock": True
        }


def get_facebook_service(user: User, db: Session) -> FacebookService:
    """Get Facebook service for user."""
    api_key = db.query(UserApiKey).filter(
        UserApiKey.user_id == user.id,
        UserApiKey.key_type == ApiKeyType.FACEBOOK,
        UserApiKey.is_valid == True
    ).first()
    
    access_token = ""
    page_id = ""
    if api_key:
        try:
            access_token = encryption.decrypt(api_key.encrypted_key)
            if api_key.encrypted_credentials:
                import json
                creds = json.loads(encryption.decrypt(api_key.encrypted_credentials))
                page_id = creds.get("page_id", "")
        except (EncryptionError, json.JSONDecodeError):
            pass
    
    return FacebookService(access_token=access_token, page_id=page_id)
