"""BYOK (Bring Your Own AI Provider) Module.

This module provides enterprise-grade BYOK functionality:
- Provider adapters for 10+ AI providers
- AES-256-GCM encryption for API keys
- Per-user provider management
- Rate limiting and audit logging
- Per-user execution with BYOK providers
"""

# Import adapters to trigger registration
from app.llm.byok.adapters import (
    BYOKProviderAdapter,
    ChatCompletion,
    ChatMessage,
    EmbeddingResult,
    ModelInfo,
    ProviderAdapterRegistry,
    ProviderCapability,
    ProviderError,
    RateLimitError,
    VerificationResult,
    get_provider_registry,
    register_provider,
)

# Import implementations to register them
from app.llm.byok import implementations

# Import executor for BYOK execution
from app.llm.byok.executor import (
    BYOKExecutionService,
    BYOKExecutionError,
    BYOKRouter,
)

# Import service for CRUD operations
from app.llm.byok.service import (
    ProviderService,
    ProviderServiceError,
    ProviderNotFoundError,
    ProviderLimitExceededError,
    DuplicateProviderError,
)

__all__ = [
    # Adapters
    "BYOKProviderAdapter",
    "ChatCompletion",
    "ChatMessage",
    "EmbeddingResult",
    "ModelInfo",
    "ProviderAdapterRegistry",
    "ProviderCapability",
    "ProviderError",
    "RateLimitError",
    "VerificationResult",
    # Utilities
    "get_provider_registry",
    "register_provider",
    # Executor
    "BYOKExecutionService",
    "BYOKExecutionError",
    "BYOKRouter",
    # Service
    "ProviderService",
    "ProviderServiceError",
    "ProviderNotFoundError",
    "ProviderLimitExceededError",
    "DuplicateProviderError",
    # Submodules
    "implementations",
    "executor",
    "service",
]
