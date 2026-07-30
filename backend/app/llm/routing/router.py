"""Intelligent model routing."""

import time
from datetime import datetime
from typing import Any

from app.agents.types import AgentType
from app.llm.routing.schemas import (
    ModelCapability,
    ModelConfig,
    ModelInfo,
    ProviderType,
    RouteRequest,
    RouteResult,
    RoutingMetrics,
    RoutingRule,
    TaskType,
)


# Default model catalog
DEFAULT_MODELS = [
    # Ollama models
    ModelInfo(
        name="llama3.2",
        provider=ProviderType.OLLAMA,
        display_name="Llama 3.2",
        capabilities=[ModelCapability.REASONING, ModelCapability.FAST],
        context_length=128_000,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        description="Meta's latest general-purpose model",
    ),
    ModelInfo(
        name="llama3.2:1b",
        provider=ProviderType.OLLAMA,
        display_name="Llama 3.2 1B",
        capabilities=[ModelCapability.FAST, ModelCapability.CHEAP],
        context_length=128_000,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        description="Fast, efficient Llama variant",
    ),
    ModelInfo(
        name="codellama",
        provider=ProviderType.OLLAMA,
        display_name="Code Llama",
        capabilities=[ModelCapability.CODING, ModelCapability.REASONING],
        context_length=128_000,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        description="Code-specialized Llama",
    ),
    ModelInfo(
        name="mistral",
        provider=ProviderType.OLLAMA,
        display_name="Mistral",
        capabilities=[ModelCapability.REASONING, ModelCapability.FAST],
        context_length=32_000,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        description="Efficient general-purpose model",
    ),
    ModelInfo(
        name="qwen2.5",
        provider=ProviderType.OLLAMA,
        display_name="Qwen 2.5",
        capabilities=[ModelCapability.REASONING, ModelCapability.LARGE_CONTEXT],
        context_length=32_000,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        description="Alibaba's capable model",
    ),
    # OpenAI models
    ModelInfo(
        name="gpt-4o",
        provider=ProviderType.OPENAI,
        display_name="GPT-4o",
        capabilities=[ModelCapability.REASONING, ModelCapability.CODING, ModelCapability.VISION],
        context_length=128_000,
        max_output_tokens=16_384,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        description="OpenAI's flagship multimodal model",
    ),
    ModelInfo(
        name="gpt-4o-mini",
        provider=ProviderType.OPENAI,
        display_name="GPT-4o Mini",
        capabilities=[ModelCapability.FAST, ModelCapability.CHEAP],
        context_length=128_000,
        max_output_tokens=16_384,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        description="Fast, affordable GPT-4 variant",
    ),
    ModelInfo(
        name="gpt-4-turbo",
        provider=ProviderType.OPENAI,
        display_name="GPT-4 Turbo",
        capabilities=[ModelCapability.REASONING, ModelCapability.CODING],
        context_length=128_000,
        max_output_tokens=4096,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        description="Fast GPT-4 variant",
    ),
    # Anthropic models
    ModelInfo(
        name="claude-sonnet-4-20250514",
        provider=ProviderType.ANTHROPIC,
        display_name="Claude Sonnet 4",
        capabilities=[ModelCapability.REASONING, ModelCapability.CODING, ModelCapability.LARGE_CONTEXT],
        context_length=200_000,
        max_output_tokens=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        description="Anthropic's balanced model",
    ),
    ModelInfo(
        name="claude-3-5-sonnet-20241022",
        provider=ProviderType.ANTHROPIC,
        display_name="Claude 3.5 Sonnet",
        capabilities=[ModelCapability.REASONING, ModelCapability.CODING, ModelCapability.LARGE_CONTEXT],
        context_length=200_000,
        max_output_tokens=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        description="Anthropic's most capable coding model",
    ),
    ModelInfo(
        name="claude-3-5-haiku-20241022",
        provider=ProviderType.ANTHROPIC,
        display_name="Claude 3.5 Haiku",
        capabilities=[ModelCapability.FAST, ModelCapability.CHEAP],
        context_length=200_000,
        max_output_tokens=8192,
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.004,
        description="Fast, affordable Claude",
    ),
    ModelInfo(
        name="claude-3-opus-20240229",
        provider=ProviderType.ANTHROPIC,
        display_name="Claude 3 Opus",
        capabilities=[ModelCapability.REASONING, ModelCapability.CODING, ModelCapability.LARGE_CONTEXT],
        context_length=200_000,
        max_output_tokens=4096,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        description="Anthropic's most capable model",
    ),
]


