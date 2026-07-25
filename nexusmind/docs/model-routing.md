# Model Routing Documentation

Intelligent model routing selects the optimal LLM provider and model based on task requirements.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Model Router                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│   │   Ollama   │    │   OpenAI   │    │  Anthropic  │   │
│   │  (Local)   │    │   (API)    │    │   (API)     │   │
│   └──────┬─────┘    └──────┬─────┘    └──────┬─────┘   │
│          │                 │                 │          │
│          └─────────────────┼─────────────────┘          │
│                            │                            │
│                            ▼                            │
│                   ┌────────────────┐                   │
│                   │   Model Catalog │                   │
│                   │   + Routing     │                   │
│                   │   + Scoring     │                   │
│                   └────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Routing Rules

| Agent | Task Type | Preferred Model |
|-------|-----------|-----------------|
| Planner | `planning` | Reasoning model |
| Researcher | `research` | Large context model |
| Coder | `coding` | Coding model |
| Reviewer | `review` | Strong reasoning model |
| Documentation | `documentation` | Efficient/cheap model |

## Supported Providers

### Ollama (Local)
- Free, fast inference
- Models: llama3.2, codellama, mistral, qwen2.5

### OpenAI
- gpt-4o (multipurpose)
- gpt-4o-mini (fast, cheap)
- gpt-4-turbo (fast GPT-4)

### Anthropic
- claude-sonnet-4 (balanced)
- claude-3-5-sonnet (coding specialist)
- claude-3-5-haiku (fast, cheap)

## Usage

### Basic Routing

```python
from app.llm.routing import ModelRouter, TaskType, RouteRequest

router = ModelRouter()

# Route for a task
request = RouteRequest(
    task_type=TaskType.CODING,
    estimated_input_tokens=1000,
    estimated_output_tokens=500,
)

result = router.route(request)
print(f"Model: {result.selected_model.name}")
print(f"Provider: {result.provider}")
print(f"Cost: ${result.estimated_cost:.4f}")
```

### Route for Agent

```python
from app.agents.types import AgentType

result = router.route_for_agent(AgentType.CODER)
print(f"Selected: {result.selected_model.display_name}")
```

### Custom Configuration

```python
from app.llm.routing import ModelConfig, ModelRouter

config = ModelConfig(
    routing_strategy="cost_first",
    enable_fallback=True,
)

router = ModelRouter(config)
```

## Configuration File

```yaml
# model_routing.yaml
models:
  - name: llama3.2
    provider: ollama
    display_name: Llama 3.2
    capabilities:
      - reasoning
      - fast
    context_length: 128000
    cost_per_1k_input: 0.0
    enabled: true

  - name: gpt-4o
    provider: openai
    display_name: GPT-4o
    capabilities:
      - reasoning
      - coding
    context_length: 128000
    cost_per_1k_input: 0.005
    cost_per_1k_output: 0.015
    enabled: true

routing_rules:
  - task_type: coding
    preferred_capabilities:
      - coding
    fallback_capabilities:
      - reasoning
    max_latency_ms: 10000

  - task_type: documentation
    preferred_capabilities:
      - fast
      - cheap
    max_cost_per_request: 0.10

default_task_routing:
  coding: gpt-4o
  planning: claude-3-5-sonnet-20241022

routing_strategy: capability_first
enable_fallback: true
```

### Load Configuration

```python
from app.llm.routing import load_model_config, ModelRouter

config = load_model_config("model_routing.yaml")
router = ModelRouter(config)
```

## REST API

### List Models

```bash
GET /api/v1/routing/models
```

### List by Provider

```bash
GET /api/v1/routing/models?provider=openai
```

### Route Request

```bash
POST /api/v1/routing/route
Content-Type: application/json

{
    "task_type": "coding",
    "estimated_input_tokens": 1000,
    "estimated_output_tokens": 500,
    "prefer_low_cost": false
}
```

### Route for Agent

```bash
POST /api/v1/routing/route/agent/coder
```

### Get Metrics

```bash
GET /api/v1/routing/metrics
```

### Estimate Cost

```bash
GET /api/v1/routing/estimate?model_name=gpt-4o&input_tokens=1000&output_tokens=500
```

## Scoring Algorithm

Models are scored based on:

1. **Capability Match** (highest weight)
   - Preferred capabilities: +2 points each
   - Fallback capabilities: +1 point each

2. **Context Length**
   - Can handle request: +5 points
   - Cannot handle: -∞ (excluded)

3. **Cost** (if preferred)
   - Lower cost = higher score

4. **Latency** (if preferred)
   - Lower latency = higher score

5. **Provider Bonus**
   - Ollama (local): +2 points

## Task Types

| Type | Description | Preferred Capabilities |
|------|-------------|----------------------|
| `planning` | Task decomposition | reasoning |
| `research` | Information gathering | large_context, reasoning |
| `coding` | Code generation | coding |
| `review` | Code review | reasoning, coding |
| `documentation` | Doc generation | fast, cheap |
| `general` | General tasks | reasoning |

## Model Capabilities

| Capability | Description |
|------------|-------------|
| `reasoning` | Strong reasoning |
| `large_context` | Long context window |
| `coding` | Code generation |
| `fast` | Fast inference |
| `cheap` | Low cost |
| `vision` | Image understanding |
| `function_calling` | Tool use |

## Cost Estimation

```python
cost = (input_tokens / 1000) * model.cost_per_1k_input + \
       (output_tokens / 1000) * model.cost_per_1k_output
```

## Latency Estimation

Based on model capabilities:
- `fast`: ~500ms base
- `cheap`: ~800ms base
- `reasoning`: ~2000ms base
- `large_context`: ~3000ms base

Plus per-token latency.

## Metrics

Track routing decisions:

```python
router.record_request(
    model_name="gpt-4o",
    task_type=TaskType.CODING,
    latency_ms=1500.0,
    cost=0.025,
)

metrics = router.get_metrics()
print(f"Total requests: {metrics.total_requests}")
print(f"Avg latency: {metrics.average_latency_ms}ms")
print(f"Total cost: ${metrics.total_cost}")
```

## Integration

### With LLM Manager

```python
from app.llm import LLMManager
from app.llm.routing import get_model_router

router = get_model_router()
llm = LLMManager()

# Route request
result = router.route_for_agent(AgentType.CODER)

# Use routed provider
response = await llm.chat(
    messages,
    provider=result.provider,
    model=result.selected_model.name,
)
```

### Custom Provider

```python
from app.llm.providers import BaseLLMProvider

class MyProvider(BaseLLMProvider):
    async def chat(self, messages, **kwargs):
        # Implementation
        pass
```
