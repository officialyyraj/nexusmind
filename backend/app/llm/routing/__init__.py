"""Intelligent model routing module."""

from app.llm.routing.api import router as api_router
from app.llm.routing.config import (
    EXAMPLE_CONFIG,
    create_router_from_config,
    load_model_config,
    parse_config_data,
    save_model_config,
)
from app.llm.routing.router import (
    AGENT_TO_TASK,
    DEFAULT_MODELS,
    DEFAULT_ROUTING_RULES,
    ModelRouter,
    get_model_router,
    set_model_router,
)
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

__all__ = [
    # Router
    "ModelRouter",
    "get_model_router",
    "set_model_router",
    # Schemas
    "TaskType",
    "ModelCapability",
    "ProviderType",
    "ModelInfo",
    "RoutingRule",
    "RouteRequest",
    "RouteResult",
    "RoutingMetrics",
    "ModelConfig",
    # Config
    "load_model_config",
    "save_model_config",
    "parse_config_data",
    "create_router_from_config",
    "EXAMPLE_CONFIG",
    # Defaults
    "DEFAULT_MODELS",
    "DEFAULT_ROUTING_RULES",
    "AGENT_TO_TASK",
    # API
    "api_router",
]
