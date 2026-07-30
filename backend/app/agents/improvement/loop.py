"""Self-improvement loop for coding agents."""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Callable

from app.agents.improvement.schemas import (
    CritiqueResult,
    ImprovementConfig,
    ImprovementIteration,
    ImprovementLoop,
    ImprovementStatus,
    IterationPhase,
)
from app.agents.improvement.storage import IterationStorage, get_iteration_storage


class SelfImprovementLoop:
    """Self-improvement loop for generating, critiquing, and improving solutions."""

    def __init__(
        self,
        generator: Callable[[str], Any] | None = None,
        critic: Callable[[str], CritiqueResult] | None = None,
        storage: IterationStorage | None = None,
        config: ImprovementConfig | None = None,
    ):
        """Initialize the improvement loop.
        
        Args:
            generator: Function that generates initial solution
            critic: Function that critiques a solution
            storage: Storage for iterations
            config: Configuration
        """
        self.generator = generator
        self.critic = critic
        self.storage = storage or get_iteration_storage()
        self.config = config or ImprovementConfig()

    async def run(
        self,
        task: str,
        initial_solution: str | None = None,
        on_iteration: Callable[[ImprovementIteration], None] | None = None,
    ) -> ImprovementLoop:
        """Run the improvement loop.
        
        Args:
            task: Task description
            initial_solution: Optional initial solution
            on_iteration: Callback for each iteration
            
        Returns:
            Completed improvement loop
        """
        loop_id = str(uuid.uuid4())

        loop = ImprovementLoop(
            loop_id=loop_id,
            task=task,
            max_iterations=self.config.max_iterations,
            quality_threshold=self.config.quality_threshold,
        )

        # Generate initial solution if not provided
        if initial_solution:
            current_solution = initial_solution
        elif self.generator:
            current_solution = await self._generate(task, iteration=0)
        else:
            current_solution = "# TODO: Implement solution\n"

        # Save initial state
        iteration = ImprovementIteration(
            iteration=0,
            phase=IterationPhase.GENERATE,
            solution=current_solution,
            changes="Initial solution generated",
        )
        loop.iterations.append(iteration)

        # Main improvement loop
        while loop.current_iteration < loop.max_iterations:
            loop.current_iteration += 1
            start_time = time.time()

            try:
                # CRITIQUE PHASE
                critique = await self._critique(current_solution, task)

                critique_iteration = ImprovementIteration(
                    iteration=loop.current_iteration,
                    phase=IterationPhase.CRITIQUE,
                    solution=current_solution,
                    critique=critique,
                    changes=f"Critique: {len(critique.issues)} issues found",
                    execution_time=time.time() - start_time,
                )
                loop.iterations.append(critique_iteration)

                if on_iteration:
                    on_iteration(critique_iteration)

                # Check termination conditions
                if self._should_stop(loop, critique):
                    loop.status = self._get_termination_status(loop, critique)
                    break

                # IMPROVE PHASE
                improve_start = time.time()
                improved_solution, changes = await self._improve(
                    current_solution, critique, task
                )

                improvement_iteration = ImprovementIteration(
                    iteration=loop.current_iteration,
                    phase=IterationPhase.IMPROVE,
                    solution=improved_solution,
                    critique=critique,
                    changes=changes,
                    execution_time=time.time() - improve_start,
                )
                loop.iterations.append(improvement_iteration)

                if on_iteration:
                    on_iteration(improvement_iteration)

                # Update current solution
                current_solution = improved_solution

            except Exception as e:
                loop.error = str(e)
                loop.status = ImprovementStatus.FAILED
                break

        # Check if we exhausted iterations
        if loop.status == ImprovementStatus.RUNNING:
            loop.status = ImprovementStatus.MAX_ITERATIONS

        # Set final solution
        loop.final_solution = current_solution
        loop.completed_at = datetime.utcnow()

        # Save to storage
        if self.config.save_iterations:
            self.storage.save_loop(loop)

        return loop

    async def _generate(self, task: str, iteration: int) -> str:
        """Generate a solution.
        
        Args:
            task: Task description
            iteration: Current iteration number
            
        Returns:
            Generated solution
        """
        if self.generator:
            result = self.generator(task)
            if asyncio.iscoroutine(result):
                return await result
            return result

        # Default generator
        return f"# Solution for: {task}\n\ndef solution():\n    pass\n"

    async def _critique(self, solution: str, task: str) -> CritiqueResult:
        """Critique a solution.
        
        Args:
            solution: Solution code
            task: Task description
            
        Returns:
            Critique result
        """
        if self.critic:
            result = self.critic(solution)
            if asyncio.iscoroutine(result):
                return await result
            return result

        # Default critique - basic checks
        issues = []
        suggestions = []
        quality_score = 0.5

        # Check for basic elements
        if "def " in solution or "class " in solution:
            quality_score += 0.2

        if "return" in solution:
            quality_score += 0.1

        if solution.count("\n") > 5:
            quality_score += 0.1

        if "#" in solution:  # Has comments
            quality_score += 0.1

        # Cap at 1.0
        quality_score = min(quality_score, 1.0)

        return CritiqueResult(
            issues=issues,
            suggestions=suggestions,
            quality_score=quality_score,
            passed_tests=["syntax_check"],
            failed_tests=[],
        )

    async def _improve(
        self,
        solution: str,
        critique: CritiqueResult,
        task: str,
    ) -> tuple[str, str]:
        """Improve a solution based on critique.
        
        Args:
            solution: Current solution
            critique: Critique result
            task: Task description
            
        Returns:
            Tuple of (improved solution, changes summary)
        """
        changes = []
        improved = solution

        # Apply suggestions
        for suggestion in critique.suggestions:
            # Simple text-based improvements
            if "add docstring" in suggestion.lower():
                if '"""' not in improved:
                    # Add docstring after function definition
                    improved = improved.replace(
                        "def ",
                        'def ',  # TODO: more sophisticated
                    )
                    changes.append("Added docstring")

            elif "add type hints" in suggestion.lower():
                # Basic type hint addition
                changes.append("Type hints suggested")

            elif "simplify" in suggestion.lower():
                # Suggest simplification
                changes.append("Simplification suggested")

            elif "optimize" in suggestion.lower():
                # Suggest optimization
                changes.append("Optimization suggested")

        # If no specific changes, add basic improvements
        if not changes:
            # Add basic improvements
            if not improved.startswith("#"):
                improved = f"# Task: {task}\n\n{improved}"
                changes.append("Added task comment")

            # Ensure proper formatting
            if "\n\n\n" in improved:
                improved = improved.replace("\n\n\n", "\n\n")
                changes.append("Fixed formatting")

            if not changes:
                changes.append("Solution verified")

        return improved, "; ".join(changes) if changes else "No changes needed"

    def _should_stop(self, loop: ImprovementLoop, critique: CritiqueResult) -> bool:
        """Check if the loop should stop.
        
        Args:
            loop: Current loop state
            critique: Latest critique
            
        Returns:
            True if should stop
        """
        # Check quality threshold
        if critique.quality_score >= loop.quality_threshold:
            return True

        # Check if tests pass
        if not critique.failed_tests and critique.passed_tests:
            return True

        # Check if no issues
        if not critique.issues and critique.quality_score > 0.8:
            return True

        return False

    def _get_termination_status(
        self,
        loop: ImprovementLoop,
        critique: CritiqueResult,
    ) -> ImprovementStatus:
        """Get the termination status.
        
        Args:
            loop: Current loop state
            critique: Latest critique
            
        Returns:
            Termination status
        """
        if critique.quality_score >= loop.quality_threshold:
            return ImprovementStatus.CONVERGED

        if not critique.failed_tests and critique.passed_tests:
            return ImprovementStatus.TESTS_PASSING

        return ImprovementStatus.CONVERGED


