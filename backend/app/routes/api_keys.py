"""
API Keys Management Routes
==========================
Secure endpoints for users to manage their API keys.
All keys are encrypted before storage.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserApiKey, ApiKeyType
from app.auth import get_current_user
from app.encryption import encryption, EncryptionError

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


# =========================================
# Pydantic Schemas
# =========================================
class ApiKeyCreate(BaseModel):
    key_type: str = Field(..., description="Type: openai, gemini, anthropic, linkedin, instagram, facebook")
    api_key: str = Field(..., min_length=10, description="The API key value")
    key_name: Optional[str] = Field(None, max_length=255, description="Friendly name for this key")
    credentials: Optional[dict] = Field(None, description="Additional credentials (e.g., client_id, client_secret)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "key_type": "openai",
                "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxx",
                "key_name": "My OpenAI Key"
            }
        }


class ApiKeyUpdate(BaseModel):
    api_key: Optional[str] = Field(None, min_length=10)
    key_name: Optional[str] = Field(None, max_length=255)
    credentials: Optional[dict] = None


class ApiKeyResponse(BaseModel):
    id: int
    key_type: str
    key_name: Optional[str]
    masked_key: str  # Show only last 4 characters
    is_valid: bool
    last_used: Optional[str]
    created_at: str
    updated_at: str


class ApiKeyStatusResponse(BaseModel):
    """Shows which API keys the user has configured."""
    openai: bool
    gemini: bool
    anthropic: bool
    linkedin: bool
    instagram: bool
    facebook: bool


# =========================================
# Helper Functions
# =========================================
def get_key_type_enum(key_type_str: str) -> ApiKeyType:
    """Convert string to ApiKeyType enum."""
    try:
        return ApiKeyType(key_type_str.lower())
    except ValueError:
        valid = [t.value for t in ApiKeyType]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid key type. Valid options: {valid}"
        )


# =========================================
# Routes
# =========================================
@router.get("/status", response_model=ApiKeyStatusResponse)
async def get_keys_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check which API keys the user has configured.
    Returns a boolean for each key type.
    """
    keys = db.query(UserApiKey).filter(
        UserApiKey.user_id == user.id,
        UserApiKey.is_valid == True
    ).all()
    
    configured = {key.key_type.value for key in keys}
    
    return ApiKeyStatusResponse(
        openai="openai" in configured,
        gemini="gemini" in configured,
        anthropic="anthropic" in configured,
        linkedin="linkedin" in configured,
        instagram="instagram" in configured,
        facebook="facebook" in configured
    )


