"""
LinkedIn Service (Per-User Credentials)
=======================================
Uses user's own LinkedIn API credentials.
"""

from datetime import datetime
from typing import Optional
import httpx
from sqlalchemy.orm import Session

from app.models import User, UserApiKey, ApiKeyType
from app.encryption import encryption, EncryptionError


class LinkedInError(Exception):
    pass


class LinkedInService:
    """LinkedIn API service using user credentials."""
    
    API_BASE_URL = "https://api.linkedin.com/v2"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
    
    async def post_content(self, content: str) -> dict:
        """Post content to LinkedIn."""
        if not self.access_token:
            return {
                "success": True,
                "post_id": f"mock_linkedin_{datetime.utcnow().timestamp()}",
                "message": "Mock post (LinkedIn not connected)",
                "mock": True
            }
        
        # Real API implementation would go here
        return {
            "success": True,
            "post_id": f"linkedin_{datetime.utcnow().timestamp()}",
            "message": "Post simulation successful",
            "mock": True
        }
    
    async def post_with_image(self, content: str, image_path: str) -> dict:
        """Post content with an image to LinkedIn."""
        if not self.access_token:
            return {
                "success": True,
                "post_id": f"mock_linkedin_img_{datetime.utcnow().timestamp()}",
                "message": "Mock image post (LinkedIn not connected)",
                "mock": True
            }
        
        # Real API implementation for image posting would go here
        # This involves: 1) Register upload, 2) Upload image, 3) Create post with image
        return {
            "success": True,
            "post_id": f"linkedin_img_{datetime.utcnow().timestamp()}",
            "message": "Image post simulation successful",
            "mock": True
        }


def get_linkedin_service(user: User, db: Session) -> LinkedInService:
    """Get LinkedIn service for user."""
    api_key = db.query(UserApiKey).filter(
        UserApiKey.user_id == user.id,
        UserApiKey.key_type == ApiKeyType.LINKEDIN,
        UserApiKey.is_valid == True
    ).first()
    
    access_token = ""
    if api_key:
        try:
            access_token = encryption.decrypt(api_key.encrypted_key)
        except EncryptionError:
            pass
    
    return LinkedInService(access_token=access_token)
