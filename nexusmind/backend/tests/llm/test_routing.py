"""Tests for model routing."""

import pytest
from unittest.mock import MagicMock, patch

from app.llm.routing.schemas import (
    ModelCapability,
    ModelInfo,
    ProviderType,
    RouteRequest,
    RouteResult,
    RoutingRule,
    TaskType,
)
from app.llm.routing.router import (
    DEFAULT_MODELS,
    ModelRouter,
    get_model_router,
    set_model_router,
)


class TestSchemas:
    """Test routing schemas."""

    def test_task_type_values(self):
        """Test TaskType enum values."""
        assert TaskType.PLANNING.value == "planning"
        assert TaskType.RESEARCH.value == "research"
        assert TaskType.CODING.value == "coding"
        assert TaskType.REVIEW.value == "review"
        assert TaskType.DOCUMENTATION.value == "documentation"

    def test_model_capability_values(self):
        """Test ModelCapability enum values."""
        assert ModelCapability.REASONING.value == "reasoning"
        assert ModelCapability.LARGE_CONTEXT.value == "large_context"
        assert ModelCapability.CODING.value == "coding"
        assert ModelCapability.FAST.value == "fast"
        assert ModelCapability.CHEAP.value == "cheap"

    def test_provider_type_values(self):
        """Test ProviderType enum values."""
        assert ProviderType.OLLAMA.value == "ollama"
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.ANTHROPIC.value == "anthropic"

    def test_model_info(self):
        """Test ModelInfo."""
        model = ModelInfo(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            display_name="GPT-4o",
            capabilities=[ModelCapability.REASONING, ModelCapability.CODING],
            context_length=128_000,
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.015,
        )
        assert model.name == "gpt-4o"
        assert ModelCapability.REASONING in model.capabilities
        assert model.context_length == 128_000

    def test_routing_rule(self):
        """Test RoutingRule."""
        rule = RoutingRule(
            task_type=TaskType.CODING,
            preferred_capabilities=[ModelCapability.CODING],
            fallback_capabilities=[ModelCapability.REASONING],
            max_latency_ms=5000,
        )
        assert rule.task_type == TaskType.CODING
        assert ModelCapability.CODING in rule.preferred_capabilities
        assert rule.max_latency_ms == 5000

    def test_route_request(self):
        """Test RouteRequest."""
        request = RouteRequest(
            task_type=TaskType.CODING,
            estimated_input_tokens=1000,
            estimated_output_tokens=500,
            prefer_low_cost=True,
        )
        assert request.task_type == TaskType.CODING
        assert request.prefer_low_cost is True

    def test_route_result(self):
        """Test RouteResult."""
        model = ModelInfo(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            display_name="GPT-4o",
        )
        result = RouteResult(
            selected_model=model,
            provider="openai",
            reasoning="Best for coding",
            estimated_cost=0.01,
        )
        assert result.selected_model.name == "gpt-4o"
        assert result.estimated_cost == 0.01


class TestModelRouter:
    """Test ModelRouter class."""

    def test_router_creation(self):
        """Test router creation."""
        router = ModelRouter()
        assert router is not None
        assert len(router.get_available_models()) > 0

    def test_get_available_models(self):
        """Test getting available models."""
        router = ModelRouter()
        models = router.get_available_models()
        assert len(models) > 0
        assert all(m.enabled for m in models)

    def test_get_task_rule(self):
        """Test getting task rule."""
        router = ModelRouter()
        rule = router.get_task_rule(TaskType.CODING)
        assert rule is not None
        assert rule.task_type == TaskType.CODING
        assert ModelCapability.CODING in rule.preferred_capabilities

    def test_estimate_cost(self):
        """Test cost estimation."""
        router = ModelRouter()
        model = ModelInfo(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            display_name="GPT-4o",
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.015,
        )
        
        cost = router.estimate_cost(model, 1000, 500)
        assert cost == 0.005 + 0.0075  # $0.0125

    def test_estimate_cost_free_model(self):
        """Test cost estimation for free model."""
        router = ModelRouter()
        model = ModelInfo(
            name="llama3.2",
            provider=ProviderType.OLLAMA,
            display_name="Llama 3.2",
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
        )
        
        cost = router.estimate_cost(model, 1000, 500)
        assert cost == 0.0

    def test_route_coding_task(self):
        """Test routing for coding task."""
        router = ModelRouter()
        request = RouteRequest(
            task_type=TaskType.CODING,
            estimated_input_tokens=1000,
            estimated_output_tokens=500,
        )
        
        result = router.route(request)
        assert result.selected_model is not None
        assert result.provider is not None
        assert ModelCapability.CODING in result.selected_model.capabilities or \
               ModelCapability.REASONING in result.selected_model.capabilities

    def test_route_research_task(self):
        """Test routing for research task."""
        router = ModelRouter()
        request = RouteRequest(
            task_type=TaskType.RESEARCH,
            estimated_input_tokens=50000,
            estimated_output_tokens=2000,
        )
        
        result = router.route(request)
        assert result.selected_model is not None
        assert result.selected_model.context_length >= 50000

    def test_route_documentation_task(self):
        """Test routing for documentation task."""
        router = ModelRouter()
        request = RouteRequest(
            task_type=TaskType.DOCUMENTATION,
            estimated_input_tokens=500,
            estimated_output_tokens=200,
            prefer_low_cost=True,
        )
        
        result = router.route(request)
        assert result.selected_model is not None
        # Documentation should prefer cheaper models
        assert result.estimated_cost < 0.01

    def test_route_with_fallback(self):
        """Test routing with fallback."""
        router = ModelRouter()
        router.config.enable_fallback = True
        
        request = RouteRequest(
            task_type=TaskType.PLANNING,
            estimated_input_tokens=100,
            estimated_output_tokens=100,
        )
        
        result = router.route(request)
        assert result.selected_model is not None
        assert len(result.alternatives) >= 0

    def test_route_for_agent_planner(self):
        """Test routing for planner agent."""
        from app.agents.types import AgentType
        
        router = ModelRouter()
        result = router.route_for_agent(AgentType.PLANNER)
        
        assert result.selected_model is not None
        # Planner should use reasoning model
        assert ModelCapability.REASONING in result.selected_model.capabilities

    def test_route_for_agent_coder(self):
        """Test routing for coder agent."""
        from app.agents.types import AgentType
        
        router = ModelRouter()
        result = router.route_for_agent(AgentType.CODER)
        
        assert result.selected_model is not None
        # Coder should prefer coding-capable model
        caps = result.selected_model.capabilities
        assert ModelCapability.CODING in caps or ModelCapability.REASONING in caps

    def test_route_for_agent_researcher(self):
        """Test routing for researcher agent."""
        from app.agents.types import AgentType
        
        router = ModelRouter()
        result = router.route_for_agent(AgentType.RESEARCHER)
        
        assert result.selected_model is not None
        # Researcher should prefer large context
        assert result.selected_model.context_length >= 32000


