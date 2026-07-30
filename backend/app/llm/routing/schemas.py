"""Model routing schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Types of tasks for routing."""

    PLANNING = "planning"
    RESEARCH = "research"
    CODING = "coding"
    REVIEW = "review"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


class ModelCapability(str, Enum):
    """Model capabilities."""

    REASONING = "reasoning"  # Strong reasoning capabilities
    LARGE_CONTEXT = "large_context"  # Long context window
    CODING = "coding"  # Code generation
    FAST = "fast"  # Fast inference
    CHEAP = "cheap"  # Low cost
    VISION = "vision"  # Image understanding
    FUNCTION_CALLING = "function_calling"  # Tool use


class ProviderType(str, Enum):
    """LLM provider types."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ModelInfo(BaseModel):
    """Information about a model."""

    name: str = Field(..., description="Model identifier")
    provider: ProviderType = Field(..., description="Provider type")
    display_name: str = Field(..., description="Human-readable name")
    capabilities: list[ModelCapability] = Field(default_factory=list)
    context_length: int = Field(128_000, description="Context window size")
    max_output_tokens: int = Field(8192, description="Max output tokens")
    cost_per_1k_input: float = Field(0.0, description="Cost per 1K input tokens")
    cost_per_1k_output: float = Field(0.0, description="Cost per 1K output tokens")
    latency_ms: float | None = Field(None, description="Average latency in ms")
    enabled: bool = Field(True, description="Whether model is enabled")
    description: str = Field("", description="Model description")


class RoutingRule(BaseModel):
    """Routing rule configuration."""

    task_type: TaskType = Field(..., description="Task type")
    preferred_capabilities: list[ModelCapability] = Field(
        default_factory=list,
        description="Preferred capabilities for this task",
    )
    fallback_capabilities: list[ModelCapability] = Field(
        default_factory=list,
        description="Fallback capabilities if preferred not available",
    )
    max_cost_per_request: float | None = Field(
        None, description="Maximum cost per request"
    )
    max_latency_ms: float | None = Field(
        None, description="Maximum acceptable latency"
    )
    min_context_length: int = Field(
        0, description="Minimum context length required"
    )


class RouteRequest(BaseModel):
    """Request to route a task."""

    task_type: TaskType = Field(..., description="Type of task")
    estimated_input_tokens: int = Field(0, description="Estimated input tokens")
    estimated_output_tokens: int = Field(0, description="Estimated output tokens")
    priority: str = Field("normal", description="Priority: low, normal, high")
    prefer_low_cost: bool = Field(False, description="Prefer low cost")
    prefer_low_latency: bool = Field(False, description="Prefer low latency")


class RouteResult(BaseModel):
    """Result of routing decision."""

    selected_model: ModelInfo = Field(..., description="Selected model")
    provider: str = Field(..., description="Provider name")
    reasoning: str = Field("", description="Why this model was selected")
    estimated_cost: float = Field(0.0, description="Estimated cost")
    estimated_latency_ms: float | None = Field(None, description="Estimated latency")
    alternatives: list[ModelInfo] = Field(
        default_factory=list, description="Alternative models"
    )


class RoutingMetrics(BaseModel):
    """Metrics for routing decisions."""

    total_requests: int = 0
    requests_by_task: dict[str, int] = Field(default_factory=dict)
    requests_by_model: dict[str, int] = Field(default_factory=dict)
    average_cost: float = 0.0
    average_latency_ms: float = 0.0
    total_cost: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ModelConfig(BaseModel):
    """Configuration for model routing."""

    models: list[ModelInfo] = Field(default_factory=list)
    routing_rules: list[RoutingRule] = Field(default_factory=list)
    default_task_routing: dict[TaskType, str] = Field(default_factory=dict)
    routing_strategy: str = Field(
        "capability_first",
        description="Strategy: capability_first, cost_first, latency_first",
    )
    enable_fallback: bool = Field(
        True, description="Enable automatic fallback to alternative models"
    )
