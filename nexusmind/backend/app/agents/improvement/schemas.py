"""Self-improvement loop schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ImprovementStatus(str, Enum):
    """Status of an improvement loop."""

    RUNNING = "running"
    CONVERGED = "converged"  # Quality threshold reached
    MAX_ITERATIONS = "max_iterations"  # Reached max iterations
    TESTS_PASSING = "tests_passing"  # Tests passing
    FAILED = "failed"  # Unrecoverable failure


class IterationPhase(str, Enum):
    """Phase within an iteration."""

    GENERATE = "generate"
    CRITIQUE = "critique"
    IMPROVE = "improve"


class CritiqueResult(BaseModel):
    """Result of critiquing a solution."""

    issues: list[str] = Field(default_factory=list, description="List of issues found")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score 0-1")
    passed_tests: list[str] = Field(default_factory=list, description="Tests that passed")
    failed_tests: list[str] = Field(default_factory=list, description="Tests that failed")
    complexity_score: float | None = Field(None, ge=0.0, le=1.0, description="Code complexity")


class ImprovementIteration(BaseModel):
    """Single iteration of the improvement loop."""

    iteration: int = Field(..., description="Iteration number (1-indexed)")
    phase: IterationPhase
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    solution: str = Field(..., description="Solution code at this point")
    critique: CritiqueResult | None = None
    changes: str = Field(default_factory=str, description="Summary of changes made")
    execution_time: float = Field(0.0, description="Time spent in this iteration")


class ImprovementLoop(BaseModel):
    """Complete improvement loop with all iterations."""

    loop_id: str
    task: str = Field(..., description="Original task description")
    status: ImprovementStatus = ImprovementStatus.RUNNING
    current_iteration: int = 0
    max_iterations: int = 10
    quality_threshold: float = 0.9
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    iterations: list[ImprovementIteration] = Field(default_factory=list)
    final_solution: str | None = None
    error: str | None = None

    @property
    def quality_scores(self) -> list[float]:
        """Get list of quality scores from all iterations."""
        return [
            i.critique.quality_score
            for i in self.iterations
            if i.critique and i.critique.quality_score is not None
        ]

    @property
    def latest_quality(self) -> float | None:
        """Get the latest quality score."""
        scores = self.quality_scores
        return scores[-1] if scores else None

    @property
    def has_improved(self) -> bool:
        """Check if quality has improved since start."""
        scores = self.quality_scores
        if len(scores) < 2:
            return False
        return scores[-1] > scores[0]


class ImprovementConfig(BaseModel):
    """Configuration for the improvement loop."""

    max_iterations: int = Field(10, ge=1, le=100, description="Max iterations")
    quality_threshold: float = Field(0.9, ge=0.0, le=1.0, description="Quality threshold to stop")
    test_timeout: int = Field(60, ge=1, description="Test timeout in seconds")
    auto_critique: bool = Field(True, description="Automatically critique solutions")
    save_iterations: bool = Field(True, description="Save all iterations to storage")


class IterationQuery(BaseModel):
    """Query for searching iterations."""

    loop_id: str | None = None
    task_contains: str | None = None
    min_quality: float | None = None
    max_iterations: int | None = None
    status: ImprovementStatus | None = None
    limit: int = Field(10, ge=1, le=100)
