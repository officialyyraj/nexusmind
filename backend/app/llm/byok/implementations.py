"""BYOK Provider Implementations.

This module contains adapter implementations for all supported BYOK providers.
Each provider is a single self-contained adapter class.

Providers supported:
1. OpenAI
2. Anthropic
3. Google Gemini
4. Groq
5. OpenRouter
6. Together
7. DeepSeek
8. Mistral
9. xAI
10. Ollama (local)

Adding a new provider: Create new class, register with @register_provider decorator.
"""

from app.llm.byok.adapters import (
    BYOKProviderAdapter,
    ChatCompletion,
    ChatMessage,
    EmbeddingResult,
    ModelInfo,
    ProviderCapability,
    ProviderError,
    RateLimitError,
    VerificationResult,
    register_provider,
)


# ==================== OPENAI ====================

@register_provider(
    "openai",
    "OpenAI",
    website="https://openai.com",
    supported_models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
)
class OpenAIAdapter(BYOKProviderAdapter):
    """OpenAI API adapter."""
    
    provider_name = "openai"
    provider_display_name = "OpenAI"
    
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o"
    
    def __init__(self, api_key: str, base_url: str | None = None, **kwargs):
        base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, base_url, **kwargs)
    
    async def verify_key(self) -> VerificationResult:
        """Verify OpenAI API key."""
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                model_ids = [m["id"] for m in models[:10]]
                
                # Check rate limits
                remaining = response.headers.get("x-ratelimit-remaining-requests")
                
                return VerificationResult(
                    success=True,
                    message="API key verified successfully",
                    verified_models=model_ids,
                    rate_limit_remaining=int(remaining) if remaining else None,
                )
            elif response.status_code == 401:
                return VerificationResult(
                    success=False,
                    message="Invalid API key",
                    error_code="invalid_api_key",
                )
            else:
                return VerificationResult(
                    success=False,
                    message=f"Verification failed: {response.status_code}",
                )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Connection error: {str(e)}",
            )
    
    async def available_models(self) -> list[ModelInfo]:
        """Get available OpenAI models."""
        models = [
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                description="Flagship multimodal model",
                context_length=128_000,
                capabilities=[ProviderCapability.TOOLS, ProviderCapability.STREAMING, ProviderCapability.VISION],
                input_cost_per_1k=0.005,
                output_cost_per_1k=0.015,
                supports_tools=True,
                supports_vision=True,
            ),
            ModelInfo(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                description="Fast, affordable model",
                context_length=128_000,
                capabilities=[ProviderCapability.TOOLS, ProviderCapability.STREAMING],
                input_cost_per_1k=0.00015,
                output_cost_per_1k=0.0006,
                supports_tools=True,
            ),
            ModelInfo(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                description="Fast GPT-4 variant",
                context_length=128_000,
                capabilities=[ProviderCapability.TOOLS, ProviderCapability.STREAMING, ProviderCapability.VISION],
                input_cost_per_1k=0.01,
                output_cost_per_1k=0.03,
                supports_tools=True,
                supports_vision=True,
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                description="Fast, affordable model",
                context_length=16_385,
                capabilities=[ProviderCapability.TOOLS, ProviderCapability.STREAMING],
                input_cost_per_1k=0.0005,
                output_cost_per_1k=0.0015,
                supports_tools=True,
            ),
        ]
        return models
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """Send chat completion request."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Handle tools if provided
        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]
        
        response = await client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        
        if response.status_code != 200:
            self._handle_error(response)
        
        data = response.json()
        choice = data["choices"][0]
        
        return ChatCompletion(
            content=choice["message"]["content"],
            model=data["model"],
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    async def stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> list[str]:
        """Stream chat completion."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        async with client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        ) as response:
            if response.status_code != 200:
                self._handle_error(response)
            
            chunks = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json
                    chunk = json.loads(data)
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            chunks.append(delta["content"])
            
            return chunks
    
    def capabilities(self) -> list[ProviderCapability]:
        return [
            ProviderCapability.TOOLS,
            ProviderCapability.STREAMING,
            ProviderCapability.VISION,
            ProviderCapability.EMBEDDINGS,
        ]
    
    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL


# ==================== ANTHROPIC ====================

