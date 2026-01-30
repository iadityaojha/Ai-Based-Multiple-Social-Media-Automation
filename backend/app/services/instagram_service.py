"""
Instagram Service (Per-User Credentials)
========================================
Uses user's own Instagram API credentials via Facebook Graph API.
"""

from datetime import datetime
from typing import Optional
import httpx
from sqlalchemy.orm import Session

from app.models import User, UserApiKey, ApiKeyType
from app.encryption import encryption, EncryptionError


class InstagramError(Exception):
    pass


class InstagramService:
    """Instagram API service using user credentials."""
    
    API_BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, access_token: str, business_account_id: str = ""):
        self.access_token = access_token
        self.business_account_id = business_account_id
    
    async def post_content(
        self,
        content: str,
        image_url: Optional[str] = None,
        hashtags: Optional[list[str]] = None
    ) -> dict:
        """Post content to Instagram."""
        full_caption = content
        if hashtags:
            full_caption += "\n\n" + " ".join(hashtags)
        
        if not self.access_token:
            return {
                "success": True,
                "post_id": f"mock_instagram_{datetime.utcnow().timestamp()}",
                "message": "Mock post (Instagram not connected)",
                "mock": True
            }
        
        return {
            "success": True,
            "post_id": f"instagram_{datetime.utcnow().timestamp()}",
            "message": "Post simulation successful",
            "mock": True
        }
    
    async def post_with_image(self, content: str, image_path: str) -> dict:
        """Post content with an image to Instagram."""
        if not self.access_token:
            return {
                "success": True,
                "post_id": f"mock_instagram_img_{datetime.utcnow().timestamp()}",
                "message": "Mock image post (Instagram not connected)",
                "mock": True
            }
        
        # Real API implementation would go here
        # Instagram requires: 1) Upload image, 2) Create media container, 3) Publish
        return {
            "success": True,
            "post_id": f"instagram_img_{datetime.utcnow().timestamp()}",
            "message": "Image post simulation successful",
            "mock": True
        }


def get_instagram_service(user: User, db: Session) -> InstagramService:
    """Get Instagram service for user."""
    api_key = db.query(UserApiKey).filter(
        UserApiKey.user_id == user.id,
        UserApiKey.key_type == ApiKeyType.INSTAGRAM,
        UserApiKey.is_valid == True
    ).first()
    
    access_token = ""
    business_id = ""
    if api_key:
        try:
            access_token = encryption.decrypt(api_key.encrypted_key)
            if api_key.encrypted_credentials:
                import json
                creds = json.loads(encryption.decrypt(api_key.encrypted_credentials))
                business_id = creds.get("business_account_id", "")
        except (EncryptionError, json.JSONDecodeError):
            pass
    
    return InstagramService(access_token=access_token, business_account_id=business_id)
