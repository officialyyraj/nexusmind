"""Secrets management with encryption for sensitive data."""

import base64
import os
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import get_settings


class SecretsManager:
    """Manages encryption and decryption of sensitive data."""

    def __init__(self, encryption_key: bytes | None = None):
        """Initialize secrets manager with encryption key."""
        settings = get_settings()

        if encryption_key:
            self._key = encryption_key
        elif settings.secret_key:
            self._key = self._derive_key(settings.secret_key)
        else:
            # Generate a new key (should only happen in development)
            self._key = Fernet.generate_key()

        self._fernet = Fernet(self._key)

    @staticmethod
    def _derive_key(password: str) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        salt = b"nexusmind_salt_v1"  # In production, use env variable
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        key = kdf.derive(password.encode())
        return base64.urlsafe_b64encode(key)

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key."""
        return Fernet.generate_key().decode()

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string."""
        if not plaintext:
            return ""
        encrypted = self._fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt an encrypted string."""
        if not ciphertext:
            return ""
        try:
            encrypted = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = self._fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception:
            # Return empty string if decryption fails
            return ""

    def encrypt_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Encrypt all string values in a dictionary."""
        encrypted = {}
        for key, value in data.items():
            if isinstance(value, str) and value:
                encrypted[key] = self.encrypt(value)
            elif isinstance(value, dict):
                encrypted[key] = self.encrypt_dict(value)
            else:
                encrypted[key] = value
        return encrypted

    def decrypt_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Decrypt all encrypted values in a dictionary."""
        decrypted = {}
        for key, value in data.items():
            if isinstance(value, str) and value:
                decrypted[key] = self.decrypt(value)
            elif isinstance(value, dict):
                decrypted[key] = self.decrypt_dict(value)
            else:
                decrypted[key] = value
        return decrypted


class SecureValue:
    """Wrapper for encrypted values that never exposes raw data."""

    def __init__(self, encrypted_value: str, manager: SecretsManager):
        self._encrypted = encrypted_value
        self._manager = manager

    @property
    def encrypted(self) -> str:
        """Get encrypted value."""
        return self._encrypted

    def decrypt(self) -> str:
        """Decrypt and return the value."""
        return self._manager.decrypt(self._encrypted)

    def __repr__(self) -> str:
        return "***REDACTED***"


class APIKeyManager(SecretsManager):
    """Specialized manager for API keys and credentials."""

    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key."""
        return self.encrypt(api_key)

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key."""
        return self.decrypt(encrypted_key)

    def encrypt_github_token(self, token: str) -> str:
        """Encrypt a GitHub token."""
        return self.encrypt(token)

    def decrypt_github_token(self, encrypted_token: str) -> str:
        """Decrypt a GitHub token."""
        return self.decrypt(encrypted_token)

    def encrypt_openai_key(self, api_key: str) -> str:
        """Encrypt an OpenAI API key."""
        return self.encrypt(api_key)

    def decrypt_openai_key(self, encrypted_key: str) -> str:
        """Decrypt an OpenAI API key."""
        return self.decrypt(encrypted_key)

    def encrypt_anthropic_key(self, api_key: str) -> str:
        """Encrypt an Anthropic API key."""
        return self.encrypt(api_key)

    def decrypt_anthropic_key(self, encrypted_key: str) -> str:
        """Decrypt an Anthropic API key."""
        return self.decrypt(encrypted_key)

    def encrypt_mcp_credentials(self, credentials: dict[str, Any]) -> dict[str, str]:
        """Encrypt MCP server credentials."""
        encrypted = {}
        for key, value in credentials.items():
            if isinstance(value, str):
                encrypted[key] = self.encrypt(value)
            else:
                encrypted[key] = str(value)
        return encrypted

    def decrypt_mcp_credentials(self, encrypted_credentials: dict[str, str]) -> dict[str, Any]:
        """Decrypt MCP server credentials."""
        decrypted = {}
        for key, value in encrypted_credentials.items():
            decrypted[key] = self.decrypt(value)
        return decrypted

    def encrypt_database_url(self, url: str) -> str:
        """Encrypt a database connection URL."""
        return self.encrypt(url)

    def decrypt_database_url(self, encrypted_url: str) -> str:
        """Decrypt a database connection URL."""
        return self.decrypt(encrypted_url)


class SecretsValidator:
    """Validates secrets and credentials."""

    @staticmethod
    def validate_openai_key(key: str) -> bool:
        """Validate OpenAI API key format."""
        if not key:
            return False
        # OpenAI keys typically start with sk-
        return key.startswith("sk-")

    @staticmethod
    def validate_anthropic_key(key: str) -> bool:
        """Validate Anthropic API key format."""
        if not key:
            return False
        # Anthropic keys typically start with sk-ant-
        return key.startswith("sk-ant-")

    @staticmethod
    def validate_github_token(token: str) -> bool:
        """Validate GitHub token format."""
        if not token:
            return False
        # GitHub tokens are typically 40+ characters
        return len(token) >= 40

    @staticmethod
    def validate_database_url(url: str) -> bool:
        """Validate database URL format."""
        if not url:
            return False
        valid_prefixes = ("postgresql://", "mysql://", "sqlite://")
        return url.startswith(valid_prefixes)


# Global secrets manager instance
_secrets_manager: APIKeyManager | None = None


def get_secrets_manager() -> APIKeyManager:
    """Get secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = APIKeyManager()
    return _secrets_manager
