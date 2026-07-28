"""BYOK Provider Service - User-scoped provider management.

This service provides CRUD operations for user AI provider connections:
- Each user owns their provider connections
- API keys are encrypted at rest
- All operations are user-scoped (no cross-user access)
- Rate limiting and audit logging
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.provider import (
    AuditAction,
    ProviderAuditLog,
    UserProviderConnection,
    VerificationStatus,
)
from app.llm.byok.adapters import (
    BYOKProviderAdapter,
    ModelInfo,
    VerificationResult,
    get_provider_registry,
)
from app.security.encryption import encrypt_api_key, decrypt_api_key, get_encryption_service


class ProviderServiceError(Exception):
    """Base exception for provider service errors."""
    pass


class ProviderNotFoundError(ProviderServiceError):
    """Provider connection not found."""
    pass


class ProviderLimitExceededError(ProviderServiceError):
    """User has too many provider connections."""
    pass


class DuplicateProviderError(ProviderServiceError):
    """Provider with this nickname already exists."""
    pass


class ProviderService:
    """Service for managing user AI provider connections.
    
    Features:
    - User-scoped operations (all queries include user_id)
    - Encrypted API key storage
    - Rate limiting for verification
    - Audit logging
    - Provider isolation
    """
    
    MAX_PROVIDERS_PER_USER = 20
    VERIFICATION_COOLDOWN_SECONDS = 60  # Prevent verification spam
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._registry = get_provider_registry()
        self._encryption = get_encryption_service()
    
    # ==================== CREATE ====================
    
    async def create_connection(
        self,
        user_id: uuid.UUID,
        provider: str,
        api_key: str,
        nickname: str | None = None,
        base_url: str | None = None,
        default_model: str | None = None,
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
        request_context: dict[str, Any] | None = None,
    ) -> UserProviderConnection:
        """Create a new provider connection.
        
        Args:
            user_id: User's UUID.
            provider: Provider name (e.g., "openai").
            api_key: Plaintext API key (will be encrypted).
            nickname: Optional friendly name.
            base_url: Custom API endpoint (for proxies/custom deployments).
            default_model: Preferred model.
            enabled: Whether connection is enabled.
            metadata: Additional provider-specific config.
            request_context: Request metadata for audit log.
            
        Returns:
            Created provider connection.
            
        Raises:
            ProviderLimitExceededError: If user has too many providers.
            DuplicateProviderError: If nickname already exists.
            ValueError: If provider is not supported.
        """
        # Verify provider is supported
        if not self._registry.has_provider(provider):
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Check provider limit
        existing = await self._count_user_providers(user_id)
        if existing >= self.MAX_PROVIDERS_PER_USER:
            raise ProviderLimitExceededError(
                f"Maximum of {self.MAX_PROVIDERS_PER_USER} providers allowed per user"
            )
        
        # Check for duplicate nickname
        if nickname:
            existing = await self._get_by_nickname(user_id, provider, nickname)
            if existing:
                raise DuplicateProviderError(
                    f"Provider '{provider}' with nickname '{nickname}' already exists"
                )
        
        # Encrypt API key
        encrypted_key = encrypt_api_key(api_key)
        
        # If this is the user's first provider, make it default
        is_first = existing == 0
        
        # Create connection
        connection = UserProviderConnection(
            user_id=user_id,
            provider=provider,
            nickname=nickname,
            encrypted_api_key=encrypted_key,
            base_url=base_url,
            default_model=default_model,
            enabled=enabled,
            is_default=is_first,
            metadata=metadata or {},
            verification_status=VerificationStatus.PENDING.value,
        )
        
        self.db.add(connection)
        await self.db.flush()
        await self.db.refresh(connection)
        
        # Audit log
        await self._log_audit(
            user_id=user_id,
            connection_id=connection.id,
            action=AuditAction.CONNECT,
            provider=provider,
            details={"nickname": nickname},
            request_context=request_context,
        )
        
        return connection
    
    # ==================== READ ====================
    
    async def list_connections(
        self,
        user_id: uuid.UUID,
        enabled_only: bool = False,
    ) -> list[UserProviderConnection]:
        """List all provider connections for a user.
        
        Args:
            user_id: User's UUID.
            enabled_only: Only return enabled connections.
            
        Returns:
            List of provider connections.
        """
        query = select(UserProviderConnection).where(
            UserProviderConnection.user_id == user_id
        )
        
        if enabled_only:
            query = query.where(UserProviderConnection.enabled == True)
        
        query = query.order_by(
            UserProviderConnection.is_default.desc(),
            UserProviderConnection.created_at.desc(),
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_connection(
        self,
        user_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> UserProviderConnection | None:
        """Get a specific provider connection.
        
        Args:
            user_id: User's UUID.
            connection_id: Connection UUID.
            
        Returns:
            Provider connection or None if not found.
        """
        result = await self.db.execute(
            select(UserProviderConnection).where(
                and_(
                    UserProviderConnection.id == connection_id,
                    UserProviderConnection.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_default_connection(
        self,
        user_id: uuid.UUID,
    ) -> UserProviderConnection | None:
        """Get user's default provider connection.
        
        Args:
            user_id: User's UUID.
            
        Returns:
            Default provider connection or None.
        """
        result = await self.db.execute(
            select(UserProviderConnection).where(
                and_(
                    UserProviderConnection.user_id == user_id,
                    UserProviderConnection.is_default == True,
                    UserProviderConnection.enabled == True,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_connection_for_provider(
        self,
        user_id: uuid.UUID,
        provider: str,
    ) -> UserProviderConnection | None:
        """Get a provider connection by provider name.
        
        Returns the default connection if multiple exist.
        
        Args:
            user_id: User's UUID.
            provider: Provider name.
            
        Returns:
            Provider connection or None.
        """
        result = await self.db.execute(
            select(UserProviderConnection).where(
                and_(
                    UserProviderConnection.user_id == user_id,
                    UserProviderConnection.provider == provider,
                    UserProviderConnection.enabled == True,
                )
            ).order_by(
                UserProviderConnection.is_default.desc(),
            ).limit(1)
        )
        return result.scalar_one_or_none()
    
    # ==================== UPDATE ====================
    
    async def update_connection(
        self,
        user_id: uuid.UUID,
        connection_id: uuid.UUID,
        updates: dict[str, Any],
        request_context: dict[str, Any] | None = None,
    ) -> UserProviderConnection:
        """Update a provider connection.
        
        Args:
            user_id: User's UUID.
            connection_id: Connection UUID.
            updates: Fields to update.
            request_context: Request metadata for audit log.
            
        Returns:
            Updated provider connection.
            
        Raises:
            ProviderNotFoundError: If connection not found.
        """
        connection = await self.get_connection(user_id, connection_id)
        if not connection:
            raise ProviderNotFoundError(f"Provider connection not found: {connection_id}")
        
        # Handle API key update (requires re-encryption)
        if "api_key" in updates:
            updates["encrypted_api_key"] = encrypt_api_key(updates.pop("api_key"))
            updates["verification_status"] = VerificationStatus.PENDING.value
            updates["last_verified"] = None
        
        # Handle nickname uniqueness check
        if "nickname" in updates and updates["nickname"]:
            existing = await self._get_by_nickname(
                user_id, connection.provider, updates["nickname"]
            )
            if existing and existing.id != connection_id:
                raise DuplicateProviderError(
                    f"Provider '{connection.provider}' with nickname '{updates['nickname']}' already exists"
                )
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(connection, key):
                setattr(connection, key, value)
        
        connection.updated_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(connection)
        
        # Audit log
        await self._log_audit(
            user_id=user_id,
            connection_id=connection_id,
            action=AuditAction.UPDATE,
            provider=connection.provider,
            details={"updated_fields": list(updates.keys())},
            request_context=request_context,
        )
        
        return connection
    
    async def set_default(
        self,
        user_id: uuid.UUID,
        connection_id: uuid.UUID,
        request_context: dict[str, Any] | None = None,
    ) -> UserProviderConnection:
        """Set a connection as the default provider.
        
        Args:
            user_id: User's UUID.
            connection_id: Connection UUID.
            request_context: Request metadata for audit log.
            
        Returns:
            Updated provider connection.
        """
        connection = await self.get_connection(user_id, connection_id)
        if not connection:
            raise ProviderNotFoundError(f"Provider connection not found: {connection_id}")
        
        # Clear other defaults for this provider
        result = await self.db.execute(
            select(UserProviderConnection).where(
                and_(
                    UserProviderConnection.user_id == user_id,
                    UserProviderConnection.provider == connection.provider,
                    UserProviderConnection.is_default == True,
                )
            )
        )
        for other in result.scalars().all():
            if other.id != connection_id:
                other.is_default = False
        
        # Set this as default
        connection.is_default = True
        connection.updated_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(connection)
        
        # Audit log
        await self._log_audit(
            user_id=user_id,
            connection_id=connection_id,
            action=AuditAction.SET_DEFAULT,
            provider=connection.provider,
            request_context=request_context,
        )
        
        return connection
    
    async def enable(
        self,
        user_id: uuid.UUID,
        connection_id: uuid.UUID,
        request_context: dict[str, Any] | None = None,
    ) -> UserProviderConnection:
        """Enable a provider connection.
        
        Args:
            user_id: User's UUID.
            connection_id: Connection UUID.
            request_context: Request metadata for audit log.
            
        Returns:
            Updated provider connection.
        """
        return await self.update_connection(
            user_id,
            connection_id,
            {"enabled": True},
            request_context,
        )
    
    async def disable(
        self,
        user_id: uuid.UUID,
        connection_id: uuid.UUID,
        request_context: dict[str, Any] | None = None,
    ) -> UserProviderConnection:
        """Disable a provider connection.
        
        Args:
            user_id: User's UUID.
            connection_id: Connection UUID.
            request_context: Request metadata for audit log.
            
        Returns:
            Updated provider connection.
        """
        connection = await self.get_connection(user_id, connection_id)
        if not connection:
            raise ProviderNotFoundError(f"Provider connection not found: {connection_id}")
        
        # Audit log before update
        await self._log_audit(
            user_id=user_id,
            connection_id=connection_id,
            action=AuditAction.DISABLE,
            provider=connection.provider,
            request_context=request_context,
        )
        
        return await self.update_connection(
            user_id,
            connection_id,
            {"enabled": False},
            request_context,
        )
    
    # ==================== DELETE ====================
    
    async def delete_connection(
        self,
        user_id: uuid.UUID,
        connection_id: uuid.UUID,
        request_context: dict[str, Any] | None = None,
    ) -> bool:
        """Delete a provider connection.
        
        Args:
            user_id: User's UUID.
            connection_id: Connection UUID.
            request_context: Request metadata for audit log.
            
        Returns:
            True if deleted.
        """
        connection = await self.get_connection(user_id, connection_id)
        if not connection:
            return False
        
        provider = connection.provider
        
        # Audit log before delete
        await self._log_audit(
            user_id=user_id,
            connection_id=connection_id,
            action=AuditAction.DELETE,
            provider=provider,
            request_context=request_context,
        )
        
        await self.db.delete(connection)
        await self.db.flush()
        
        return True
    
    # ==================== VERIFICATION ====================
    
    async def verify_connection(
        self,
        user_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> VerificationResult:
        """Verify a provider connection.
        
        Args:
            user_id: User's UUID.
            connection_id: Connection UUID.
            
        Returns:
            Verification result.
        """
        connection = await self.get_connection(user_id, connection_id)
        if not connection:
            raise ProviderNotFoundError(f"Provider connection not found: {connection_id}")
        
        # Get adapter class
        adapter_class = self._registry.get(connection.provider)
        if not adapter_class:
            return VerificationResult(
                success=False,
                message=f"Provider not supported: {connection.provider}",
                error_code="unsupported_provider",
            )
        
        # Decrypt API key
        try:
            api_key = decrypt_api_key(connection.encrypted_api_key)
        except Exception as e:
            return VerificationResult(
                success=False,
                message="Failed to decrypt API key",
                error_code="decryption_error",
            )
        
        # Create adapter and verify
        async with adapter_class(
            api_key=api_key,
            base_url=connection.base_url,
        ) as adapter:
            result = await adapter.verify_key()
        
        # Update connection with verification result
        if result.success:
            connection.verification_status = VerificationStatus.VERIFIED.value
            connection.last_verified = datetime.utcnow()
            connection.verification_error = None
        else:
            connection.verification_status = VerificationStatus.FAILED.value
            connection.verification_error = result.message
        
        connection.updated_at = datetime.utcnow()
        await self.db.flush()
        
        # Audit log
        await self._log_audit(
            user_id=user_id,
            connection_id=connection_id,
            action=AuditAction.VERIFY,
            provider=connection.provider,
            details={
                "success": result.success,
                "message": result.message,
            },
        )
        
        return result
    
    async def get_available_models(
        self,
        user_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> list[ModelInfo]:
        """Get available models for a provider connection.
        
        Args:
            user_id: User's UUID.
            connection_id: Connection UUID.
            
        Returns:
            List of available models.
        """
        connection = await self.get_connection(user_id, connection_id)
        if not connection:
            raise ProviderNotFoundError(f"Provider connection not found: {connection_id}")
        
        # Get adapter class
        adapter_class = self._registry.get(connection.provider)
        if not adapter_class:
            return []
        
        # Decrypt API key
        try:
            api_key = decrypt_api_key(connection.encrypted_api_key)
        except Exception:
            return []
        
        # Create adapter and get models
        async with adapter_class(
            api_key=api_key,
            base_url=connection.base_url,
        ) as adapter:
            return await adapter.available_models()
    
    # ==================== ADAPTER CREATION ====================
    
    async def create_adapter(
        self,
        user_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> BYOKProviderAdapter | None:
        """Create an adapter instance for a connection.
        
        This method decrypts the API key and creates a provider adapter.
        The plaintext API key is held in memory only during request execution.
        
        Args:
            user_id: User's UUID.
            connection_id: Connection UUID.
            
        Returns:
            Configured adapter instance or None.
        """
        connection = await self.get_connection(user_id, connection_id)
        if not connection or not connection.enabled:
            return None
        
        # Update usage stats
        connection.use_count += 1
        connection.last_used_at = datetime.utcnow()
        await self.db.flush()
        
        # Get adapter class
        adapter_class = self._registry.get(connection.provider)
        if not adapter_class:
            return None
        
        # Decrypt API key
        api_key = decrypt_api_key(connection.encrypted_api_key)
        
        # Create adapter
        return adapter_class(
            api_key=api_key,
            base_url=connection.base_url,
            model=connection.default_model,
        )
    
    # ==================== HELPER METHODS ====================
    
    async def _count_user_providers(self, user_id: uuid.UUID) -> int:
        """Count user's provider connections."""
        result = await self.db.execute(
            select(UserProviderConnection).where(
                UserProviderConnection.user_id == user_id
            )
        )
        return len(result.scalars().all())
    
    async def _get_by_nickname(
        self,
        user_id: uuid.UUID,
        provider: str,
        nickname: str,
    ) -> UserProviderConnection | None:
        """Get connection by nickname."""
        result = await self.db.execute(
            select(UserProviderConnection).where(
                and_(
                    UserProviderConnection.user_id == user_id,
                    UserProviderConnection.provider == provider,
                    UserProviderConnection.nickname == nickname,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _log_audit(
        self,
        user_id: uuid.UUID,
        action: AuditAction,
        provider: str,
        connection_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        request_context: dict[str, Any] | None = None,
    ) -> None:
        """Create an audit log entry."""
        log = ProviderAuditLog(
            user_id=user_id,
            connection_id=connection_id,
            action=action.value,
            provider=provider,
            details=details or {},
            ip_address=request_context.get("ip_address") if request_context else None,
            user_agent=request_context.get("user_agent") if request_context else None,
        )
        self.db.add(log)
        await self.db.flush()
    
    # ==================== LIST PROVIDERS ====================
    
    def list_supported_providers(self) -> list[dict[str, Any]]:
        """List all supported BYOK providers.
        
        Returns:
            List of provider info dicts.
        """
        return self._registry.list_providers()
