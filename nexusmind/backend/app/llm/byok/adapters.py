"""BYOK Provider Adapters - Extended LLM Provider Interface.

This module defines the canonical interface for BYOK (Bring Your Own Key)
provider adapters. Every provider must implement this interface to ensure
consistent behavior across all supported providers.

No switch statements allowed. Adding provider N+1 requires only one new adapter.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator

import httpx


class ProviderCapability(str, Enum):
    """Provider capabilities."""
    
    TOOLS = "tools"           # Function calling / tool use
    STREAMING = "streaming"   # Streaming responses
    VISION = "vision"         # Image understanding
    REASONING = "reasoning"  # Advanced reasoning (CoT, etc.)
    FUNCTION_CALLING = "function_calling"  # Explicit function calling
    EMBEDDINGS = "embeddings"  # Text embeddings
    IMAGE_GENERATION = "image_generation"  # Image creation


@dataclass
class ModelInfo:
    """Information about a model from a provider."""
    
    id: str                          # Model identifier
    name: str                        # Display name
    description: str = ""            # Model description
    context_length: int = 128_000     # Context window size
    capabilities: list[ProviderCapability] = field(default_factory=list)
    input_cost_per_1k: float = 0.0    # Cost per 1K input tokens
    output_cost_per_1k: float = 0.0   # Cost per 1K output tokens
    max_output_tokens: int | None = None
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_vision: bool = False


@dataclass
class VerificationResult:
    """Result of API key verification."""
    
    success: bool
    message: str = ""
    verified_models: list[str] = field(default_factory=list)
    rate_limit_remaining: int | None = None
    quota_info: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ChatMessage:
    """Chat message format."""
    
    role: str      # system, user, assistant
    content: str


@dataclass
class ChatCompletion:
    """Chat completion response."""
    
    content: str
    model: str
    usage: dict[str, int]  # input_tokens, output_tokens, total_tokens
    finish_reason: str | None = None
    raw_response: dict[str, Any] | None = None


@dataclass
class EmbeddingResult:
    """Text embedding response."""
    
    embeddings: list[list[float]]
    model: str
    usage: dict[str, int]


class ProviderError(Exception):
    """Base exception for provider errors."""
    
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


class InvalidAPIKeyError(ProviderError):
    """API key is invalid."""
    
    def __init__(self, message: str = "Invalid API key", provider: str | None = None):
        super().__init__(
            message=message,
            error_code="invalid_api_key",
            is_retryable=False,
            provider=provider,
        )


class ExpiredAPIKeyError(ProviderError):
    """API key has expired."""
    
    def __init__(self, message: str = "API key has expired", provider: str | None = None):
        super().__init__(
            message=message,
            error_code="expired_api_key",
            is_retryable=False,
            provider=provider,
        )


class QuotaExceededError(ProviderError):
    """Provider quota exceeded."""
    
    def __init__(self, message: str = "Quota exceeded", provider: str | None = None):
        super().__init__(
            message=message,
            error_code="quota_exceeded",
            is_retryable=True,
            provider=provider,
        )


class RateLimitError(ProviderError):
    """Provider rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None, provider: str | None = None):
        super().__init__(
            message=message,
            error_code="rate_limit",
            is_retryable=True,
            provider=provider,
        )
        self.retry_after = retry_after


class ProviderOfflineError(ProviderError):
    """Provider service is offline."""
    
    def __init__(self, message: str = "Provider offline", provider: str | None = None):
        super().__init__(
            message=message,
            error_code="provider_offline",
            is_retryable=True,
            provider=provider,
        )


class TimeoutError(ProviderError):
    """Request timed out."""
    
    def __init__(self, message: str = "Request timed out", provider: str | None = None):
        super().__init__(
            message=message,
            error_code="timeout",
            is_retryable=True,
            provider=provider,
        )


