"""REST API endpoints for self-improvement loop."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.agents.improvement.loop import (
    SelfImprovementLoop,
    get_improvement_loop,
    mock_critic,
    mock_generator,
)
from app.agents.improvement.schemas import (
    ImprovementConfig,
    ImprovementLoop,
    ImprovementStatus,
    IterationPhase,
)
from app.agents.improvement.storage import get_iteration_storage

router = APIRouter(prefix="/api/v1/improvement", tags=["improvement"])


def get_loop() -> SelfImprovementLoop:
    """Get improvement loop instance."""
    return get_improvement_loop()


def get_storage():
    """Get storage instance."""
    return get_iteration_storage()


class RunLoopRequest:
    """Request to run improvement loop."""

    def __init__(
        self,
        task: str,
        initial_solution: str | None = None,
        max_iterations: int = 10,
        quality_threshold: float = 0.9,
        save_iterations: bool = True,
    ):
        self.task = task
        self.initial_solution = initial_solution
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.save_iterations = save_iterations


@router.post("/run", response_model=ImprovementLoop)
async def run_improvement_loop(request: dict[str, Any]) -> ImprovementLoop:
    """Run an improvement loop for a task.
    
    Args:
        request: Loop configuration
        
    Returns:
        Completed improvement loop
    """
    loop = get_loop()
    storage = get_storage()

    # Create config
    config = ImprovementConfig(
        max_iterations=request.get("max_iterations", 10),
        quality_threshold=request.get("quality_threshold", 0.9),
        save_iterations=request.get("save_iterations", True),
    )

    # Create loop with config
    improvement_loop = SelfImprovementLoop(
        generator=mock_generator,
        critic=mock_critic,
        storage=storage,
        config=config,
    )

    # Run loop
    result = await improvement_loop.run(
        task=request["task"],
        initial_solution=request.get("initial_solution"),
    )

    return result


@router.get("/loops", response_model=list[dict[str, Any]])
async def list_loops(limit: int = 10) -> list[dict[str, Any]]:
    """List recent improvement loops.
    
    Args:
        limit: Maximum number of loops to return
        
    Returns:
        List of recent loops
    """
    storage = get_storage()
    return storage.list_recent_loops(limit=limit)


@router.get("/loops/{loop_id}", response_model=ImprovementLoop)
async def get_loop_by_id(loop_id: str) -> ImprovementLoop:
    """Get a specific improvement loop.
    
    Args:
        loop_id: Loop ID
        
    Returns:
        Improvement loop
    """
    storage = get_storage()
    loop = storage.get_loop(loop_id)

    if not loop:
        raise HTTPException(status_code=404, detail="Loop not found")

    return loop


@router.get("/loops/{loop_id}/iterations")
async def get_loop_iterations(loop_id: str) -> list[dict[str, Any]]:
    """Get iterations for a loop.
    
    Args:
        loop_id: Loop ID
        
    Returns:
        List of iterations
    """
    storage = get_storage()
    iterations = storage.get_iterations(loop_id)

    return [
        {
            "iteration": i.iteration,
            "phase": i.phase.value,
            "timestamp": i.timestamp.isoformat(),
            "changes": i.changes,
            "execution_time": i.execution_time,
            "quality_score": i.critique.quality_score if i.critique else None,
        }
        for i in iterations
    ]


@router.get("/search")
async def search_loops(
    task_query: str | None = None,
    min_quality: float | None = None,
    status: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search for loops.
    
    Args:
        task_query: Text to search in tasks
        min_quality: Minimum quality score
        status: Filter by status
        limit: Maximum results
        
    Returns:
        List of matching loops
    """
    storage = get_storage()

    status_enum = None
    if status:
        try:
            status_enum = ImprovementStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    return storage.search_loops(
        task_query=task_query,
        min_quality=min_quality,
        status=status_enum,
        limit=limit,
    )


@router.get("/statistics")
async def get_statistics() -> dict[str, Any]:
    """Get storage statistics.
    
    Returns:
        Statistics
    """
    storage = get_storage()
    return storage.get_statistics()


@router.delete("/loops/{loop_id}")
async def delete_loop(loop_id: str) -> dict[str, bool]:
    """Delete a loop and its iterations.
    
    Args:
        loop_id: Loop ID
        
    Returns:
        Success status
    """
    storage = get_storage()
    deleted = storage.delete_loop(loop_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Loop not found")

    return {"deleted": True}


@router.post("/loops/{loop_id}/continue", response_model=ImprovementLoop)
async def continue_loop(loop_id: str) -> ImprovementLoop:
    """Continue a stopped loop.
    
    Args:
        loop_id: Loop ID
        
    Returns:
        Updated loop
    """
    storage = get_storage()
    loop = storage.get_loop(loop_id)

    if not loop:
        raise HTTPException(status_code=404, detail="Loop not found")

    if loop.status not in [ImprovementStatus.MAX_ITERATIONS, ImprovementStatus.CONVERGED]:
        raise HTTPException(
            status_code=400,
            detail=f"Loop is still {loop.status.value}",
        )

    # Create new loop with extended iterations
    improvement_loop = SelfImprovementLoop(
        generator=mock_generator,
        critic=mock_critic,
        storage=storage,
        config=ImprovementConfig(max_iterations=loop.max_iterations + 5),
    )

    # Continue from final solution
    result = await improvement_loop.run(
        task=loop.task,
        initial_solution=loop.final_solution,
    )

    return result
