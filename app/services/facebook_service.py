"""
Facebook Service Module
=======================
Handles all Facebook-specific functionality including:
- OAuth authentication via Facebook Graph API (placeholder)
- Page posting via Graph API
- Content formatting for Facebook's audience

Documentation: https://developers.facebook.com/docs/graph-api/
"""

import httpx
from typing import Optional
from datetime import datetime

from app.config import settings


class FacebookError(Exception):
    """Custom exception for Facebook API errors."""
    pass


class FacebookService:
    """
    Service class for Facebook API interactions.
    
    Note: For posting to pages, you need:
    - A Facebook App with pages_manage_posts permission
    - A Page Access Token (not user token)
    
    In production, this would handle:
    1. OAuth 2.0 flow for app authorization
    2. Page token management
    3. Posts, links, photos, and videos
    4. Scheduled posts natively
    """
    
    # Facebook Graph API base URL
    API_BASE_URL = "https://graph.facebook.com/v18.0"
    OAUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        page_id: Optional[str] = None
    ):
        """
        Initialize the Facebook service.
        
        Args:
            access_token: Facebook Page Access Token
            page_id: Facebook Page ID to post to
        """
        self.access_token = access_token or settings.FACEBOOK_ACCESS_TOKEN
        self.page_id = page_id or settings.FACEBOOK_PAGE_ID
        self.app_id = settings.FACEBOOK_APP_ID
        self.app_secret = settings.FACEBOOK_APP_SECRET
    
    @property
    def is_configured(self) -> bool:
        """Check if Facebook credentials are properly configured."""
        return bool(self.access_token and self.page_id)
    
    def _get_params(self) -> dict:
        """Get default parameters for API requests."""
        return {"access_token": self.access_token}
    
    async def get_page_info(self) -> dict:
        """
        Get Facebook Page information.
        
        Returns:
            Dict containing page information
        """
        if not self.is_configured:
            raise FacebookError("Facebook credentials not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE_URL}/{self.page_id}",
                params={
                    **self._get_params(),
                    "fields": "name,fan_count,about,picture"
                }
            )
            
            if response.status_code != 200:
                raise FacebookError(f"Failed to get page info: {response.text}")
            
            return response.json()
    
    async def post_content(
        self,
        content: str,
        link: Optional[str] = None,
        scheduled_time: Optional[datetime] = None
    ) -> dict:
        """
        Post content to a Facebook Page.
        
        Args:
            content: The post message/text
            link: Optional URL to include as a link post
            scheduled_time: Optional time to schedule the post (must be 10min-6months in future)
        
        Returns:
            Dict containing post result:
                - success: Boolean indicating if post was successful
                - post_id: ID of the created post (if successful)
                - message: Status message
                - timestamp: When the post was created
        """
        if not self.is_configured:
            # Return mock success for development/testing
            return {
                "success": True,
                "post_id": f"mock_facebook_{datetime.utcnow().timestamp()}",
                "message": "Mock post created (Facebook not configured)",
                "timestamp": datetime.utcnow().isoformat(),
                "mock": True
            }
        
        # =========================================
        # Real Facebook API implementation
        # =========================================
        # Uncomment and use when you have real credentials
        
        # try:
        #     params = {
        #         **self._get_params(),
        #         "message": content
        #     }
        #     
        #     # Add link if provided
        #     if link:
        #         params["link"] = link
        #     
        #     # Add scheduled time if provided
        #     if scheduled_time:
        #         # Facebook requires Unix timestamp
        #         params["published"] = False
        #         params["scheduled_publish_time"] = int(scheduled_time.timestamp())
        #     
        #     async with httpx.AsyncClient() as client:
        #         response = await client.post(
        #             f"{self.API_BASE_URL}/{self.page_id}/feed",
        #             params=params
        #         )
        #         
        #         if response.status_code == 200:
        #             post_data = response.json()
        #             return {
        #                 "success": True,
        #                 "post_id": post_data.get("id"),
        #                 "message": "Post published successfully" if not scheduled_time else "Post scheduled successfully",
        #                 "timestamp": datetime.utcnow().isoformat(),
        #                 "scheduled": scheduled_time.isoformat() if scheduled_time else None,
        #                 "mock": False
        #             }
        #         else:
        #             raise FacebookError(f"Failed to post: {response.text}")
        #             
        # except httpx.RequestError as e:
        #     raise FacebookError(f"Network error: {str(e)}")
        
        # For now, simulate successful posting
        return {
            "success": True,
            "post_id": f"facebook_{datetime.utcnow().timestamp()}",
            "message": "Post simulation successful (replace with real API call)",
            "timestamp": datetime.utcnow().isoformat(),
            "mock": True
        }
    
    async def post_photo(
        self,
        content: str,
        photo_url: str
    ) -> dict:
        """
        Post a photo with caption to a Facebook Page.
        
        Args:
            content: The caption for the photo
            photo_url: Public URL of the photo to post
            
        Returns:
            Dict containing post result
        """
        if not self.is_configured:
            return {
                "success": True,
                "post_id": f"mock_facebook_photo_{datetime.utcnow().timestamp()}",
                "message": "Mock photo post created (Facebook not configured)",
                "timestamp": datetime.utcnow().isoformat(),
                "mock": True
            }
        
        # Real implementation would use /{page-id}/photos endpoint
        return {
            "success": True,
            "post_id": f"facebook_photo_{datetime.utcnow().timestamp()}",
            "message": "Photo post simulation successful",
            "timestamp": datetime.utcnow().isoformat(),
            "mock": True
        }
    
    def get_oauth_url(self, state: str, redirect_uri: str) -> str:
        """
        Generate the OAuth authorization URL.
        
        Args:
            state: Random state string for CSRF protection
            redirect_uri: URL to redirect after authorization
            
        Returns:
            URL to redirect user for Facebook authorization
        """
        scopes = "pages_manage_posts,pages_read_engagement"
        return (
            f"{self.OAUTH_URL}?"
            f"client_id={self.app_id}&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}&"
            f"scope={scopes}"
        )
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Same redirect URI used in authorization
            
        Returns:
            Dict containing access_token and expires_in
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE_URL}/oauth/access_token",
                params={
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "redirect_uri": redirect_uri,
                    "code": code
                }
            )
            
            if response.status_code != 200:
                raise FacebookError(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def get_page_access_token(self, user_access_token: str) -> dict:
        """
        Get Page Access Token from User Access Token.
        
        This is needed because you need a Page token to post to pages.
        
        Args:
            user_access_token: User's access token with pages_manage_posts permission
            
        Returns:
            Dict containing page access token
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE_URL}/me/accounts",
                params={"access_token": user_access_token}
            )
            
            if response.status_code != 200:
                raise FacebookError(f"Failed to get page token: {response.text}")
            
            pages = response.json().get("data", [])
            
            # Find the page we're looking for
            for page in pages:
                if page.get("id") == self.page_id:
                    return {
                        "page_access_token": page.get("access_token"),
                        "page_name": page.get("name")
                    }
            
            raise FacebookError(f"Page {self.page_id} not found in user's pages")


# Singleton instance for easy import
facebook_service = FacebookService()
