"""
LLM Client Module
=================
Provider-agnostic abstraction for Large Language Model APIs.
Currently supports OpenAI, but designed to easily add other providers.

Each platform has specific prompt templates to generate appropriate content:
- LinkedIn: Professional, long-form thought leadership
- Instagram: Short, catchy caption with hooks and hashtags
- Facebook: Storytelling style with call-to-action
"""

from abc import ABC, abstractmethod
from typing import Optional
import openai

from app.config import settings
from app.models import Platform


# =========================================
# Platform-Specific Prompt Templates
# =========================================
PLATFORM_PROMPTS = {
    Platform.LINKEDIN: """You are an expert LinkedIn content creator specializing in AI education.

Create a professional, engaging LinkedIn post about the following topic:
Topic: {topic}

Requirements:
1. Write in a professional yet approachable tone
2. Start with a compelling hook to grab attention
3. Include 3-5 key insights or takeaways
4. Use appropriate spacing and formatting for readability
5. End with a thought-provoking question to encourage engagement
6. Keep it between 200-300 words
7. Do NOT include hashtags in the main content (they will be added separately)

Focus on providing genuine value to professionals interested in AI.""",

    Platform.INSTAGRAM: """You are an expert Instagram content creator specializing in AI education.

Create an engaging Instagram caption about the following topic:
Topic: {topic}

Requirements:
1. Start with a POWERFUL hook (emoji + attention-grabbing statement)
2. Keep the main message short and punchy (max 150 words)
3. Use line breaks for readability
4. Include a clear call-to-action (save, share, comment)
5. End with relevant hashtags (provide 15-20 hashtags)
6. Make it educational but fun and accessible

Format:
[Hook with emoji]

[Main content with line breaks]

[Call to action]

[Hashtags on new line]""",

    Platform.FACEBOOK: """You are an expert Facebook content creator specializing in AI education.

Create a compelling Facebook post about the following topic:
Topic: {topic}

Requirements:
1. Use a storytelling approach - start with a relatable scenario or question
2. Break down complex AI concepts into simple, digestible points
3. Include a personal touch or real-world example
4. Write in a conversational, friendly tone
5. End with a clear call-to-action (comment, share, learn more)
6. Keep it between 150-250 words
7. Make it shareable and discussion-worthy

Focus on making AI accessible and exciting for a general audience."""
}


# =========================================
# Base LLM Client (Abstract)
# =========================================
class BaseLLMClient(ABC):
    """
    Abstract base class for LLM providers.
    Implement this interface to add support for new LLM providers.
    """
    
    @abstractmethod
    def generate_content(
        self, 
        topic: str, 
        platform: Platform,
        additional_context: Optional[str] = None
    ) -> dict:
        """
        Generate platform-specific content for a given topic.
        
        Args:
            topic: The topic to generate content about
            platform: Target social media platform
            additional_context: Optional extra context for generation
            
        Returns:
            dict with keys:
                - content: The generated post content
                - hashtags: List of hashtags (if applicable)
                - metadata: Any additional metadata from the LLM
        """
        pass
    
    def _get_prompt(self, topic: str, platform: Platform, additional_context: Optional[str] = None) -> str:
        """Build the full prompt for content generation."""
        base_prompt = PLATFORM_PROMPTS[platform].format(topic=topic)
        
        if additional_context:
            base_prompt += f"\n\nAdditional Context:\n{additional_context}"
        
        return base_prompt


# =========================================
# OpenAI Client Implementation
# =========================================
class OpenAIClient(BaseLLMClient):
    """
    OpenAI API implementation of the LLM client.
    Uses the chat completions API for content generation.
    """
    
    def __init__(self):
        """Initialize the OpenAI client with API key from settings."""
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.MAX_CONTENT_TOKENS
    
    def generate_content(
        self, 
        topic: str, 
        platform: Platform,
        additional_context: Optional[str] = None
    ) -> dict:
        """
        Generate content using OpenAI's chat completions API.
        
        Args:
            topic: The topic to generate content about
            platform: Target social media platform
            additional_context: Optional extra context for generation
            
        Returns:
            dict with generated content, hashtags, and metadata
        """
        prompt = self._get_prompt(topic, platform, additional_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert social media content creator specializing in AI education. You create engaging, informative, and platform-appropriate content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            generated_text = response.choices[0].message.content.strip()
            
            # Extract hashtags if present (for Instagram)
            hashtags = self._extract_hashtags(generated_text, platform)
            
            # Clean content (remove hashtags from main content for cleaner storage)
            clean_content = self._clean_content(generated_text, platform)
            
            return {
                "content": clean_content,
                "hashtags": hashtags,
                "metadata": {
                    "model": self.model,
                    "tokens_used": response.usage.total_tokens if response.usage else None,
                    "finish_reason": response.choices[0].finish_reason
                }
            }
            
        except openai.APIError as e:
            raise LLMError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise LLMError(f"Unexpected error during content generation: {str(e)}")
    
    def _extract_hashtags(self, text: str, platform: Platform) -> list[str]:
        """Extract hashtags from generated text."""
        import re
        hashtags = re.findall(r'#\w+', text)
        return list(set(hashtags))  # Remove duplicates
    
    def _clean_content(self, text: str, platform: Platform) -> str:
        """Clean the generated content based on platform requirements."""
        # For now, just strip whitespace
        # Can be extended to remove hashtags from body text, etc.
        return text.strip()


# =========================================
# LLM Factory
# =========================================
class LLMError(Exception):
    """Custom exception for LLM-related errors."""
    pass


def get_llm_client() -> BaseLLMClient:
    """
    Factory function to get the appropriate LLM client based on settings.
    
    Returns:
        An instance of BaseLLMClient (currently OpenAI)
        
    Raises:
        ValueError if the configured provider is not supported
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured. Set OPENAI_API_KEY in .env")
        return OpenAIClient()
    
    # Add more providers here as needed:
    # elif provider == "anthropic":
    #     return AnthropicClient()
    # elif provider == "ollama":
    #     return OllamaClient()
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported: openai")


# =========================================
# Convenience Function
# =========================================
def generate_content_for_platforms(
    topic: str,
    platforms: list[Platform],
    additional_context: Optional[str] = None
) -> dict[Platform, dict]:
    """
    Generate content for multiple platforms at once.
    
    Args:
        topic: The topic to generate content about
        platforms: List of target platforms
        additional_context: Optional extra context
        
    Returns:
        Dict mapping platform to generated content
    """
    client = get_llm_client()
    results = {}
    
    for platform in platforms:
        try:
            results[platform] = client.generate_content(topic, platform, additional_context)
        except LLMError as e:
            results[platform] = {
                "content": None,
                "hashtags": [],
                "error": str(e),
                "metadata": {}
            }
    
    return results