class BYOKProviderAdapter(ABC):
    """Abstract base class for BYOK provider adapters.
    
    Every BYOK provider must implement this interface.
    Adding a new provider requires ONLY creating a new adapter class.
    No modifications to other files required.
    
    Required Methods:
    - verify_key(): Verify API key is valid
    - available_models(): List available models
    - chat(): Send chat completion
    - embeddings(): Generate embeddings
    - capabilities(): Get provider capabilities
    
    Optional Methods:
    - stream(): Stream chat completion
    - image_generation(): Generate images
    """
    
    # Class-level provider identifier
    provider_name: str = "unknown"
    provider_display_name: str = "Unknown Provider"
    
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 120.0,
        **kwargs,
    ):
        """Initialize the provider adapter.
        
        Args:
            api_key: The API key (will be decrypted before use).
            base_url: Optional custom base URL for API.
            timeout: Request timeout in seconds.
            **kwargs: Additional provider-specific configuration.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.extra_config = kwargs
        
        # Initialize HTTP client
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._get_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    # ==================== REQUIRED METHODS ====================
    
    @abstractmethod
    async def verify_key(self) -> VerificationResult:
        """Verify the API key is valid and get provider info.
        
        This method should:
        1. Make a minimal API call to verify the key
        2. Return available models or quota info
        3. Handle all error cases appropriately
        
        Returns:
            VerificationResult with success status and details.
        """
        pass
    
    @abstractmethod
    async def available_models(self) -> list[ModelInfo]:
        """Get list of available models.
        
        Returns:
            List of ModelInfo objects.
        """
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """Send a chat completion request.
        
        Args:
            messages: List of chat messages.
            model: Model to use (uses default if None).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            **kwargs: Additional provider-specific parameters.
            
        Returns:
            ChatCompletion response.
        """
        pass
    
    async def embeddings(
        self,
        texts: list[str],
        model: str | None = None,
        **kwargs,
    ) -> EmbeddingResult:
        """Generate embeddings for texts.
        
        Default implementation calls the chat endpoint with a simple prompt.
        Override for providers with native embedding support.
        
        Args:
            texts: List of texts to embed.
            model: Embedding model to use.
            
        Returns:
            EmbeddingResult with embeddings.
        """
        raise NotImplementedError(f"{self.provider_name} does not support embeddings")
    
    def capabilities(self) -> list[ProviderCapability]:
        """Get list of provider capabilities.
        
        Returns:
            List of supported capabilities.
        """
        return []
    
    # ==================== OPTIONAL METHODS ====================
    
    async def stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat completion response.
        
        Override for providers with native streaming support.
        
        Args:
            messages: List of chat messages.
            model: Model to use.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.
            
        Yields:
            String chunks of the response.
        """
        # Default: non-streaming and yield full response
        completion = await self.chat(messages, model, temperature, max_tokens, **kwargs)
        yield completion.content
    
    # ==================== HELPER METHODS ====================
    
    def _handle_error(self, response: httpx.Response, provider: str | None = None) -> None:
        """Handle HTTP error responses.
        
        Args:
            response: The error response.
            provider: Provider name for error context.
            
        Raises:
            ProviderError subclass appropriate for the error.
        """
        provider = provider or self.provider_name
        
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", response.text)
            error_type = error_data.get("error", {}).get("type", "")
        except Exception:
            error_message = response.text or "Unknown error"
            error_type = ""
        
        # Map provider-specific errors to our error types
        status_code = response.status_code
        
        if status_code == 401 or "invalid" in error_type.lower():
            raise InvalidAPIKeyError(error_message, provider)
        
        if status_code == 403 or "expired" in error_type.lower():
            raise ExpiredAPIKeyError(error_message, provider)
        
        if status_code == 429:
            retry_after = None
            if "retry-after" in response.headers:
                try:
                    retry_after = int(response.headers["retry-after"])
                except ValueError:
                    pass
            raise RateLimitError(error_message, retry_after, provider)
        
        if status_code >= 500:
            raise ProviderOfflineError(f"Provider error: {error_message}", provider)
        
        if "quota" in error_message.lower() or "limit" in error_message.lower():
            raise QuotaExceededError(error_message, provider)
        
        raise ProviderError(error_message, provider=provider)
    
    def _format_messages(self, messages: list[ChatMessage]) -> list[dict[str, str]]:
        """Format messages for API request.
        
        Args:
            messages: List of ChatMessage objects.
            
        Returns:
            List of dicts for API.
        """
        return [{"role": m.role, "content": m.content} for m in messages]
    
    @property
    def default_model(self) -> str:
        """Get the default model for this provider."""
        return "default"


