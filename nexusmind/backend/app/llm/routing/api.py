"""REST API endpoints for model routing."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.agents.types import AgentType
from app.llm.routing.router import get_model_router
from app.llm.routing.schemas import (
    ModelConfig,
    ModelInfo,
    ProviderType,
    RouteRequest,
    RouteResult,
    RoutingMetrics,
    TaskType,
)

router = APIRouter(prefix="/api/v1/routing", tags=["routing"])


def get_router():
    """Get model router."""
    return get_model_router()


@router.get("/models", response_model=list[ModelInfo])
async def list_models(provider: ProviderType | None = None) -> list[ModelInfo]:
    """List available models.
    
    Args:
        provider: Filter by provider
        
    Returns:
        List of models
    """
    router = get_router()
    models = router.get_available_models()

    if provider:
        models = [m for m in models if m.provider == provider]

    return models


@router.get("/models/{model_name}")
async def get_model(model_name: str) -> ModelInfo:
    """Get model info.
    
    Args:
        model_name: Model name
        
    Returns:
        Model info
    """
    router = get_router()

    for model in router.get_available_models():
        if model.name == model_name:
            return model

    raise HTTPException(status_code=404, detail="Model not found")


@router.post("/route", response_model=RouteResult)
async def route_request(request: RouteRequest) -> RouteResult:
    """Route a request to the best model.
    
    Args:
        request: Route request
        
    Returns:
        Route result
    """
    router = get_router()
    return router.route(request)


@router.post("/route/agent/{agent_type}", response_model=RouteResult)
async def route_for_agent(
    agent_type: str,
    estimated_input_tokens: int = 1000,
    estimated_output_tokens: int = 500,
) -> RouteResult:
    """Route for a specific agent type.
    
    Args:
        agent_type: Agent type name
        estimated_input_tokens: Estimated input tokens
        estimated_output_tokens: Estimated output tokens
        
    Returns:
        Route result
    """
    router = get_router()

    try:
        agent = AgentType(agent_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")

    return router.route_for_agent(
        agent_type=agent,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
    )


@router.post("/route/task/{task_type}", response_model=RouteResult)
async def route_for_task(
    task_type: str,
    estimated_input_tokens: int = 1000,
    estimated_output_tokens: int = 500,
    prefer_low_cost: bool = False,
    prefer_low_latency: bool = False,
) -> RouteResult:
    """Route for a specific task type.
    
    Args:
        task_type: Task type name
        estimated_input_tokens: Estimated input tokens
        estimated_output_tokens: Estimated output tokens
        prefer_low_cost: Prefer low cost
        prefer_low_latency: Prefer low latency
        
    Returns:
        Route result
    """
    router = get_router()

    try:
        task = TaskType(task_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid task type: {task_type}")

    request = RouteRequest(
        task_type=task,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        prefer_low_cost=prefer_low_cost,
        prefer_low_latency=prefer_low_latency,
    )

    return router.route(request)


@router.get("/metrics", response_model=RoutingMetrics)
async def get_metrics() -> RoutingMetrics:
    """Get routing metrics.
    
    Returns:
        Routing metrics
    """
    router = get_router()
    return router.get_metrics()


@router.post("/record")
async def record_request(
    model_name: str,
    task_type: str,
    latency_ms: float,
    cost: float,
) -> dict[str, Any]:
    """Record a request for metrics.
    
    Args:
        model_name: Model used
        task_type: Task type
        latency_ms: Request latency
        cost: Request cost
        
    Returns:
        Success status
    """
    router = get_router()

    try:
        task = TaskType(task_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid task type: {task_type}")

    router.record_request(model_name, task_type=task, latency_ms=latency_ms, cost=cost)

    return {"recorded": True}


@router.get("/estimate")
async def estimate_cost(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
) -> dict[str, Any]:
    """Estimate cost for a request.
    
    Args:
        model_name: Model name
        input_tokens: Input tokens
        output_tokens: Output tokens
        
    Returns:
        Cost estimate
    """
    router = get_router()

    model = None
    for m in router.get_available_models():
        if m.name == model_name:
            model = m
            break

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    cost = router.estimate_cost(model, input_tokens, output_tokens)
    latency = router.estimate_latency(model, input_tokens, output_tokens)

    return {
        "model": model_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": cost,
        "estimated_latency_ms": latency,
    }
