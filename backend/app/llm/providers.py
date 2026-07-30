"""LLM Provider implementations."""

import json
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, TypedDict

import httpx


class LLMMessage(TypedDict):
    """LLM message format."""
    role: str
    content: str


class LLMResponse(TypedDict):
    """LLM response format."""
    content: str
    model: str
    usage: dict[str, int]
    finish_reason: str | None


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, base_url: str, api_key: str | None = None, model: str = "default", **kwargs):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.extra_config = kwargs

    @abstractmethod
    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        pass

    @abstractmethod
    async def stream(self, messages: list[LLMMessage], **kwargs) -> AsyncIterator[str]:
        pass

    @abstractmethod
    async def list_models(self) -> list[dict[str, Any]]:
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2", **kwargs):
        super().__init__(base_url, api_key=None, model=model, **kwargs)

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={"model": kwargs.get("model", self.model), "messages": messages, "stream": False},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "content": data["message"]["content"],
                "model": data["model"],
                "usage": {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                },
                "finish_reason": "stop",
            }

    async def stream(self, messages: list[LLMMessage], **kwargs) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", f"{self.base_url}/api/chat",
                json={"model": kwargs.get("model", self.model), "messages": messages, "stream": True},
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data:
                            yield data["message"]["content"]

    async def list_models(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [{"name": m["name"], "model": m["name"]} for m in data.get("models", [])]


class OpenAICompatibleProvider(BaseLLMProvider):
    """OpenAI-compatible LLM provider."""

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json={"model": kwargs.get("model", self.model), "messages": messages, "stream": False},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]
            return {
                "content": choice["message"]["content"],
                "model": data["model"],
                "usage": data.get("usage", {}),
                "finish_reason": choice.get("finish_reason"),
            }

    async def stream(self, messages: list[LLMMessage], **kwargs) -> AsyncIterator[str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", f"{self.base_url}/chat/completions",
                json={"model": kwargs.get("model", self.model), "messages": messages, "stream": True},
                headers=headers,
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]

    async def list_models(self) -> list[dict[str, Any]]:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/models", headers=headers)
            if response.status_code == 200:
                return response.json().get("data", [])
            return []


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, base_url: str = "https://api.anthropic.com", api_key: str | None = None,
                 model: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(base_url, api_key, model, **kwargs)

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Anthropic API key required")

        system = ""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                anthropic_messages.append({"role": "user" if msg["role"] == "user" else "assistant", "content": msg["content"]})

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                json={"model": kwargs.get("model", self.model), "messages": anthropic_messages, "system": system, "max_tokens": kwargs.get("max_tokens", 1024)},
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "content": data["content"][0]["text"],
                "model": data["model"],
                "usage": {"input_tokens": data["usage"]["input_tokens"], "output_tokens": data["usage"]["output_tokens"]},
                "finish_reason": data.get("stop_reason"),
            }

    async def stream(self, messages: list[LLMMessage], **kwargs) -> AsyncIterator[str]:
        result = await self.chat(messages, **kwargs)
        yield result["content"]

    async def list_models(self) -> list[dict[str, Any]]:
        return [{"name": "claude-3-5-sonnet-20241022"}, {"name": "claude-3-opus-20240229"}, {"name": "claude-3-haiku-20240307"}]


class LLMManager:
    """Manager for LLM providers."""

    def __init__(self):
        self._providers: dict[str, BaseLLMProvider] = {}
        self._default_provider: str | None = None

    def register_provider(self, name: str, provider: BaseLLMProvider, set_default: bool = False) -> None:
        self._providers[name] = provider
        if set_default or self._default_provider is None:
            self._default_provider = name

    def get_provider(self, name: str | None = None) -> BaseLLMProvider:
        if name is None:
            name = self._default_provider
        if name is None:
            raise ValueError("No LLM provider registered")
        provider = self._providers.get(name)
        if provider is None:
            raise ValueError(f"Unknown provider: {name}")
        return provider

    async def chat(self, messages: list[LLMMessage], provider: str | None = None, **kwargs) -> LLMResponse:
        return await self.get_provider(provider).chat(messages, **kwargs)

    async def stream(self, messages: list[LLMMessage], provider: str | None = None, **kwargs) -> AsyncIterator[str]:
        async for chunk in self.get_provider(provider).stream(messages, **kwargs):
            yield chunk

    def list_providers(self) -> list[dict[str, Any]]:
        return [{"name": name, "model": p.model, "base_url": p.base_url} for name, p in self._providers.items()]