class TestDefaultModels:
    """Test default model catalog."""

    def test_default_models_exist(self):
        """Test that default models are defined."""
        assert len(DEFAULT_MODELS) > 0

    def test_default_models_have_providers(self):
        """Test that all default models have providers."""
        for model in DEFAULT_MODELS:
            assert model.provider is not None
            assert model.name is not None

    def test_ollama_models(self):
        """Test Ollama model configuration."""
        ollama_models = [m for m in DEFAULT_MODELS if m.provider == ProviderType.OLLAMA]
        assert len(ollama_models) > 0
        for model in ollama_models:
            assert model.cost_per_1k_input == 0.0
            assert model.cost_per_1k_output == 0.0

    def test_openai_models(self):
        """Test OpenAI model configuration."""
        openai_models = [m for m in DEFAULT_MODELS if m.provider == ProviderType.OPENAI]
        assert len(openai_models) > 0
        for model in openai_models:
            assert model.cost_per_1k_input > 0

    def test_anthropic_models(self):
        """Test Anthropic model configuration."""
        anthropic_models = [m for m in DEFAULT_MODELS if m.provider == ProviderType.ANTHROPIC]
        assert len(anthropic_models) > 0
        for model in anthropic_models:
            assert model.context_length >= 200_000


class TestRoutingIntegration:
    """Integration tests for routing."""

    def test_singleton_pattern(self):
        """Test router singleton."""
        router1 = get_model_router()
        router2 = get_model_router()
        assert router1 is router2

    def test_set_router(self):
        """Test setting custom router."""
        custom_router = ModelRouter()
        set_model_router(custom_router)
        assert get_model_router() is custom_router

    def test_metrics_recording(self):
        """Test metrics recording."""
        router = ModelRouter()
        initial_metrics = router.get_metrics()
        
        router.record_request(
            model_name="gpt-4o",
            task_type=TaskType.CODING,
            latency_ms=1000.0,
            cost=0.01,
        )
        
        metrics = router.get_metrics()
        assert metrics.total_requests >= initial_metrics.total_requests

    def test_model_latency_update(self):
        """Test model latency update."""
        router = ModelRouter()
        router.update_model_latency("gpt-4o", 500.0)
        
        model = None
        for m in router.config.models:
            if m.name == "gpt-4o":
                model = m
                break
        
        assert model is not None
        assert model.latency_ms == 500.0


class TestConfig:
    """Test configuration functionality."""

    def test_parse_config_data(self):
        """Test parsing config data."""
        from app.llm.routing.config import parse_config_data
        
        data = {
            "models": [
                {
                    "name": "test-model",
                    "provider": "ollama",
                    "display_name": "Test Model",
                    "capabilities": ["fast", "cheap"],
                    "context_length": 8000,
                }
            ],
            "routing_rules": [
                {
                    "task_type": "planning",
                    "preferred_capabilities": ["reasoning"],
                }
            ],
        }
        
        config = parse_config_data(data)
        assert len(config.models) == 1
        assert config.models[0].name == "test-model"
        assert len(config.routing_rules) == 1

    def test_example_config(self):
        """Test example config is valid YAML."""
        from app.llm.routing.config import EXAMPLE_CONFIG
        import yaml
        
        data = yaml.safe_load(EXAMPLE_CONFIG)
        assert "models" in data
        assert "routing_rules" in data


class TestAPI:
    """Test API endpoints."""

    def test_api_router_import(self):
        """Test that API router can be imported."""
        from app.llm.routing.api import router
        assert router is not None
