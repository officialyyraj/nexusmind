"""Self-improvement loop for coding agents."""

from app.agents.improvement.api import router as api_router
from app.agents.improvement.loop import (
    SelfImprovementLoop,
    get_improvement_loop,
    mock_critic,
    mock_generator,
)
from app.agents.improvement.schemas import (
    CritiqueResult,
    ImprovementConfig,
    ImprovementIteration,
    ImprovementLoop,
    ImprovementStatus,
    IterationPhase,
)
from app.agents.improvement.storage import (
    IterationStorage,
    get_iteration_storage,
)

__all__ = [
    # API
    "api_router",
    # Loop
    "SelfImprovementLoop",
    "get_improvement_loop",
    "mock_generator",
    "mock_critic",
    # Storage
    "IterationStorage",
    "get_iteration_storage",
    # Schemas
    "CritiqueResult",
    "ImprovementConfig",
    "ImprovementIteration",
    "ImprovementLoop",
    "ImprovementStatus",
    "IterationPhase",
]
