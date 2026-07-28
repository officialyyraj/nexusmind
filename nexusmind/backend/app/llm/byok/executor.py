"""BYOK Execution Service - Per-user LLM execution with BYOK providers.

This service provides LLM execution that respects user BYOK configurations:
1. Check if authenticated user has a BYOK provider
2. If yes, decrypt API key and create temporary adapter
3. Route request through user's provider
4. Immediately clean up plaintext keys after use
5. Fall back to system providers if no BYOK configured

No global provider instances. No singleton API keys.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.byok.adapters import (
    BYOKProviderAdapter,
    ChatCompletion,
    ChatMessage,
    ProviderError,
    RateLimitError,
    get_provider_registry,
)
from app.llm.byok.service import ProviderService
from app.llm.providers import LLMMessage, LLMResponse


class BYOKExecutionError(Exception):
    """Error during BYOK execution."""
    
    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        is_retryable: bool = True,
        provider: str | None = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.is_retryable = is_retryable
        self.provider = provider


class BYOKExecutionService:
    """Service for executing LLM requests using user BYOK providers.
    
    This service provides per-user LLM execution:
    - User-scoped provider lookup
    - On-demand API key decryption
    - No persistent provider instances
    - Immediate memory cleanup after use
    
    Execution Flow:
    1. Get user's default BYOK provider
    2. Create adapter with decrypted API key
    3. Execute request
    4. Destroy plaintext key
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._service = ProviderService(db)
        self._registry = get_provider_registry()
    
    async def get_user_provider(
        self,
        user_id: uuid.UUID,
        provider: str | None = None,
    ) -> tuple[BYOKProviderAdapter, dict[str, Any]] | None:
        """Get user's BYOK provider adapter.
        
        This method:
        1. Looks up user's provider connection
        2. Decrypts the API key
        3. Creates an adapter instance
        
        Args:
            user_id: User's UUID.
            provider: Optional specific provider name.
            
        Returns:
            Tuple of (adapter, connection_info) or None if no provider found.
        """
        # Get connection
        if provider:
            connection = await self._service.get_connection_for_provider(user_id, provider)
        else:
            connection = await self._service.get_default_connection(user_id)
        
        if not connection or not connection.enabled:
            return None
        
        # Create adapter
        adapter = await self._service.create_adapter(user_id, connection.id)
        if not adapter:
            return None
        
        connection_info = {
            "id": str(connection.id),
            "provider": connection.provider,
            "nickname": connection.nickname,
            "model": connection.default_model,
            "is_default": connection.is_default,
        }
        
        return adapter, connection_info
    
    async def chat(
        self,
        user_id: uuid.UUID,
        messages: list[LLMMessage],
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request using user's BYOK provider.
        
        Args:
            user_id: User's UUID.
            messages: Chat messages.
            provider: Optional specific provider.
            model: Optional model override.
            temperature: Sampling temperature.
            max_tokens: Max tokens in response.
            
        Returns:
            LLMResponse with completion.
            
        Raises:
            BYOKExecutionError: If execution fails.
        """
        result = await self.get_user_provider(user_id, provider)
        
        if not result:
            raise BYOKExecutionError(
                "No BYOK provider configured",
                error_code="no_provider",
                is_retryable=False,
            )
        
        adapter, connection_info = result
        
        # Convert messages to BYOK format
        byok_messages = [
            ChatMessage(role=m["role"], content=m["content"])
            for m in messages
        ]
        
        try:
            # Execute request
            completion = await adapter.chat(
                messages=byok_messages,
                model=model or connection_info.get("model"),
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            
            # Convert to LLMResponse format
            return LLMResponse(
                content=completion.content,
                model=completion.model,
                usage=completion.usage or {},
                finish_reason=completion.finish_reason,
            )
            
        except ProviderError as e:
            raise BYOKExecutionError(
                str(e),
                error_code=e.error_code,
                is_retryable=e.is_retryable,
                provider=e.provider,
            )
        except Exception as e:
            raise BYOKExecutionError(
                f"Execution failed: {str(e)}",
                provider=connection_info.get("provider"),
            )
        finally:
            # Cleanup: close adapter and clear any sensitive data
            await adapter.close()
    
    async def stream(
        self,
        user_id: uuid.UUID,
        messages: list[LLMMessage],
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat response using user's BYOK provider.
        
        Args:
            user_id: User's UUID.
            messages: Chat messages.
            provider: Optional specific provider.
            model: Optional model override.
            temperature: Sampling temperature.
            max_tokens: Max tokens in response.
            
        Yields:
            String chunks of the response.
        """
        result = await self.get_user_provider(user_id, provider)
        
        if not result:
            raise BYOKExecutionError(
                "No BYOK provider configured",
                error_code="no_provider",
                is_retryable=False,
            )
        
        adapter, connection_info = result
        
        # Convert messages to BYOK format
        byok_messages = [
            ChatMessage(role=m["role"], content=m["content"])
            for m in messages
        ]
        
        try:
            # Stream request
            async for chunk in adapter.stream(
                messages=byok_messages,
                model=model or connection_info.get("model"),
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            ):
                yield chunk
        except ProviderError as e:
            raise BYOKExecutionError(
                str(e),
                error_code=e.error_code,
                is_retryable=e.is_retryable,
                provider=e.provider,
            )
        except Exception as e:
            raise BYOKExecutionError(
                f"Stream failed: {str(e)}",
                provider=connection_info.get("provider"),
            )
        finally:
            # Cleanup
            await adapter.close()


class BYOKRouter:
    """Router that selects between BYOK and system providers.
    
    This router:
    1. Checks if user has BYOK provider
    2. Uses BYOK if available
    3. Falls back to system providers
    4. Provides unified interface
    """
    
    def __init__(self, db: AsyncSession, system_llm_service: Any | None = None):
        """Initialize BYOK router.
        
        Args:
            db: Database session.
            system_llm_service: Optional system LLM service for fallback.
        """
        self._db = db
        self._byok_service = BYOKExecutionService(db)
        self._system_service = system_llm_service
    
    async def chat(
        self,
        user_id: uuid.UUID,
        messages: list[LLMMessage],
        provider: str | None = None,
        model: str | None = None,
        prefer_byok: bool = True,
        **kwargs,
    ) -> LLMResponse:
        """Send chat request with BYOK preference.
        
        Args:
            user_id: User's UUID.
            messages: Chat messages.
            provider: Preferred provider.
            model: Preferred model.
            prefer_byok: If True, prefer BYOK over system providers.
            
        Returns:
            LLMResponse from provider.
        """
        # Try BYOK first
        if prefer_byok:
            try:
                return await self._byok_service.chat(
                    user_id=user_id,
                    messages=messages,
                    provider=provider,
                    model=model,
                    **kwargs,
                )
            except BYOKExecutionError as e:
                if e.error_code == "no_provider":
                    # No BYOK configured, fall through to system
                    pass
                elif not e.is_retryable:
                    # Non-retryable error, raise immediately
                    raise
                else:
                    # Retryable error, try system as fallback
                    pass
        
        # Fall back to system providers
        if self._system_service:
            return await self._system_service.chat(
                messages=messages,
                provider=provider,
                model=model,
                **kwargs,
            )
        
        # No provider available
        raise BYOKExecutionError(
            "No LLM provider available",
            error_code="no_provider",
            is_retryable=False,
        )
    
    async def stream(
        self,
        user_id: uuid.UUID,
        messages: list[LLMMessage],
        provider: str | None = None,
        model: str | None = None,
        prefer_byok: bool = True,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream chat response with BYOK preference.
        
        Args:
            user_id: User's UUID.
            messages: Chat messages.
            provider: Preferred provider.
            model: Preferred model.
            prefer_byok: If True, prefer BYOK over system providers.
            
        Yields:
            String chunks from provider.
        """
        # Try BYOK first
        if prefer_byok:
            try:
                async for chunk in self._byok_service.stream(
                    user_id=user_id,
                    messages=messages,
                    provider=provider,
                    model=model,
                    **kwargs,
                ):
                    yield chunk
                return
            except BYOKExecutionError as e:
                if e.error_code == "no_provider":
                    pass
                elif not e.is_retryable:
                    raise
                # Retryable error, try system as fallback
        
        # Fall back to system providers
        if self._system_service:
            async for chunk in self._system_service.stream(
                messages=messages,
                provider=provider,
                model=model,
                **kwargs,
            ):
                yield chunk
            return
        
        raise BYOKExecutionError(
            "No LLM provider available",
            error_code="no_provider",
            is_retryable=False,
        )
    
    async def get_available_providers(
        self,
        user_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """Get all available providers for user.
        
        Args:
            user_id: User's UUID.
            
        Returns:
            List of provider info including BYOK and system.
        """
        providers = []
        
        # Add BYOK providers
        byok_connections = await self._service.list_connections(user_id, enabled_only=True)
        for conn in byok_connections:
            providers.append({
                "type": "byok",
                "provider": conn.provider,
                "id": str(conn.id),
                "nickname": conn.nickname,
                "is_default": conn.is_default,
                "verification_status": conn.verification_status,
            })
        
        # Add system providers (if configured)
        if self._system_service:
            system_providers = self._system_service.list_providers()
            for p in system_providers:
                providers.append({
                    "type": "system",
                    "provider": p["name"],
                    "model": p.get("model"),
                })
        
        return providers
