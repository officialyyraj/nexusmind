"""Configuration file support for model routing."""

import json
from pathlib import Path
from typing import Any

import yaml

from app.llm.routing.router import ModelRouter
from app.llm.routing.schemas import ModelConfig, ModelInfo, ProviderType, RoutingRule, TaskType


def load_model_config(path: str | Path) -> ModelConfig:
    """Load model configuration from YAML or JSON file.
    
    Args:
        path: Path to config file
        
    Returns:
        ModelConfig instance
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        if path.suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(f)
        elif path.suffix == ".json":
            data = json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")

    return parse_config_data(data)


def parse_config_data(data: dict[str, Any]) -> ModelConfig:
    """Parse config data into ModelConfig.
    
    Args:
        data: Config dictionary
        
    Returns:
        ModelConfig instance
    """
    models = []
    for m in data.get("models", []):
        capabilities = [c if isinstance(c, str) else c for c in m.get("capabilities", [])]
        models.append(ModelInfo(
            name=m["name"],
            provider=ProviderType(m["provider"]),
            display_name=m.get("display_name", m["name"]),
            capabilities=capabilities,
            context_length=m.get("context_length", 128_000),
            max_output_tokens=m.get("max_output_tokens", 8192),
            cost_per_1k_input=m.get("cost_per_1k_input", 0.0),
            cost_per_1k_output=m.get("cost_per_1k_output", 0.0),
            latency_ms=m.get("latency_ms"),
            enabled=m.get("enabled", True),
            description=m.get("description", ""),
        ))

    rules = []
    for r in data.get("routing_rules", []):
        rules.append(RoutingRule(
            task_type=TaskType(r["task_type"]),
            preferred_capabilities=r.get("preferred_capabilities", []),
            fallback_capabilities=r.get("fallback_capabilities", []),
            max_cost_per_request=r.get("max_cost_per_request"),
            max_latency_ms=r.get("max_latency_ms"),
            min_context_length=r.get("min_context_length", 0),
        ))

    return ModelConfig(
        models=models,
        routing_rules=rules,
        default_task_routing=data.get("default_task_routing", {}),
        routing_strategy=data.get("routing_strategy", "capability_first"),
        enable_fallback=data.get("enable_fallback", True),
    )


def save_model_config(config: ModelConfig, path: str | Path) -> None:
    """Save model configuration to file.
    
    Args:
        config: ModelConfig to save
        path: Path to save to
    """
    path = Path(path)

    data = {
        "models": [
            {
                "name": m.name,
                "provider": m.provider.value,
                "display_name": m.display_name,
                "capabilities": [c.value for c in m.capabilities],
                "context_length": m.context_length,
                "max_output_tokens": m.max_output_tokens,
                "cost_per_1k_input": m.cost_per_1k_input,
                "cost_per_1k_output": m.cost_per_1k_output,
                "latency_ms": m.latency_ms,
                "enabled": m.enabled,
                "description": m.description,
            }
            for m in config.models
        ],
        "routing_rules": [
            {
                "task_type": r.task_type.value,
                "preferred_capabilities": [c.value for c in r.preferred_capabilities],
                "fallback_capabilities": [c.value for c in r.fallback_capabilities],
                "max_cost_per_request": r.max_cost_per_request,
                "max_latency_ms": r.max_latency_ms,
                "min_context_length": r.min_context_length,
            }
            for r in config.routing_rules
        ],
        "default_task_routing": config.default_task_routing,
        "routing_strategy": config.routing_strategy,
        "enable_fallback": config.enable_fallback,
    }

    with open(path, "w") as f:
        if path.suffix in [".yaml", ".yml"]:
            yaml.dump(data, f, default_flow_style=False)
        elif path.suffix == ".json":
            json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")


def create_router_from_config(path: str | Path) -> ModelRouter:
    """Create a ModelRouter from a config file.
    
    Args:
        path: Path to config file
        
    Returns:
        ModelRouter instance
    """
    config = load_model_config(path)
    return ModelRouter(config)


# Example configuration template
EXAMPLE_CONFIG = """
# Model Routing Configuration

# Available models
models:
  - name: llama3.2
    provider: ollama
    display_name: Llama 3.2
    capabilities:
      - reasoning
      - fast
    context_length: 128000
    cost_per_1k_input: 0.0
    cost_per_1k_output: 0.0
    enabled: true
    description: Meta's latest general-purpose model

  - name: gpt-4o
    provider: openai
    display_name: GPT-4o
    capabilities:
      - reasoning
      - coding
      - vision
    context_length: 128000
    max_output_tokens: 16384
    cost_per_1k_input: 0.005
    cost_per_1k_output: 0.015
    enabled: true
    description: OpenAI's flagship multimodal model

  - name: claude-3-5-sonnet-20241022
    provider: anthropic
    display_name: Claude 3.5 Sonnet
    capabilities:
      - reasoning
      - coding
      - large_context
    context_length: 200000
    max_output_tokens: 8192
    cost_per_1k_input: 0.003
    cost_per_1k_output: 0.015
    enabled: true
    description: Anthropic's most capable coding model

# Routing rules
routing_rules:
  - task_type: planning
    preferred_capabilities:
      - reasoning
    fallback_capabilities:
      - fast
    max_latency_ms: 5000

  - task_type: research
    preferred_capabilities:
      - large_context
      - reasoning
    fallback_capabilities:
      - reasoning
    min_context_length: 32000
    max_cost_per_request: 0.50

  - task_type: coding
    preferred_capabilities:
      - coding
    fallback_capabilities:
      - reasoning
    max_latency_ms: 10000

  - task_type: review
    preferred_capabilities:
      - reasoning
      - coding
    fallback_capabilities:
      - reasoning
    max_latency_ms: 10000

  - task_type: documentation
    preferred_capabilities:
      - fast
      - cheap
    fallback_capabilities:
      - reasoning
    max_cost_per_request: 0.10

# Default task routing (model names)
default_task_routing:
  planning: claude-3-5-sonnet-20241022
  research: claude-3-5-sonnet-20241022
  coding: gpt-4o
  review: claude-3-5-sonnet-20241022
  documentation: gpt-4o-mini

# Routing strategy: capability_first, cost_first, latency_first
routing_strategy: capability_first

# Enable automatic fallback to alternative models
enable_fallback: true
"""
