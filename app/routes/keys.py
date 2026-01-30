"""
API Keys Routes Module
======================
Handles CRUD operations for API keys with encryption.
Keys are stored encrypted in the database for security.
"""

import base64
import hashlib
from datetime import datetime
from typing import Optional
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import APIKey
from app.config import settings

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


# =========================================
# Encryption Helpers
# =========================================
def get_encryption_key() -> bytes:
    """
    Generate a consistent encryption key from a secret.
    In production, use a secure key management service.
    """
    # Use a combination of secrets to generate the key
    secret = settings.DATABASE_URL + "api_key_encryption_salt"
    key = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for storage."""
    fernet = Fernet(get_encryption_key())
    return fernet.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key from storage."""
    fernet = Fernet(get_encryption_key())
    return fernet.decrypt(encrypted_key.encode()).decode()


def mask_api_key(api_key: str) -> str:
    """Mask an API key for display, showing only first and last 4 characters."""
    if len(api_key) <= 8:
        return "••••••••"
    return f"{api_key[:4]}••••{api_key[-4:]}"


# =========================================
# Pydantic Schemas
# =========================================
class APIKeyCreate(BaseModel):
    key_type: str
    api_key: str


class APIKeyUpdate(BaseModel):
    api_key: str


class APIKeyResponse(BaseModel):
    id: int
    key_type: str
    masked_key: str
    is_valid: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================
# Routes
# =========================================
@router.get("/status")
def get_keys_status(db: Session = Depends(get_db)):
    """
    Get the status of all API keys (whether they're configured).
    Returns a dict like {"openai": true, "gemini": false, ...}
    """
    keys = db.query(APIKey).all()
    key_types = ["openai", "gemini", "linkedin", "instagram", "facebook"]
    
    status = {}
    for key_type in key_types:
        key = next((k for k in keys if k.key_type == key_type), None)
        status[key_type] = key is not None and key.is_valid
    
    return status


@router.get("/", response_model=list[APIKeyResponse])
def list_keys(db: Session = Depends(get_db)):
    """List all stored API keys (masked)."""
    keys = db.query(APIKey).all()
    
    result = []
    for key in keys:
        try:
            decrypted = decrypt_api_key(key.encrypted_key)
            masked = mask_api_key(decrypted)
        except Exception:
            masked = "••••••••"
        
        result.append(APIKeyResponse(
            id=key.id,
            key_type=key.key_type,
            masked_key=masked,
            is_valid=key.is_valid,
            created_at=key.created_at,
            updated_at=key.updated_at
        ))
    
    return result


@router.post("/", response_model=APIKeyResponse)
def create_key(data: APIKeyCreate, db: Session = Depends(get_db)):
    """Create a new API key."""
    # Check if key already exists
    existing = db.query(APIKey).filter(APIKey.key_type == data.key_type).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"API key for {data.key_type} already exists. Use PUT to update.")
    
    # Encrypt and store
    encrypted = encrypt_api_key(data.api_key)
    key = APIKey(
        key_type=data.key_type,
        encrypted_key=encrypted,
        is_valid=True  # Assume valid until tested
    )
    
    db.add(key)
    db.commit()
    db.refresh(key)
    
    return APIKeyResponse(
        id=key.id,
        key_type=key.key_type,
        masked_key=mask_api_key(data.api_key),
        is_valid=key.is_valid,
        created_at=key.created_at,
        updated_at=key.updated_at
    )


@router.put("/{key_id}", response_model=APIKeyResponse)
def update_key(key_id: int, data: APIKeyUpdate, db: Session = Depends(get_db)):
    """Update an existing API key."""
    key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Encrypt and update
    key.encrypted_key = encrypt_api_key(data.api_key)
    key.is_valid = True  # Reset validity status
    key.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(key)
    
    return APIKeyResponse(
        id=key.id,
        key_type=key.key_type,
        masked_key=mask_api_key(data.api_key),
        is_valid=key.is_valid,
        created_at=key.created_at,
        updated_at=key.updated_at
    )


@router.delete("/{key_id}")
def delete_key(key_id: int, db: Session = Depends(get_db)):
    """Delete an API key."""
    key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(key)
    db.commit()
    
    return {"message": "API key deleted successfully"}


@router.post("/{key_id}/test")
def test_key(key_id: int, db: Session = Depends(get_db)):
    """Test if an API key is valid by making a simple API call."""
    key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    try:
        decrypted = decrypt_api_key(key.encrypted_key)
    except Exception:
        key.is_valid = False
        db.commit()
        raise HTTPException(status_code=400, detail="Failed to decrypt key. Please update the key.")
    
    # Test based on key type
    try:
        if key.key_type == "openai":
            import openai
            client = openai.OpenAI(api_key=decrypted)
            # Simple test - list models
            client.models.list()
            key.is_valid = True
            message = "OpenAI API key is valid!"
            
        elif key.key_type == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=decrypted)
            # Simple test - list models
            list(genai.list_models())
            key.is_valid = True
            message = "Google Gemini API key is valid!"
            
        elif key.key_type in ["linkedin", "instagram", "facebook"]:
            # For social media keys, we just accept them as valid for now
            # Real validation would require OAuth flow
            key.is_valid = True
            message = f"{key.key_type.title()} access token saved. Validation will occur during posting."
            
        else:
            key.is_valid = True
            message = f"API key for {key.key_type} saved successfully."
            
        db.commit()
        return {"message": message, "is_valid": True}
        
    except Exception as e:
        key.is_valid = False
        db.commit()
        raise HTTPException(status_code=400, detail=f"API key validation failed: {str(e)}")