class ProviderAdapterRegistry:
    """Registry for BYOK provider adapters.
    
    This registry allows dynamic provider lookup without switch statements.
    Adding a new provider: RegisterAdapter(MyNewProviderAdapter)
    Using a provider: registry.get("openai").verify_key()
    """
    
    def __init__(self):
        self._adapters: dict[str, type[BYOKProviderAdapter]] = {}
        self._provider_info: dict[str, dict[str, Any]] = {}
    
    def register(
        self,
        provider_name: str,
        adapter_class: type[BYOKProviderAdapter],
        display_name: str,
        website: str | None = None,
        logo_url: str | None = None,
        supported_models: list[str] | None = None,
    ) -> None:
        """Register a provider adapter.
        
        Args:
            provider_name: Unique identifier (e.g., "openai").
            adapter_class: The adapter class.
            display_name: Human-readable name.
            website: Provider website URL.
            logo_url: URL to provider logo.
            supported_models: Default list of supported models.
        """
        self._adapters[provider_name.lower()] = adapter_class
        self._provider_info[provider_name.lower()] = {
            "name": provider_name,
            "display_name": display_name,
            "website": website,
            "logo_url": logo_url,
            "supported_models": supported_models or [],
        }
    
    def get(self, provider_name: str) -> type[BYOKProviderAdapter] | None:
        """Get adapter class by provider name.
        
        Args:
            provider_name: Provider identifier.
            
        Returns:
            Adapter class or None if not found.
        """
        return self._adapters.get(provider_name.lower())
    
    def create_adapter(
        self,
        provider_name: str,
        api_key: str,
        base_url: str | None = None,
        **kwargs,
    ) -> BYOKProviderAdapter | None:
        """Create an adapter instance.
        
        Args:
            provider_name: Provider identifier.
            api_key: API key.
            base_url: Optional custom base URL.
            **kwargs: Additional configuration.
            
        Returns:
            Adapter instance or None if provider not found.
        """
        adapter_class = self.get(provider_name)
        if not adapter_class:
            return None
        
        return adapter_class(api_key=api_key, base_url=base_url, **kwargs)
    
    def list_providers(self) -> list[dict[str, Any]]:
        """List all registered providers.
        
        Returns:
            List of provider info dicts.
        """
        return list(self._provider_info.values())
    
    def has_provider(self, provider_name: str) -> bool:
        """Check if provider is registered.
        
        Args:
            provider_name: Provider identifier.
            
        Returns:
            True if registered.
        """
        return provider_name.lower() in self._adapters


# Global registry instance
_provider_registry = ProviderAdapterRegistry()


def get_provider_registry() -> ProviderAdapterRegistry:
    """Get the global provider registry."""
    return _provider_registry


def register_provider(
    provider_name: str,
    display_name: str,
    website: str | None = None,
    logo_url: str | None = None,
    supported_models: list[str] | None = None,
) -> callable:
    """Decorator to register a provider adapter.
    
    Usage:
        @register_provider("openai", "OpenAI", website="https://openai.com")
        class OpenAIAdapter(BYOKProviderAdapter):
            ...
    """
    def decorator(cls: type[BYOKProviderAdapter]) -> type[BYOKProviderAdapter]:
        _provider_registry.register(
            provider_name,
            cls,
            display_name,
            website,
            logo_url,
            supported_models,
        )
        return cls
    return decorator