@register_provider(
    "anthropic",
    "Anthropic",
    website="https://anthropic.com",
    supported_models=["claude-sonnet-4", "claude-3-5-sonnet", "claude-3-haiku"],
)
class AnthropicAdapter(BYOKProviderAdapter):
    """Anthropic Claude API adapter."""
    
    provider_name = "anthropic"
    provider_display_name = "Anthropic"
    
    DEFAULT_BASE_URL = "https://api.anthropic.com"
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    
    def __init__(self, api_key: str, base_url: str | None = None, **kwargs):
        base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, base_url, **kwargs)
    
    async def verify_key(self) -> VerificationResult:
        """Verify Anthropic API key."""
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                json={
                    "model": self.DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 10,
                },
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
            )
            
            if response.status_code == 200:
                return VerificationResult(
                    success=True,
                    message="API key verified successfully",
                    verified_models=[self.DEFAULT_MODEL],
                )
            elif response.status_code == 401:
                return VerificationResult(
                    success=False,
                    message="Invalid API key",
                    error_code="invalid_api_key",
                )
            else:
                return VerificationResult(
                    success=False,
                    message=f"Verification failed: {response.status_code}",
                )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Connection error: {str(e)}",
            )
    
    async def available_models(self) -> list[ModelInfo]:
        """Get available Anthropic models."""
        return [
            ModelInfo(
                id="claude-sonnet-4-20250514",
                name="Claude Sonnet 4",
                description="Balanced model with strong reasoning",
                context_length=200_000,
                capabilities=[ProviderCapability.REASONING, ProviderCapability.TOOLS, ProviderCapability.STREAMING],
                input_cost_per_1k=0.003,
                output_cost_per_1k=0.015,
                supports_tools=True,
            ),
            ModelInfo(
                id="claude-3-5-sonnet-20241022",
                name="Claude 3.5 Sonnet",
                description="Best for coding and complex tasks",
                context_length=200_000,
                capabilities=[ProviderCapability.REASONING, ProviderCapability.TOOLS, ProviderCapability.STREAMING],
                input_cost_per_1k=0.003,
                output_cost_per_1k=0.015,
                supports_tools=True,
            ),
            ModelInfo(
                id="claude-3-5-haiku-20241022",
                name="Claude 3.5 Haiku",
                description="Fast, affordable model",
                context_length=200_000,
                capabilities=[ProviderCapability.STREAMING],
                input_cost_per_1k=0.0008,
                output_cost_per_1k=0.004,
            ),
        ]
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """Send chat completion request."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        # Anthropic uses different message format
        anthropic_messages = []
        system = ""
        
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                anthropic_messages.append({
                    "role": "user" if msg.role == "user" else "assistant",
                    "content": msg.content,
                })
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or 1024,
            "temperature": temperature,
        }
        if system:
            payload["system"] = system
        
        response = await client.post(
            f"{self.base_url}/v1/messages",
            json=payload,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        
        if response.status_code != 200:
            self._handle_error(response)
        
        data = response.json()
        
        return ChatCompletion(
            content=data["content"][0]["text"],
            model=data["model"],
            usage={
                "input_tokens": data["usage"]["input_tokens"],
                "output_tokens": data["usage"]["output_tokens"],
                "total_tokens": data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
            },
            finish_reason=data.get("stop_reason"),
            raw_response=data,
        )
    
    def capabilities(self) -> list[ProviderCapability]:
        return [
            ProviderCapability.REASONING,
            ProviderCapability.TOOLS,
            ProviderCapability.STREAMING,
        ]
    
    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL


# ==================== GOOGLE GEMINI ====================

@register_provider(
    "google",
    "Google Gemini",
    website="https://ai.google.dev",
    supported_models=["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
)
class GoogleAdapter(BYOKProviderAdapter):
    """Google Gemini API adapter."""
    
    provider_name = "google"
    provider_display_name = "Google Gemini"
    
    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com"
    DEFAULT_MODEL = "gemini-1.5-pro"
    
    def __init__(self, api_key: str, base_url: str | None = None, **kwargs):
        base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, base_url, **kwargs)
        self._api_key = api_key
    
    async def verify_key(self) -> VerificationResult:
        """Verify Google API key."""
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self.base_url}/v1beta/models",
                params={"key": self._api_key},
            )
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_ids = [m["name"].split("/")[-1] for m in models[:10]]
                
                return VerificationResult(
                    success=True,
                    message="API key verified successfully",
                    verified_models=model_ids,
                )
            elif response.status_code == 403:
                return VerificationResult(
                    success=False,
                    message="Invalid API key",
                    error_code="invalid_api_key",
                )
            else:
                return VerificationResult(
                    success=False,
                    message=f"Verification failed: {response.status_code}",
                )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Connection error: {str(e)}",
            )
    
    async def available_models(self) -> list[ModelInfo]:
        """Get available Gemini models."""
        return [
            ModelInfo(
                id="gemini-1.5-pro",
                name="Gemini 1.5 Pro",
                description="Most capable Gemini model",
                context_length=2_000_000,
                capabilities=[ProviderCapability.TOOLS, ProviderCapability.VISION, ProviderCapability.STREAMING],
                input_cost_per_1k=0.00125,
                output_cost_per_1k=0.005,
                supports_tools=True,
                supports_vision=True,
            ),
            ModelInfo(
                id="gemini-1.5-flash",
                name="Gemini 1.5 Flash",
                description="Fast, efficient model",
                context_length=1_000_000,
                capabilities=[ProviderCapability.TOOLS, ProviderCapability.VISION, ProviderCapability.STREAMING],
                input_cost_per_1k=0.000075,
                output_cost_per_1k=0.0003,
                supports_tools=True,
                supports_vision=True,
            ),
        ]
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """Send chat completion request."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            if msg.role != "system":
                contents.append({
                    "role": "model" if msg.role == "assistant" else "user",
                    "parts": [{"text": msg.content}],
                })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens or 2048,
            },
        }
        
        response = await client.post(
            f"{self.base_url}/v1beta/models/{model}:generateContent",
            json=payload,
            params={"key": self._api_key},
        )
        
        if response.status_code != 200:
            self._handle_error(response)
        
        data = response.json()
        
        return ChatCompletion(
            content=data["candidates"][0]["content"]["parts"][0]["text"],
            model=model,
            usage={
                "prompt_tokens": data.get("usageMetadata", {}).get("promptTokenCount", 0),
                "completion_tokens": data.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                "total_tokens": data.get("usageMetadata", {}).get("totalTokenCount", 0),
            },
            raw_response=data,
        )
    
    def capabilities(self) -> list[ProviderCapability]:
        return [
            ProviderCapability.TOOLS,
            ProviderCapability.VISION,
            ProviderCapability.STREAMING,
        ]
    
    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL


