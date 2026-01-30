"""
Init file for services package
"""

from app.services.llm_client import get_llm_client, generate_content_for_platforms, LLMError
from app.services.linkedin_service import linkedin_service, LinkedInError
from app.services.instagram_service import instagram_service, InstagramError
from app.services.facebook_service import facebook_service, FacebookError

__all__ = [
    "get_llm_client",
    "generate_content_for_platforms",
    "LLMError",
    "linkedin_service",
    "LinkedInError",
    "instagram_service",
    "InstagramError",
    "facebook_service",
    "FacebookError",
]
