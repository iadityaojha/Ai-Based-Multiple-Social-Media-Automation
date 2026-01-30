"""
Encryption Module for Secure API Key Storage
=============================================
Uses Fernet symmetric encryption to protect user API keys.
"""

from cryptography.fernet import Fernet, InvalidToken
from app.config import settings
import base64
import hashlib


class EncryptionError(Exception):
    """Custom exception for encryption errors."""
    pass


class KeyEncryption:
    """
    Handles encryption and decryption of API keys.
    Uses Fernet (AES-128-CBC) for symmetric encryption.
    """
    
    def __init__(self):
        """Initialize with encryption key from settings."""
        key = settings.ENCRYPTION_KEY
        
        # Always generate a valid key from SECRET_KEY
        # This ensures the app works even without a properly configured ENCRYPTION_KEY
        try:
            if key and len(key) == 44 and key.endswith('='):
                # Looks like a valid Fernet key, try to use it
                key = key.encode() if isinstance(key, str) else key
                self.cipher = Fernet(key)
            else:
                # Generate deterministic key from SECRET_KEY
                raise ValueError("Generate from SECRET_KEY")
        except Exception:
            # Generate a deterministic key from SECRET_KEY for development
            hash_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
            key = base64.urlsafe_b64encode(hash_bytes)
            self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string (like an API key).
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        
        try:
            encrypted = self.cipher.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            ciphertext: The encrypted string
            
        Returns:
            Original plaintext string
        """
        if not ciphertext:
            return ""
        
        try:
            decrypted = self.cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken:
            raise EncryptionError("Invalid or corrupted encrypted data")
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")
    
    def mask_key(self, key: str, visible_chars: int = 4) -> str:
        """
        Mask an API key for display (show only last few characters).
        
        Args:
            key: The API key to mask
            visible_chars: Number of characters to show at the end
            
        Returns:
            Masked string like "••••••••abcd"
        """
        if not key or len(key) <= visible_chars:
            return "••••••••"
        
        masked_length = len(key) - visible_chars
        return "•" * min(masked_length, 12) + key[-visible_chars:]


# Singleton instance
encryption = KeyEncryption()


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.
    Use this to create ENCRYPTION_KEY for .env file.
    
    Returns:
        A valid Fernet key as a string
    """
    return Fernet.generate_key().decode()