# ==================== GROQ ====================

@register_provider(
    "groq",
    "Groq",
    website="https://console.groq.com",
    supported_models=["llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
)
class GroqAdapter(BYOKProviderAdapter):
    """Groq API adapter (OpenAI-compatible)."""
    
    provider_name = "groq"
    provider_display_name = "Groq"
    
    DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
    DEFAULT_MODEL = "llama-3.1-70b-versatile"
    
    def __init__(self, api_key: str, base_url: str | None = None, **kwargs):
        base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, base_url, **kwargs)
    
    async def verify_key(self) -> VerificationResult:
        """Verify Groq API key."""
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                model_ids = [m["id"] for m in models[:10]]
                
                return VerificationResult(
                    success=True,
                    message="API key verified successfully",
                    verified_models=model_ids,
                )
            elif response.status_code == 401:
                return VerificationResult(
                    success=False,
                    message="Invalid API key",
                    error_code="invalid_api_key",
                )
            else:
                return VerificationResult(
                    success=False,
                    message=f"Verification failed: {response.status_code}",
                )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Connection error: {str(e)}",
            )
    
    async def available_models(self) -> list[ModelInfo]:
        """Get available Groq models."""
        return [
            ModelInfo(
                id="llama-3.1-70b-versatile",
                name="Llama 3.1 70B",
                description="Fast, versatile model",
                context_length=128_000,
                capabilities=[ProviderCapability.STREAMING],
                input_cost_per_1k=0.00059,
                output_cost_per_1k=0.00079,
            ),
            ModelInfo(
                id="mixtral-8x7b-32768",
                name="Mixtral 8x7B",
                description="Fast mixture of experts",
                context_length=32_768,
                capabilities=[ProviderCapability.STREAMING],
            ),
        ]
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """Send chat completion request."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = await client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        
        if response.status_code != 200:
            self._handle_error(response)
        
        data = response.json()
        choice = data["choices"][0]
        
        return ChatCompletion(
            content=choice["message"]["content"],
            model=data["model"],
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.STREAMING]
    
    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL


# ==================== OPENROUTER ====================

@register_provider(
    "openrouter",
    "OpenRouter",
    website="https://openrouter.ai",
    supported_models=[],  # Dynamic - many models available
)
class OpenRouterAdapter(BYOKProviderAdapter):
    """OpenRouter API adapter (aggregates many providers)."""
    
    provider_name = "openrouter"
    provider_display_name = "OpenRouter"
    
    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"
    
    def __init__(self, api_key: str, base_url: str | None = None, **kwargs):
        base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, base_url, **kwargs)
    
    async def verify_key(self) -> VerificationResult:
        """Verify OpenRouter API key."""
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self.base_url}/auth/key",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            
            if response.status_code == 200:
                data = response.json()
                return VerificationResult(
                    success=True,
                    message="API key verified successfully",
                    quota_info={
                        "remaining": data.get("usage", {}).get("remaining"),
                        "limit": data.get("usage", {}).get("limit"),
                    },
                )
            elif response.status_code == 401:
                return VerificationResult(
                    success=False,
                    message="Invalid API key",
                    error_code="invalid_api_key",
                )
            else:
                return VerificationResult(
                    success=False,
                    message=f"Verification failed: {response.status_code}",
                )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Connection error: {str(e)}",
            )
    
    async def available_models(self) -> list[ModelInfo]:
        """Get available OpenRouter models."""
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            
            if response.status_code == 200:
                models_data = response.json().get("data", [])
                models = []
                for m in models_data[:20]:
                    models.append(ModelInfo(
                        id=m["id"],
                        name=m.get("name", m["id"]),
                        description=m.get("description", ""),
                        context_length=m.get("context_length", 128_000),
                        input_cost_per_1k=m.get("pricing", {}).get("prompt", 0) * 1_000_000,
                        output_cost_per_1k=m.get("pricing", {}).get("completion", 0) * 1_000_000,
                    ))
                return models
        except Exception:
            pass
        
        # Fallback to common models
        return [
            ModelInfo(
                id="anthropic/claude-3.5-sonnet",
                name="Claude 3.5 Sonnet (via OR)",
                description="Aggregated by OpenRouter",
                context_length=200_000,
            ),
        ]
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """Send chat completion request."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = await client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://nexusmind.ai",
                "X-Title": "NexusMind",
            },
        )
        
        if response.status_code != 200:
            self._handle_error(response)
        
        data = response.json()
        choice = data["choices"][0]
        
        return ChatCompletion(
            content=choice["message"]["content"],
            model=data["model"],
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.STREAMING, ProviderCapability.TOOLS]
    
    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL


