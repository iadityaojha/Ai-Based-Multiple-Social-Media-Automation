"""
Instagram Service Module
========================
Handles all Instagram-specific functionality including:
- OAuth authentication via Facebook Graph API (placeholder)
- Content posting via Instagram Graph API
- Media uploads and caption management

Instagram uses Facebook's Graph API for business accounts.
Documentation: https://developers.facebook.com/docs/instagram-api/
"""

import httpx
from typing import Optional
from datetime import datetime

from app.config import settings


class InstagramError(Exception):
    """Custom exception for Instagram API errors."""
    pass


class InstagramService:
    """
    Service class for Instagram API interactions.
    
    Note: Instagram API requires a Facebook Business account and
    an Instagram Business or Creator account linked to a Facebook Page.
    
    In production, this would handle:
    1. OAuth 2.0 flow via Facebook
    2. Media container creation for images/videos
    3. Caption and hashtag management
    4. Publishing to feed, stories, reels
    """
    
    # Instagram Graph API base URL
    API_BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        business_account_id: Optional[str] = None
    ):
        """
        Initialize the Instagram service.
        
        Args:
            access_token: Facebook Graph API access token
            business_account_id: Instagram Business Account ID
        """
        self.access_token = access_token or settings.FACEBOOK_ACCESS_TOKEN
        self.business_account_id = business_account_id or settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
    
    @property
    def is_configured(self) -> bool:
        """Check if Instagram credentials are properly configured."""
        return bool(self.access_token and self.business_account_id)
    
    def _get_params(self) -> dict:
        """Get default parameters for API requests."""
        return {"access_token": self.access_token}
    
    async def get_account_info(self) -> dict:
        """
        Get Instagram Business Account information.
        
        Returns:
            Dict containing account information
        """
        if not self.is_configured:
            raise InstagramError("Instagram credentials not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE_URL}/{self.business_account_id}",
                params={
                    **self._get_params(),
                    "fields": "username,profile_picture_url,followers_count,media_count"
                }
            )
            
            if response.status_code != 200:
                raise InstagramError(f"Failed to get account info: {response.text}")
            
            return response.json()
    
    async def post_content(
        self,
        content: str,
        image_url: Optional[str] = None,
        hashtags: Optional[list[str]] = None
    ) -> dict:
        """
        Post content to Instagram.
        
        Note: Instagram API requires an image for feed posts.
        For the MVP, this is a placeholder that simulates the posting process.
        
        Args:
            content: The caption text (including hashtags)
            image_url: Public URL of the image to post
            hashtags: Optional list of hashtags to append
        
        Returns:
            Dict containing post result:
                - success: Boolean indicating if post was successful
                - post_id: ID of the created post (if successful)
                - message: Status message
                - timestamp: When the post was created
        """
        # Combine content with hashtags if provided separately
        full_caption = content
        if hashtags:
            hashtag_text = " ".join(hashtags)
            if hashtag_text not in content:
                full_caption = f"{content}\n\n{hashtag_text}"
        
        if not self.is_configured:
            # Return mock success for development/testing
            return {
                "success": True,
                "post_id": f"mock_instagram_{datetime.utcnow().timestamp()}",
                "message": "Mock post created (Instagram not configured)",
                "caption": full_caption[:100] + "..." if len(full_caption) > 100 else full_caption,
                "timestamp": datetime.utcnow().isoformat(),
                "mock": True
            }
        
        # =========================================
        # Real Instagram API implementation
        # =========================================
        # Instagram requires a two-step process:
        # 1. Create a media container
        # 2. Publish the container
        
        # Uncomment and use when you have real credentials
        
        # try:
        #     if not image_url:
        #         raise InstagramError("Instagram requires an image URL for feed posts")
        #     
        #     # Step 1: Create media container
        #     async with httpx.AsyncClient() as client:
        #         container_response = await client.post(
        #             f"{self.API_BASE_URL}/{self.business_account_id}/media",
        #             params={
        #                 **self._get_params(),
        #                 "image_url": image_url,
        #                 "caption": full_caption
        #             }
        #         )
        #         
        #         if container_response.status_code != 200:
        #             raise InstagramError(f"Failed to create container: {container_response.text}")
        #         
        #         container_id = container_response.json().get("id")
        #         
        #         # Step 2: Publish the container
        #         publish_response = await client.post(
        #             f"{self.API_BASE_URL}/{self.business_account_id}/media_publish",
        #             params={
        #                 **self._get_params(),
        #                 "creation_id": container_id
        #             }
        #         )
        #         
        #         if publish_response.status_code != 200:
        #             raise InstagramError(f"Failed to publish: {publish_response.text}")
        #         
        #         return {
        #             "success": True,
        #             "post_id": publish_response.json().get("id"),
        #             "message": "Post published successfully",
        #             "timestamp": datetime.utcnow().isoformat(),
        #             "mock": False
        #         }
        #         
        # except httpx.RequestError as e:
        #     raise InstagramError(f"Network error: {str(e)}")
        
        # For now, simulate successful posting
        return {
            "success": True,
            "post_id": f"instagram_{datetime.utcnow().timestamp()}",
            "message": "Post simulation successful (replace with real API call)",
            "caption": full_caption[:100] + "..." if len(full_caption) > 100 else full_caption,
            "timestamp": datetime.utcnow().isoformat(),
            "mock": True,
            "note": "Instagram API requires an image URL for real posts"
        }
    
    async def create_story(
        self,
        image_url: str,
        sticker_text: Optional[str] = None
    ) -> dict:
        """
        Create an Instagram Story (placeholder for future implementation).
        
        Args:
            image_url: Public URL of the image for the story
            sticker_text: Optional text for a sticker overlay
            
        Returns:
            Dict containing story creation result
        """
        # This would use the Instagram Stories API
        # Stories have different requirements than feed posts
        return {
            "success": False,
            "message": "Stories not yet implemented",
            "note": "This feature requires additional API setup"
        }


# Singleton instance for easy import
instagram_service = InstagramService()