# Default routing rules
DEFAULT_ROUTING_RULES = [
    RoutingRule(
        task_type=TaskType.PLANNING,
        preferred_capabilities=[ModelCapability.REASONING],
        fallback_capabilities=[ModelCapability.FAST],
        max_latency_ms=5000,
    ),
    RoutingRule(
        task_type=TaskType.RESEARCH,
        preferred_capabilities=[ModelCapability.LARGE_CONTEXT, ModelCapability.REASONING],
        fallback_capabilities=[ModelCapability.REASONING],
        min_context_length=32_000,
        max_cost_per_request=0.50,
    ),
    RoutingRule(
        task_type=TaskType.CODING,
        preferred_capabilities=[ModelCapability.CODING],
        fallback_capabilities=[ModelCapability.REASONING],
        max_latency_ms=10000,
    ),
    RoutingRule(
        task_type=TaskType.REVIEW,
        preferred_capabilities=[ModelCapability.REASONING, ModelCapability.CODING],
        fallback_capabilities=[ModelCapability.REASONING],
        max_latency_ms=10000,
    ),
    RoutingRule(
        task_type=TaskType.DOCUMENTATION,
        preferred_capabilities=[ModelCapability.FAST, ModelCapability.CHEAP],
        fallback_capabilities=[ModelCapability.REASONING],
        max_cost_per_request=0.10,
    ),
    RoutingRule(
        task_type=TaskType.GENERAL,
        preferred_capabilities=[ModelCapability.REASONING],
        fallback_capabilities=[ModelCapability.FAST],
    ),
]


# Agent to task type mapping
AGENT_TO_TASK = {
    AgentType.PLANNER: TaskType.PLANNING,
    AgentType.RESEARCHER: TaskType.RESEARCH,
    AgentType.CODER: TaskType.CODING,
    AgentType.REVIEWER: TaskType.REVIEW,
    AgentType.TESTER: TaskType.CODING,
    AgentType.DOCUMENTATION: TaskType.DOCUMENTATION,
    AgentType.MANAGER: TaskType.GENERAL,
}