# ==================== TOGETHER ====================

@register_provider(
    "together",
    "Together AI",
    website="https://together.ai",
    supported_models=["meta-llama/Llama-3-70b-chat-hf", "mistralai/Mixtral-8x7B-Instruct-v0.1"],
)
class TogetherAdapter(BYOKProviderAdapter):
    """Together AI API adapter."""
    
    provider_name = "together"
    provider_display_name = "Together AI"
    
    DEFAULT_BASE_URL = "https://api.together.xyz/v1"
    DEFAULT_MODEL = "meta-llama/Llama-3-70b-chat-hf"
    
    def __init__(self, api_key: str, base_url: str | None = None, **kwargs):
        base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, base_url, **kwargs)
    
    async def verify_key(self) -> VerificationResult:
        """Verify Together AI API key."""
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                model_ids = [m["id"] for m in models[:10]]
                
                return VerificationResult(
                    success=True,
                    message="API key verified successfully",
                    verified_models=model_ids,
                )
            elif response.status_code == 401:
                return VerificationResult(
                    success=False,
                    message="Invalid API key",
                    error_code="invalid_api_key",
                )
            else:
                return VerificationResult(
                    success=False,
                    message=f"Verification failed: {response.status_code}",
                )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Connection error: {str(e)}",
            )
    
    async def available_models(self) -> list[ModelInfo]:
        """Get available Together models."""
        return [
            ModelInfo(
                id="meta-llama/Llama-3-70b-chat-hf",
                name="Llama 3 70B",
                description="Powerful open model",
                context_length=128_000,
                capabilities=[ProviderCapability.STREAMING],
                input_cost_per_1k=0.0009,
                output_cost_per_1k=0.0009,
            ),
            ModelInfo(
                id="mistralai/Mixtral-8x7B-Instruct-v0.1",
                name="Mixtral 8x7B",
                description="Fast mixture of experts",
                context_length=32_768,
                capabilities=[ProviderCapability.STREAMING],
            ),
        ]
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """Send chat completion request."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = await client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        
        if response.status_code != 200:
            self._handle_error(response)
        
        data = response.json()
        choice = data["choices"][0]
        
        return ChatCompletion(
            content=choice["message"]["content"],
            model=data["model"],
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.STREAMING]
    
    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL


# ==================== DEEPSEEK ====================

@register_provider(
    "deepseek",
    "DeepSeek",
    website="https://platform.deepseek.com",
    supported_models=["deepseek-chat", "deepseek-coder"],
)
class DeepSeekAdapter(BYOKProviderAdapter):
    """DeepSeek API adapter."""
    
    provider_name = "deepseek"
    provider_display_name = "DeepSeek"
    
    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"
    
    def __init__(self, api_key: str, base_url: str | None = None, **kwargs):
        base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, base_url, **kwargs)
    
    async def verify_key(self) -> VerificationResult:
        """Verify DeepSeek API key."""
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 10,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            
            if response.status_code == 200:
                return VerificationResult(
                    success=True,
                    message="API key verified successfully",
                    verified_models=[self.DEFAULT_MODEL],
                )
            elif response.status_code == 401:
                return VerificationResult(
                    success=False,
                    message="Invalid API key",
                    error_code="invalid_api_key",
                )
            else:
                return VerificationResult(
                    success=False,
                    message=f"Verification failed: {response.status_code}",
                )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Connection error: {str(e)}",
            )
    
    async def available_models(self) -> list[ModelInfo]:
        """Get available DeepSeek models."""
        return [
            ModelInfo(
                id="deepseek-chat",
                name="DeepSeek Chat",
                description="General purpose chat model",
                context_length=128_000,
                capabilities=[ProviderCapability.STREAMING, ProviderCapability.TOOLS],
                input_cost_per_1k=0.00027,
                output_cost_per_1k=0.0011,
            ),
            ModelInfo(
                id="deepseek-coder",
                name="DeepSeek Coder",
                description="Specialized for code",
                context_length=128_000,
                capabilities=[ProviderCapability.STREAMING],
            ),
        ]
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """Send chat completion request."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = await client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        
        if response.status_code != 200:
            self._handle_error(response)
        
        data = response.json()
        choice = data["choices"][0]
        
        return ChatCompletion(
            content=choice["message"]["content"],
            model=data["model"],
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.STREAMING, ProviderCapability.TOOLS]
    
    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL


