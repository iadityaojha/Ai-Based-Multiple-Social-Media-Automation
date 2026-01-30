"""
LLM Client Service (Per-User Keys)
==================================
Provider-agnostic LLM abstraction using user's own API keys.
Supports: OpenAI, Google Gemini
"""

from abc import ABC, abstractmethod
from typing import Optional
import openai
import google.generativeai as genai
from sqlalchemy.orm import Session

from app.models import User, UserApiKey, ApiKeyType, Platform, ToneStyle
from app.encryption import encryption, EncryptionError


# =========================================
# Tone-Specific Instructions
# =========================================
TONE_INSTRUCTIONS = {
    ToneStyle.PROFESSIONAL: "Write in a professional, authoritative tone suitable for business audiences.",
    ToneStyle.CASUAL: "Write in a friendly, conversational tone that feels approachable.",
    ToneStyle.EDUCATIONAL: "Write in an informative, teaching style that explains concepts clearly.",
    ToneStyle.INSPIRATIONAL: "Write in an uplifting, motivational tone that inspires action.",
}


# =========================================
# Platform-Specific Prompts
# =========================================
PLATFORM_PROMPTS = {
    Platform.LINKEDIN: """Create a professional LinkedIn post about: {topic}

Requirements:
- Start with a compelling hook
- Include 3-5 key insights or takeaways
- Use appropriate spacing for readability
- End with a thought-provoking question
- Keep it 200-300 words
- Don't include hashtags (added separately)

{tone_instruction}""",

    Platform.INSTAGRAM: """Create an Instagram caption about: {topic}

Requirements:
- Start with a POWERFUL hook (emoji + attention-grabbing statement)
- Keep main message short and punchy (max 150 words)
- Use line breaks for readability
- Include a clear call-to-action
- End with 15-20 relevant hashtags

{tone_instruction}""",

    Platform.FACEBOOK: """Create a Facebook post about: {topic}

Requirements:
- Use a storytelling approach
- Make complex concepts simple and digestible
- Include a personal touch or real-world example
- Write in a conversational tone
- End with a clear call-to-action
- Keep it 150-250 words

{tone_instruction}"""
}


class LLMError(Exception):
    """Custom exception for LLM errors."""
    pass


class BaseLLMClient(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate_content(
        self,
        topic: str,
        platform: Platform,
        tone: ToneStyle = ToneStyle.PROFESSIONAL,
        additional_context: Optional[str] = None
    ) -> dict:
        pass
    
    def _extract_hashtags(self, text: str) -> list[str]:
        import re
        return list(set(re.findall(r'#\w+', text)))


class OpenAIClient(BaseLLMClient):
    """OpenAI implementation using user's API key."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.7):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
    
    def generate_content(
        self,
        topic: str,
        platform: Platform,
        tone: ToneStyle = ToneStyle.PROFESSIONAL,
        additional_context: Optional[str] = None
    ) -> dict:
        """Generate platform-specific content."""
        
        tone_instruction = TONE_INSTRUCTIONS.get(tone, "")
        prompt = PLATFORM_PROMPTS[platform].format(
            topic=topic,
            tone_instruction=tone_instruction
        )
        
        if additional_context:
            prompt += f"\n\nAdditional context: {additional_context}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert social media content creator specializing in AI education."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            hashtags = self._extract_hashtags(content)
            
            return {
                "content": content,
                "hashtags": hashtags,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except openai.AuthenticationError:
            raise LLMError("Invalid OpenAI API key. Please check your key in Settings.")
        except openai.RateLimitError:
            raise LLMError("OpenAI rate limit exceeded. Please try again later.")
        except openai.APIError as e:
            raise LLMError(f"OpenAI API error: {str(e)}")


class GeminiClient(BaseLLMClient):
    """Google Gemini implementation using user's API key."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", temperature: float = 0.7):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.temperature = temperature
    
    def generate_content(
        self,
        topic: str,
        platform: Platform,
        tone: ToneStyle = ToneStyle.PROFESSIONAL,
        additional_context: Optional[str] = None
    ) -> dict:
        """Generate platform-specific content using Gemini."""
        
        tone_instruction = TONE_INSTRUCTIONS.get(tone, "")
        prompt = PLATFORM_PROMPTS[platform].format(
            topic=topic,
            tone_instruction=tone_instruction
        )
        
        if additional_context:
            prompt += f"\n\nAdditional context: {additional_context}"
        
        # Add system context to prompt for Gemini
        full_prompt = f"""You are an expert social media content creator specializing in AI education.

{prompt}"""
        
        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=1000
                )
            )
            
            content = response.text.strip()
            hashtags = self._extract_hashtags(content)
            
            return {
                "content": content,
                "hashtags": hashtags,
                "tokens_used": 0  # Gemini doesn't return token count the same way
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            if "api key" in error_msg or "invalid" in error_msg or "authenticate" in error_msg:
                raise LLMError("Invalid Gemini API key. Please check your key in Settings.")
            elif "quota" in error_msg or "limit" in error_msg:
                raise LLMError("Gemini API quota exceeded. Please try again later.")
            else:
                raise LLMError(f"Gemini API error: {str(e)}")


def get_user_llm_client(user: User, db: Session) -> BaseLLMClient:
    """
    Get an LLM client using the user's own API key.
    Priority: OpenAI > Gemini > Anthropic
    
    Args:
        user: The authenticated user
        db: Database session
        
    Returns:
        Configured LLM client
        
    Raises:
        LLMError if no valid API key found
    """
    # Try to find user's OpenAI key first
    api_key_record = db.query(UserApiKey).filter(
        UserApiKey.user_id == user.id,
        UserApiKey.key_type == ApiKeyType.OPENAI,
        UserApiKey.is_valid == True
    ).first()
    
    if not api_key_record:
        # Try Gemini as second priority
        api_key_record = db.query(UserApiKey).filter(
            UserApiKey.user_id == user.id,
            UserApiKey.key_type == ApiKeyType.GEMINI,
            UserApiKey.is_valid == True
        ).first()
    
    if not api_key_record:
        # Try Anthropic as fallback
        api_key_record = db.query(UserApiKey).filter(
            UserApiKey.user_id == user.id,
            UserApiKey.key_type == ApiKeyType.ANTHROPIC,
            UserApiKey.is_valid == True
        ).first()
    
    if not api_key_record:
        raise LLMError(
            "No LLM API key configured. Please add your OpenAI or Gemini API key in Settings."
        )
    
    # Decrypt the API key
    try:
        api_key = encryption.decrypt(api_key_record.encrypted_key)
    except EncryptionError:
        raise LLMError("Could not decrypt API key. Please re-enter your key in Settings.")
    
    # Return appropriate client based on key type
    if api_key_record.key_type == ApiKeyType.OPENAI:
        return OpenAIClient(api_key=api_key)
    
    elif api_key_record.key_type == ApiKeyType.GEMINI:
        return GeminiClient(api_key=api_key)
    
    raise LLMError(f"LLM provider {api_key_record.key_type.value} not yet supported")