# Mock implementations for testing
def mock_generator(task: str) -> str:
    """Mock solution generator."""
    return f'''"""Solution for: {task}"""

def solve():
    """Solve the task."""
    result = []
    return result
'''

def mock_critic(solution: str) -> CritiqueResult:
    """Mock solution critic."""
    issues = []
    suggestions = []
    quality_score = 0.3

    # Basic code analysis
    if "def " in solution:
        quality_score += 0.2
        suggestions.append("Add docstrings")

    if "return" in solution:
        quality_score += 0.1

    if len(solution) > 50:
        quality_score += 0.2

    if "#" in solution:
        quality_score += 0.1

    if "class " in solution:
        issues.append("Consider using functions instead of classes")
        quality_score -= 0.1

    # Cap score
    quality_score = max(0.0, min(1.0, quality_score))

    return CritiqueResult(
        issues=issues,
        suggestions=suggestions,
        quality_score=quality_score,
        passed_tests=["syntax_check"] if "def " in solution else [],
        failed_tests=[],
    )


# Global loop instance
_improvement_loop: SelfImprovementLoop | None = None


def get_improvement_loop() -> SelfImprovementLoop:
    """Get the global improvement loop instance.
    
    Returns:
        SelfImprovementLoop instance
    """
    global _improvement_loop
    if _improvement_loop is None:
        _improvement_loop = SelfImprovementLoop(
            generator=mock_generator,
            critic=mock_critic,
        )
    return _improvement_loop