@router.get("/", response_model=List[ApiKeyResponse])
async def list_keys(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all API keys for the current user.
    Keys are masked for security (only last 4 characters shown).
    """
    keys = db.query(UserApiKey).filter(UserApiKey.user_id == user.id).all()
    
    result = []
    for key in keys:
        # Decrypt and mask the key for display
        try:
            decrypted = encryption.decrypt(key.encrypted_key)
            masked = encryption.mask_key(decrypted)
        except EncryptionError:
            masked = "••••••••[error]"
        
        result.append(ApiKeyResponse(
            id=key.id,
            key_type=key.key_type.value,
            key_name=key.key_name,
            masked_key=masked,
            is_valid=key.is_valid,
            last_used=key.last_used.isoformat() if key.last_used else None,
            created_at=key.created_at.isoformat(),
            updated_at=key.updated_at.isoformat()
        ))
    
    return result


@router.post("/", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    data: ApiKeyCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new API key for the current user.
    The key is encrypted before storage.
    """
    key_type = get_key_type_enum(data.key_type)
    
    # Check if key type already exists for this user
    existing = db.query(UserApiKey).filter(
        UserApiKey.user_id == user.id,
        UserApiKey.key_type == key_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A {key_type.value} key already exists. Update or delete it first."
        )
    
    # Encrypt the API key
    try:
        encrypted_key = encryption.encrypt(data.api_key)
        encrypted_credentials = None
        if data.credentials:
            import json
            encrypted_credentials = encryption.encrypt(json.dumps(data.credentials))
    except EncryptionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encryption failed: {str(e)}"
        )
    
    # Create the key record
    api_key = UserApiKey(
        user_id=user.id,
        key_type=key_type,
        encrypted_key=encrypted_key,
        encrypted_credentials=encrypted_credentials,
        key_name=data.key_name or f"My {key_type.value.title()} Key",
        is_valid=True
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return ApiKeyResponse(
        id=api_key.id,
        key_type=api_key.key_type.value,
        key_name=api_key.key_name,
        masked_key=encryption.mask_key(data.api_key),
        is_valid=api_key.is_valid,
        last_used=None,
        created_at=api_key.created_at.isoformat(),
        updated_at=api_key.updated_at.isoformat()
    )


@router.put("/{key_id}", response_model=ApiKeyResponse)
async def update_key(
    key_id: int,
    data: ApiKeyUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing API key.
    """
    api_key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Update fields
    if data.key_name is not None:
        api_key.key_name = data.key_name
    
    if data.api_key:
        try:
            api_key.encrypted_key = encryption.encrypt(data.api_key)
            api_key.is_valid = True  # Reset validity when key is updated
        except EncryptionError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Encryption failed: {str(e)}"
            )
    
    if data.credentials is not None:
        try:
            import json
            api_key.encrypted_credentials = encryption.encrypt(json.dumps(data.credentials))
        except EncryptionError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Encryption failed: {str(e)}"
            )
    
    db.commit()
    db.refresh(api_key)
    
    # Get masked key for response
    try:
        decrypted = encryption.decrypt(api_key.encrypted_key)
        masked = encryption.mask_key(decrypted)
    except EncryptionError:
        masked = "••••••••"
    
    return ApiKeyResponse(
        id=api_key.id,
        key_type=api_key.key_type.value,
        key_name=api_key.key_name,
        masked_key=masked,
        is_valid=api_key.is_valid,
        last_used=api_key.last_used.isoformat() if api_key.last_used else None,
        created_at=api_key.created_at.isoformat(),
        updated_at=api_key.updated_at.isoformat()
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(
    key_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an API key.
    """
    api_key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    db.delete(api_key)
    db.commit()


@router.post("/{key_id}/test")
async def test_key(
    key_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test if an API key is valid by making a test API call.
    """
    api_key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Decrypt the key
    try:
        decrypted_key = encryption.decrypt(api_key.encrypted_key)
    except EncryptionError:
        api_key.is_valid = False
        db.commit()
        return {"valid": False, "message": "Could not decrypt key"}
    
    # Test based on key type
    is_valid = True
    message = "Key is valid"
    
    if api_key.key_type == ApiKeyType.OPENAI:
        try:
            import openai
            client = openai.OpenAI(api_key=decrypted_key)
            # Make a minimal API call
            client.models.list()
            message = "OpenAI API key is valid"
        except Exception as e:
            is_valid = False
            message = f"OpenAI API error: {str(e)}"
    
    elif api_key.key_type == ApiKeyType.GEMINI:
        try:
            import google.generativeai as genai
            genai.configure(api_key=decrypted_key)
            # Make a minimal API call to verify the key
            models = list(genai.list_models())
            if models:
                message = "Google Gemini API key is valid!"
            else:
                message = "Gemini key accepted (no models found)"
        except Exception as e:
            is_valid = False
            message = f"Gemini API error: {str(e)}"
    
    elif api_key.key_type == ApiKeyType.LINKEDIN:
        try:
            import requests
            # Test the access token by calling LinkedIn's userinfo endpoint
            headers = {"Authorization": f"Bearer {decrypted_key}"}
            response = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                user_info = response.json()
                name = user_info.get("name", "Unknown")
                message = f"LinkedIn access token is valid! Connected as: {name}"
            elif response.status_code == 401:
                is_valid = False
                message = "LinkedIn access token is invalid or expired"
            else:
                is_valid = False
                message = f"LinkedIn API error: {response.status_code} - {response.text[:100]}"
        except Exception as e:
            is_valid = False
            message = f"LinkedIn API error: {str(e)}"
    
    elif api_key.key_type in [ApiKeyType.INSTAGRAM, ApiKeyType.FACEBOOK]:
        # For social media, we'll mark as valid for now (real validation requires OAuth)
        message = f"{api_key.key_type.value.title()} credentials saved (validation requires OAuth flow)"
    
    else:
        message = f"{api_key.key_type.value.title()} key saved (validation not yet implemented)"
    
    # Update validity status
    api_key.is_valid = is_valid
    api_key.last_used = datetime.utcnow()
    db.commit()
    
    return {"valid": is_valid, "message": message}
