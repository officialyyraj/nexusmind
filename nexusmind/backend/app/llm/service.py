"""LLM Service for managing providers and completions."""

from typing import Any, AsyncIterator

from app.config import get_settings
from app.llm.providers import (
    AnthropicProvider,
    LLMManager,
    LLMMessage,
    LLMResponse,
    OllamaProvider,
    OpenAICompatibleProvider,
)


class LLMService:
    """Service for LLM interactions."""

    def __init__(self):
        self._manager = LLMManager()
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize default providers from settings."""
        settings = get_settings()

        # Ollama provider
        if settings.ollama_base_url:
            self._manager.register_provider(
                "ollama",
                OllamaProvider(
                    base_url=settings.ollama_base_url,
                    model=settings.ollama_default_model,
                ),
                set_default=True,
            )

        # OpenAI provider
        if settings.openai_api_key:
            self._manager.register_provider(
                "openai",
                OpenAICompatibleProvider(
                    base_url=settings.openai_base_url,
                    api_key=settings.openai_api_key,
                    model="gpt-4",
                ),
            )

        # Anthropic provider
        if settings.anthropic_api_key:
            self._manager.register_provider(
                "anthropic",
                AnthropicProvider(
                    api_key=settings.anthropic_api_key,
                ),
            )

    async def chat(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat completion request."""
        llm_messages: list[LLMMessage] = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ]
        return await self._manager.chat(llm_messages, provider, model=model, **kwargs)

    async def stream(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat completion."""
        llm_messages: list[LLMMessage] = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ]
        async for chunk in self._manager.stream(llm_messages, provider, model=model, **kwargs):
            yield chunk

    def list_providers(self) -> list[dict[str, Any]]:
        """List all available providers."""
        return self._manager.list_providers()

    def get_provider(self, name: str) -> dict[str, Any] | None:
        """Get provider info."""
        for p in self.list_providers():
            if p["name"] == name:
                return p
        return None


# Global LLM service instance
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get the global LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
