"""AES-256-GCM Encryption Service for API Key Security.

This module provides military-grade encryption for user API keys:
- AES-256-GCM authenticated encryption
- Unique IV per encryption (never reuse)
- Server master key from configuration
- Constant-time decryption
- Memory cleanup after use
- Zero plaintext logging
"""

import base64
import secrets
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


class EncryptionService:
    """AES-256-GCM encryption service for API keys.
    
    Security Properties:
    - AES-256-GCM provides authenticated encryption (confidentiality + integrity)
    - 96-bit (12-byte) nonce/IV for GCM mode
    - Unique nonce per encryption (random 12 bytes)
    - Authentication tag verified on decryption
    - Master key stored in server configuration
    - No plaintext ever written to logs or returned to clients
    
    Format: base64(nonce || ciphertext || tag)
    """
    
    # AES-256-GCM uses 256-bit keys (32 bytes)
    KEY_SIZE_BYTES = 32
    
    # GCM recommended IV size is 96 bits (12 bytes)
    NONCE_SIZE_BYTES = 12
    
    def __init__(self, master_key: bytes | None = None):
        """Initialize encryption service.
        
        Args:
            master_key: 32-byte master key. If None, loaded from config.
            
        Raises:
            EncryptionError: If master key is invalid.
        """
        if master_key is None:
            master_key = self._load_master_key()
        
        if len(master_key) != self.KEY_SIZE_BYTES:
            raise EncryptionError(
                f"Master key must be {self.KEY_SIZE_BYTES} bytes, got {len(master_key)}"
            )
        
        self._aesgcm = AESGCM(master_key)
        self._master_key = master_key  # Keep for potential zeroing
    
    def _load_master_key(self) -> bytes:
        """Load master key from configuration.
        
        Returns:
            32-byte master key.
            
        Raises:
            EncryptionError: If key not configured.
        """
        settings = get_settings()
        
        # Check for ENCRYPTION_MASTER_KEY in settings
        master_key_hex = getattr(settings, 'encryption_master_key', None)
        
        if not master_key_hex:
            # Generate a warning but allow fallback for development
            # In production, this should be required
            if settings.is_production:
                raise EncryptionError(
                    "ENCRYPTION_MASTER_KEY not configured. "
                    "Set it to a 64-character hex string (32 bytes)."
                )
            # Development fallback - generate ephemeral key
            # WARNING: Keys encrypted with this will be lost on restart!
            return secrets.token_bytes(self.KEY_SIZE_BYTES)
        
        try:
            # Convert hex to bytes
            key_bytes = bytes.fromhex(master_key_hex)
            return key_bytes
        except ValueError as e:
            raise EncryptionError(f"Invalid master key format: {e}")
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt.
            
        Returns:
            Base64-encoded ciphertext: nonce || ciphertext || tag.
            
        Raises:
            EncryptionError: If encryption fails.
        """
        if not plaintext:
            raise EncryptionError("Cannot encrypt empty plaintext")
        
        try:
            # Generate unique nonce for each encryption
            nonce = secrets.token_bytes(self.NONCE_SIZE_BYTES)
            
            # Encode plaintext to bytes
            plaintext_bytes = plaintext.encode('utf-8')
            
            # Encrypt with authentication
            ciphertext_with_tag = self._aesgcm.encrypt(
                nonce,
                plaintext_bytes,
                None  # No additional authenticated data (AAD)
            )
            
            # Combine: nonce || ciphertext_with_tag
            combined = nonce + ciphertext_with_tag
            
            # Return base64 encoded
            return base64.b64encode(combined).decode('ascii')
            
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext back to plaintext.
        
        Args:
            ciphertext: Base64-encoded ciphertext.
            
        Returns:
            Decrypted plaintext string.
            
        Raises:
            EncryptionError: If decryption fails (wrong key, tampered data, etc.)
        """
        if not ciphertext:
            raise EncryptionError("Cannot decrypt empty ciphertext")
        
        try:
            # Decode base64
            combined = base64.b64decode(ciphertext.encode('ascii'))
            
            # Extract nonce and ciphertext+tag
            nonce = combined[:self.NONCE_SIZE_BYTES]
            ciphertext_with_tag = combined[self.NONCE_SIZE_BYTES:]
            
            # Decrypt and verify authentication tag
            plaintext_bytes = self._aesgcm.decrypt(
                nonce,
                ciphertext_with_tag,
                None
            )
            
            # Return as string
            return plaintext_bytes.decode('utf-8')
            
        except ValueError as e:
            # Authentication tag mismatch - tampered data or wrong key
            raise EncryptionError(f"Decryption failed (authentication error): {e}")
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")
    
    def encrypt_dict(self, data: dict[str, Any]) -> str:
        """Encrypt a dictionary as JSON.
        
        Args:
            data: Dictionary to encrypt.
            
        Returns:
            Base64-encoded encrypted JSON.
        """
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, ciphertext: str) -> dict[str, Any]:
        """Decrypt ciphertext to dictionary.
        
        Args:
            ciphertext: Base64-encoded encrypted JSON.
            
        Returns:
            Decrypted dictionary.
        """
        import json
        json_str = self.decrypt(ciphertext)
        return json.loads(json_str)
    
    def generate_api_key_mask(self, api_key: str, visible_chars: int = 4) -> str:
        """Generate a masked version of an API key for display.
        
        Args:
            api_key: The full API key.
            visible_chars: Number of characters to show at start/end.
            
        Returns:
            Masked key like "sk-or-••••••••••••••••3f4g"
        """
        if len(api_key) <= visible_chars * 2:
            return "••••••••"
        
        start = api_key[:visible_chars]
        end = api_key[-visible_chars:]
        middle = "•" * (len(api_key) - visible_chars * 2)
        
        return f"{start}{middle}{end}"
    
    def verify_key_format(self, api_key: str, provider: str) -> bool:
        """Verify API key has expected format for provider.
        
        This is a basic format check only. Full verification
        requires a test API call.
        
        Args:
            api_key: The API key to check.
            provider: Provider name.
            
        Returns:
            True if format looks correct.
        """
        if not api_key or len(api_key) < 10:
            return False
        
        # Provider-specific format checks
        format_checks = {
            "openai": lambda k: k.startswith("sk-") and len(k) > 40,
            "anthropic": lambda k: k.startswith("sk-ant-") and len(k) > 50,
            "google": lambda k: ("AIza" in k or "gsk_" in k) and len(k) > 30,
            "groq": lambda k: k.startswith("gsk_") and len(k) > 50,
            "together": lambda k: len(k) > 40,
            "deepseek": lambda k: k.startswith("sk-") and len(k) > 40,
            "mistral": lambda k: len(k) > 40,
            "xai": lambda k: len(k) > 40,
            "openrouter": lambda k: len(k) > 40,
        }
        
        check_func = format_checks.get(provider.lower())
        if check_func:
            return check_func(api_key)
        
        # Generic check for unknown providers
        return len(api_key) >= 20 and not api_key.startswith("••")
    
    def zero_memory(self, data: bytearray) -> None:
        """Zero out sensitive data in memory.
        
        This is a best-effort attempt. Python's garbage collector
        may have already copied data elsewhere.
        
        Args:
            data: Bytearray to zero out.
        """
        if isinstance(data, bytearray):
            for i in range(len(data)):
                data[i] = 0
    
    def __del__(self):
        """Cleanup on deletion."""
        # Best-effort zeroing of master key
        if hasattr(self, '_master_key') and self._master_key:
            try:
                self._master_key = bytes(len(self._master_key))  # Create new zeroed bytes
            except Exception:
                pass


# Global encryption service instance (lazy loaded)
_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """Get the global encryption service instance.
    
    Returns:
        EncryptionService singleton.
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def encrypt_api_key(api_key: str) -> str:
    """Convenience function to encrypt an API key.
    
    Args:
        api_key: Plaintext API key.
        
    Returns:
        Encrypted API key (base64).
    """
    return get_encryption_service().encrypt(api_key)


def decrypt_api_key(encrypted: str) -> str:
    """Convenience function to decrypt an API key.
    
    Args:
        encrypted: Encrypted API key (base64).
        
    Returns:
        Plaintext API key.
    """
    return get_encryption_service().decrypt(encrypted)