class ModelRouter:
    """Intelligent model router."""

    def __init__(self, config: ModelConfig | None = None):
        """Initialize router.
        
        Args:
            config: Model configuration. Uses defaults if not provided.
        """
        self.config = config or self._default_config()
        self._metrics = RoutingMetrics()
        self._request_times: dict[str, list[float]] = {}

    def _default_config(self) -> ModelConfig:
        """Get default configuration."""
        return ModelConfig(
            models=DEFAULT_MODELS,
            routing_rules=DEFAULT_ROUTING_RULES,
            default_task_routing={
                TaskType.PLANNING: "claude-sonnet-4-20250514",
                TaskType.RESEARCH: "claude-3-5-sonnet-20241022",
                TaskType.CODING: "gpt-4o",
                TaskType.REVIEW: "claude-3-5-sonnet-20241022",
                TaskType.DOCUMENTATION: "gpt-4o-mini",
            },
            routing_strategy="capability_first",
            enable_fallback=True,
        )

    def get_available_models(self) -> list[ModelInfo]:
        """Get list of available models."""
        return [m for m in self.config.models if m.enabled]

    def get_task_rule(self, task_type: TaskType) -> RoutingRule | None:
        """Get routing rule for a task type."""
        for rule in self.config.routing_rules:
            if rule.task_type == task_type:
                return rule
        return None

    def estimate_cost(
        self,
        model: ModelInfo,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost for a request.
        
        Args:
            model: Model info
            input_tokens: Estimated input tokens
            output_tokens: Estimated output tokens
            
        Returns:
            Estimated cost in dollars
        """
        input_cost = (input_tokens / 1000) * model.cost_per_1k_input
        output_cost = (output_tokens / 1000) * model.cost_per_1k_output
        return input_cost + output_cost

    def estimate_latency(
        self,
        model: ModelInfo,
        input_tokens: int,
        output_tokens: int,
    ) -> float | None:
        """Estimate latency for a request.
        
        Args:
            model: Model info
            input_tokens: Estimated input tokens
            output_tokens: Estimated output tokens
            
        Returns:
            Estimated latency in ms
        """
        if model.latency_ms:
            return model.latency_ms

        # Estimate based on model type and token count
        base_latency = {
            ModelCapability.FAST: 500,
            ModelCapability.CHEAP: 800,
            ModelCapability.REASONING: 2000,
            ModelCapability.LARGE_CONTEXT: 3000,
        }

        for cap in model.capabilities:
            if cap in base_latency:
                # Add per-token latency
                return base_latency[cap] + (output_tokens * 0.5)

        return 2000 + (output_tokens * 0.5)

    def score_model(
        self,
        model: ModelInfo,
        request: RouteRequest,
        rule: RoutingRule,
    ) -> float:
        """Score a model for a request.
        
        Args:
            model: Model to score
            request: Route request
            rule: Routing rule
            
        Returns:
            Score (higher is better)
        """
        score = 0.0

        # Capability match (most important)
        capability_score = 0.0
        for cap in rule.preferred_capabilities:
            if cap in model.capabilities:
                capability_score += 2.0

        # Also check fallback capabilities
        for cap in rule.fallback_capabilities:
            if cap in model.capabilities:
                capability_score += 1.0

        score += capability_score * 10

        # Context length check
        if model.context_length >= request.estimated_input_tokens:
            score += 5.0
        elif model.context_length < request.estimated_input_tokens:
            return -1.0  # Cannot handle request

        # Cost factor
        if request.prefer_low_cost or rule.max_cost_per_request:
            estimated_cost = self.estimate_cost(
                model,
                request.estimated_input_tokens,
                request.estimated_output_tokens,
            )
            if rule.max_cost_per_request and estimated_cost > rule.max_cost_per_request:
                return -1.0
            score += max(0, 10 - estimated_cost * 100)

        # Latency factor
        if request.prefer_low_latency or rule.max_latency_ms:
            estimated_latency = self.estimate_latency(
                model,
                request.estimated_input_tokens,
                request.estimated_output_tokens,
            )
            if estimated_latency:
                if rule.max_latency_ms and estimated_latency > rule.max_latency_ms:
                    return -1.0
                score += max(0, 10 - estimated_latency / 500)

        # Provider availability bonus
        if model.provider == ProviderType.OLLAMA:
            score += 2.0  # Local = faster, free

        return score

    def route(self, request: RouteRequest) -> RouteResult:
        """Route a request to the best model.
        
        Args:
            request: Route request
            
        Returns:
            Route result with selected model
        """
        rule = self.get_task_rule(request.task_type)

        # Score all available models
        scored_models = []
        for model in self.get_available_models():
            score = self.score_model(model, request, rule or RoutingRule(task_type=request.task_type))
            if score >= 0:
                scored_models.append((score, model))

        if not scored_models:
            # Fallback to any available model
            if self.config.enable_fallback and self.get_available_models():
                model = self.get_available_models()[0]
                return RouteResult(
                    selected_model=model,
                    provider=model.provider.value,
                    reasoning="Fallback to first available model",
                    estimated_cost=self.estimate_cost(
                        model,
                        request.estimated_input_tokens,
                        request.estimated_output_tokens,
                    ),
                    estimated_latency=self.estimate_latency(
                        model,
                        request.estimated_input_tokens,
                        request.estimated_output_tokens,
                    ),
                )
            raise ValueError("No models available")

        # Sort by score (descending)
        scored_models.sort(key=lambda x: x[0], reverse=True)

        # Get best model
        best_score, best_model = scored_models[0]

        # Get alternatives
        alternatives = [m for _, m in scored_models[1:4]]

        # Build reasoning
        reasoning = f"Selected {best_model.display_name} for {request.task_type.value} task"
        if rule:
            matching_caps = [c.value for c in rule.preferred_capabilities if c in best_model.capabilities]
            if matching_caps:
                reasoning += f". Matches capabilities: {', '.join(matching_caps)}"

        return RouteResult(
            selected_model=best_model,
            provider=best_model.provider.value,
            reasoning=reasoning,
            estimated_cost=self.estimate_cost(
                best_model,
                request.estimated_input_tokens,
                request.estimated_output_tokens,
            ),
            estimated_latency=self.estimate_latency(
                best_model,
                request.estimated_input_tokens,
                request.estimated_output_tokens,
            ),
            alternatives=alternatives,
        )

    def route_for_agent(
        self,
        agent_type: AgentType,
        estimated_input_tokens: int = 1000,
        estimated_output_tokens: int = 500,
    ) -> RouteResult:
        """Route for a specific agent type.
        
        Args:
            agent_type: Agent type
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens
            
        Returns:
            Route result
        """
        task_type = AGENT_TO_TASK.get(agent_type, TaskType.GENERAL)

        request = RouteRequest(
            task_type=task_type,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
        )

        return self.route(request)

    def update_model_latency(self, model_name: str, latency_ms: float) -> None:
        """Update model latency metric.
        
        Args:
            model_name: Model name
            latency_ms: Measured latency in ms
        """
        for model in self.config.models:
            if model.name == model_name:
                model.latency_ms = latency_ms
                break

        # Update request times for metrics
        if model_name not in self._request_times:
            self._request_times[model_name] = []
        self._request_times[model_name].append(latency_ms)

        # Keep only last 100 measurements
        self._request_times[model_name] = self._request_times[model_name][-100:]

    def get_metrics(self) -> RoutingMetrics:
        """Get routing metrics."""
        self._metrics.total_requests = sum(
            count for count in self._metrics.requests_by_model.values()
        )

        # Calculate average latency
        all_latencies = []
        for latencies in self._request_times.values():
            all_latencies.extend(latencies)
        if all_latencies:
            self._metrics.average_latency_ms = sum(all_latencies) / len(all_latencies)

        return self._metrics

    def record_request(
        self,
        model_name: str,
        task_type: TaskType,
        latency_ms: float,
        cost: float,
    ) -> None:
        """Record a request for metrics.
        
        Args:
            model_name: Model used
            task_type: Task type
            latency_ms: Request latency
            cost: Request cost
        """
        # Update model latency
        self.update_model_latency(model_name, latency_ms)

        # Update metrics
        task_key = task_type.value
        self._metrics.requests_by_task[task_key] = self._metrics.requests_by_task.get(task_key, 0) + 1
        self._metrics.requests_by_model[model_name] = self._metrics.requests_by_model.get(model_name, 0) + 1

        self._metrics.total_cost += cost
        self._metrics.average_cost = self._metrics.total_cost / max(
            1, sum(self._metrics.requests_by_model.values())
        )
        self._metrics.last_updated = datetime.utcnow()


# Global router instance
_model_router: ModelRouter | None = None


def get_model_router() -> ModelRouter:
    """Get the global model router.
    
    Returns:
        ModelRouter instance
    """
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router


def set_model_router(router: ModelRouter) -> None:
    """Set the global model router.
    
    Args:
        router: Router instance
    """
    global _model_router
    _model_router = router