# ==================== MISTRAL ====================

@register_provider(
    "mistral",
    "Mistral AI",
    website="https://mistral.ai",
    supported_models=["mistral-large-latest", "mistral-small-latest", "codestral-latest"],
)
class MistralAdapter(BYOKProviderAdapter):
    """Mistral AI API adapter."""
    
    provider_name = "mistral"
    provider_display_name = "Mistral AI"
    
    DEFAULT_BASE_URL = "https://api.mistral.ai/v1"
    DEFAULT_MODEL = "mistral-large-latest"
    
    def __init__(self, api_key: str, base_url: str | None = None, **kwargs):
        base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, base_url, **kwargs)
    
    async def verify_key(self) -> VerificationResult:
        """Verify Mistral API key."""
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 10,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            
            if response.status_code == 200:
                return VerificationResult(
                    success=True,
                    message="API key verified successfully",
                    verified_models=[self.DEFAULT_MODEL],
                )
            elif response.status_code == 401:
                return VerificationResult(
                    success=False,
                    message="Invalid API key",
                    error_code="invalid_api_key",
                )
            else:
                return VerificationResult(
                    success=False,
                    message=f"Verification failed: {response.status_code}",
                )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Connection error: {str(e)}",
            )
    
    async def available_models(self) -> list[ModelInfo]:
        """Get available Mistral models."""
        return [
            ModelInfo(
                id="mistral-large-latest",
                name="Mistral Large",
                description="Most capable Mistral model",
                context_length=128_000,
                capabilities=[ProviderCapability.STREAMING, ProviderCapability.TOOLS],
                input_cost_per_1k=0.002,
                output_cost_per_1k=0.006,
            ),
            ModelInfo(
                id="mistral-small-latest",
                name="Mistral Small",
                description="Fast, affordable model",
                context_length=128_000,
                capabilities=[ProviderCapability.STREAMING],
                input_cost_per_1k=0.0002,
                output_cost_per_1k=0.0006,
            ),
        ]
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """Send chat completion request."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = await client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        
        if response.status_code != 200:
            self._handle_error(response)
        
        data = response.json()
        choice = data["choices"][0]
        
        return ChatCompletion(
            content=choice["message"]["content"],
            model=data["model"],
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.STREAMING, ProviderCapability.TOOLS]
    
    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL


# ==================== XAI ====================

@register_provider(
    "xai",
    "xAI",
    website="https://x.ai",
    supported_models=["grok-2", "grok-2-mini"],
)
class XAIAdapter(BYOKProviderAdapter):
    """xAI Grok API adapter."""
    
    provider_name = "xai"
    provider_display_name = "xAI"
    
    DEFAULT_BASE_URL = "https://api.x.ai/v1"
    DEFAULT_MODEL = "grok-2"
    
    def __init__(self, api_key: str, base_url: str | None = None, **kwargs):
        base_url = base_url or self.DEFAULT_BASE_URL
        super().__init__(api_key, base_url, **kwargs)
    
    async def verify_key(self) -> VerificationResult:
        """Verify xAI API key."""
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 10,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            
            if response.status_code == 200:
                return VerificationResult(
                    success=True,
                    message="API key verified successfully",
                    verified_models=[self.DEFAULT_MODEL],
                )
            elif response.status_code == 401:
                return VerificationResult(
                    success=False,
                    message="Invalid API key",
                    error_code="invalid_api_key",
                )
            else:
                return VerificationResult(
                    success=False,
                    message=f"Verification failed: {response.status_code}",
                )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Connection error: {str(e)}",
            )
    
    async def available_models(self) -> list[ModelInfo]:
        """Get available xAI models."""
        return [
            ModelInfo(
                id="grok-2",
                name="Grok 2",
                description="Most capable xAI model",
                context_length=131_072,
                capabilities=[ProviderCapability.STREAMING, ProviderCapability.TOOLS],
            ),
            ModelInfo(
                id="grok-2-mini",
                name="Grok 2 Mini",
                description="Fast, efficient model",
                context_length=131_072,
                capabilities=[ProviderCapability.STREAMING],
            ),
        ]
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """Send chat completion request."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = await client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        
        if response.status_code != 200:
            self._handle_error(response)
        
        data = response.json()
        choice = data["choices"][0]
        
        return ChatCompletion(
            content=choice["message"]["content"],
            model=data["model"],
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.STREAMING, ProviderCapability.TOOLS]
    
    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL


# ==================== OLLAMA (LOCAL) ====================

@register_provider(
    "ollama",
    "Ollama (Local)",
    website="https://ollama.ai",
    supported_models=[],  # Dynamic - discovered from server
)
class OllamaAdapter(BYOKProviderAdapter):
    """Ollama local API adapter."""
    
    provider_name = "ollama"
    provider_display_name = "Ollama (Local)"
    
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.2"
    
    def __init__(self, api_key: str | None = None, base_url: str | None = None, **kwargs):
        # Ollama doesn't need API key by default
        super().__init__(api_key or "", base_url, **kwargs)
    
    async def verify_key(self) -> VerificationResult:
        """Verify Ollama connection."""
        client = await self._get_client()
        try:
            response = await client.get(f"{self.base_url}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                model_names = [m["name"] for m in data.get("models", [])]
                
                return VerificationResult(
                    success=True,
                    message="Ollama connection successful",
                    verified_models=model_names,
                )
            else:
                return VerificationResult(
                    success=False,
                    message=f"Connection failed: {response.status_code}",
                )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Connection error: {str(e)}",
            )
    
    async def available_models(self) -> list[ModelInfo]:
        """Get available Ollama models."""
        client = await self._get_client()
        try:
            response = await client.get(f"{self.base_url}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = []
                for m in data.get("models", []):
                    models.append(ModelInfo(
                        id=m["name"],
                        name=m["name"],
                        description=f"Local model: {m['name']}",
                        context_length=m.get("details", {}).get("context_length", 4096) or 4096,
                    ))
                return models
        except Exception:
            pass
        
        return [ModelInfo(id="llama3.2", name="Llama 3.2", description="Default Ollama model")]
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """Send chat completion request."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        response = await client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        
        if response.status_code != 200:
            raise ProviderError(f"Ollama request failed: {response.status_code}", provider="ollama")
        
        data = response.json()
        
        return ChatCompletion(
            content=data["message"]["content"],
            model=data["model"],
            usage={
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "eval_count": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            },
            finish_reason=data.get("done_reason"),
            raw_response=data,
        )
    
    async def stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> list[str]:
        """Stream chat completion."""
        client = await self._get_client()
        model = model or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        chunks = []
        async with client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload,
        ) as response:
            if response.status_code != 200:
                raise ProviderError(f"Ollama request failed: {response.status_code}", provider="ollama")
            
            async for line in response.aiter_lines():
                if line:
                    import json
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        chunks.append(chunk["message"]["content"])
        
        return chunks
    
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.STREAMING]
    
    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL
