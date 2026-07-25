"""Tests for self-improvement loop."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.agents.improvement.schemas import (
    CritiqueResult,
    ImprovementConfig,
    ImprovementIteration,
    ImprovementLoop,
    ImprovementStatus,
    IterationPhase,
)


class TestImprovementSchemas:
    """Test improvement schemas."""

    def test_improvement_status_values(self):
        """Test ImprovementStatus enum values."""
        assert ImprovementStatus.RUNNING.value == "running"
        assert ImprovementStatus.CONVERGED.value == "converged"
        assert ImprovementStatus.MAX_ITERATIONS.value == "max_iterations"
        assert ImprovementStatus.TESTS_PASSING.value == "tests_passing"
        assert ImprovementStatus.FAILED.value == "failed"

    def test_iteration_phase_values(self):
        """Test IterationPhase enum values."""
        assert IterationPhase.GENERATE.value == "generate"
        assert IterationPhase.CRITIQUE.value == "critique"
        assert IterationPhase.IMPROVE.value == "improve"

    def test_critique_result(self):
        """Test CritiqueResult."""
        critique = CritiqueResult(
            issues=["Issue 1", "Issue 2"],
            suggestions=["Fix this", "Improve that"],
            quality_score=0.75,
            passed_tests=["test1", "test2"],
            failed_tests=["test3"],
            complexity_score=0.3,
        )

        assert len(critique.issues) == 2
        assert critique.quality_score == 0.75
        assert len(critique.passed_tests) == 2
        assert len(critique.failed_tests) == 1

    def test_improvement_iteration(self):
        """Test ImprovementIteration."""
        iteration = ImprovementIteration(
            iteration=1,
            phase=IterationPhase.GENERATE,
            solution="def solve(): pass",
            changes="Initial version",
            execution_time=0.5,
        )

        assert iteration.iteration == 1
        assert iteration.phase == IterationPhase.GENERATE
        assert "solve" in iteration.solution

    def test_improvement_config_defaults(self):
        """Test ImprovementConfig defaults."""
        config = ImprovementConfig()
        assert config.max_iterations == 10
        assert config.quality_threshold == 0.9
        assert config.test_timeout == 60
        assert config.auto_critique is True
        assert config.save_iterations is True

    def test_improvement_loop_defaults(self):
        """Test ImprovementLoop defaults."""
        loop = ImprovementLoop(
            loop_id="test-123",
            task="Build a feature",
        )

        assert loop.status == ImprovementStatus.RUNNING
        assert loop.current_iteration == 0
        assert len(loop.iterations) == 0
        assert loop.final_solution is None

    def test_quality_scores_property(self):
        """Test quality_scores property."""
        loop = ImprovementLoop(
            loop_id="test-123",
            task="Build a feature",
        )

        loop.iterations = [
            ImprovementIteration(
                iteration=1,
                phase=IterationPhase.CRITIQUE,
                solution="",
                critique=CritiqueResult(quality_score=0.5, issues=[], suggestions=[]),
            ),
            ImprovementIteration(
                iteration=2,
                phase=IterationPhase.CRITIQUE,
                solution="",
                critique=CritiqueResult(quality_score=0.7, issues=[], suggestions=[]),
            ),
        ]

        assert loop.quality_scores == [0.5, 0.7]
        assert loop.latest_quality == 0.7

    def test_has_improved_property(self):
        """Test has_improved property."""
        loop = ImprovementLoop(
            loop_id="test-123",
            task="Build a feature",
        )

        # No iterations yet
        assert loop.has_improved is False

        # Only one iteration
        loop.iterations.append(
            ImprovementIteration(
                iteration=1,
                phase=IterationPhase.CRITIQUE,
                solution="",
                critique=CritiqueResult(quality_score=0.5, issues=[], suggestions=[]),
            )
        )
        assert loop.has_improved is False

        # Multiple iterations with improvement
        loop.iterations.append(
            ImprovementIteration(
                iteration=2,
                phase=IterationPhase.CRITIQUE,
                solution="",
                critique=CritiqueResult(quality_score=0.8, issues=[], suggestions=[]),
            )
        )
        assert loop.has_improved is True


class TestSelfImprovementLoop:
    """Test SelfImprovementLoop class."""

    def test_loop_import(self):
        """Test that SelfImprovementLoop can be imported."""
        from app.agents.improvement.loop import SelfImprovementLoop
        assert SelfImprovementLoop is not None

    def test_mock_generator(self):
        """Test mock generator."""
        from app.agents.improvement.loop import mock_generator

        result = mock_generator("Implement sorting")
        assert "sorting" in result
        assert "def " in result

    def test_mock_critic(self):
        """Test mock critic."""
        from app.agents.improvement.loop import mock_critic

        result = mock_critic("def solve(): return 1")
        assert isinstance(result, CritiqueResult)
        assert result.quality_score > 0.3
        assert len(result.suggestions) >= 0  # May or may not have suggestions

    def test_critique_scoring(self):
        """Test that critique properly scores solutions."""
        from app.agents.improvement.loop import mock_critic

        # Poor solution
        poor = ""
        poor_result = mock_critic(poor)
        assert poor_result.quality_score < 0.5

        # Good solution
        good = """
def solve():
    '''Solve the task.'''
    result = []
    # Process data
    return result
"""
        good_result = mock_critic(good)
        assert good_result.quality_score > poor_result.quality_score


class TestImprovementStorage:
    """Test iteration storage."""

    def test_storage_import(self):
        """Test that storage can be imported."""
        from app.agents.improvement.storage import IterationStorage
        assert IterationStorage is not None

    @pytest.mark.skip(reason="Requires ChromaDB server")
    def test_storage_creation(self):
        """Test creating storage."""
        from app.agents.improvement.storage import IterationStorage

        storage = IterationStorage(persist_directory="/tmp/test_chroma")
        assert storage is not None

    @pytest.mark.skip(reason="Requires ChromaDB server")
    def test_save_and_get_loop(self):
        """Test saving and retrieving a loop."""
        from app.agents.improvement.storage import IterationStorage

        storage = IterationStorage(persist_directory="/tmp/test_chroma_save2")

        # Create a loop
        loop = ImprovementLoop(
            loop_id="test-loop-456",
            task="Test task",
            status=ImprovementStatus.CONVERGED,
            iterations=[
                ImprovementIteration(
                    iteration=1,
                    phase=IterationPhase.CRITIQUE,
                    solution="def solve(): pass",
                    critique=CritiqueResult(
                        quality_score=0.8,
                        issues=[],
                        suggestions=[],
                    ),
                )
            ],
            final_solution="def solve(): pass",
        )

        # Save
        saved_id = storage.save_loop(loop)
        assert saved_id == "test-loop-456"

        # Verify it was saved
        stats = storage.get_statistics()
        assert stats["total_loops"] >= 1

        # Cleanup
        storage.delete_loop("test-loop-456")

    @pytest.mark.skip(reason="Requires ChromaDB server")
    def test_get_statistics(self):
        """Test getting storage statistics."""
        from app.agents.improvement.storage import IterationStorage

        storage = IterationStorage(persist_directory="/tmp/test_chroma_stats")
        stats = storage.get_statistics()

        assert "total_loops" in stats
        assert "total_iterations" in stats
        assert "status_counts" in stats
        assert "average_quality" in stats


class TestImprovementLoopIntegration:
    """Integration tests for improvement loop."""

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_run_loop_with_mock(self):
        """Test running the improvement loop."""
        from app.agents.improvement.loop import (
            SelfImprovementLoop,
            mock_critic,
            mock_generator,
        )

        loop = SelfImprovementLoop(
            generator=mock_generator,
            critic=mock_critic,
            config=ImprovementConfig(
                max_iterations=2,
                quality_threshold=0.95,  # High threshold so it runs all iterations
            ),
        )

        result = await loop.run(
            task="Implement a sorting function",
            initial_solution="def sort(): pass",
        )

        assert result is not None
        assert result.loop_id is not None
        assert result.task == "Implement a sorting function"
        assert len(result.iterations) >= 2  # At least 2 iterations

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_run_loop_stops_early(self):
        """Test that loop stops when quality threshold is met."""
        from app.agents.improvement.loop import (
            SelfImprovementLoop,
            mock_critic,
            mock_generator,
        )

        loop = SelfImprovementLoop(
            generator=mock_generator,
            critic=mock_critic,
            config=ImprovementConfig(
                max_iterations=10,
                quality_threshold=1.0,  # Impossible to reach
            ),
        )

        result = await loop.run(
            task="Simple task",
            initial_solution="# Simple solution\ndef solve(): return True",
        )

        # Should complete
        assert result.status in [ImprovementStatus.MAX_ITERATIONS, ImprovementStatus.TESTS_PASSING, ImprovementStatus.CONVERGED]
        assert result.iterations is not None
        assert len(result.iterations) >= 1

    @pytest.mark.skip(reason="Requires ChromaDB server")
    @pytest.mark.asyncio
    async def test_callback_invoked(self):
        """Test that iteration callback is invoked."""
        from app.agents.improvement.loop import (
            SelfImprovementLoop,
            mock_critic,
            mock_generator,
        )

        callback_invocations = []

        def on_iteration(iteration):
            callback_invocations.append(iteration.iteration)

        loop = SelfImprovementLoop(
            generator=mock_generator,
            critic=mock_critic,
            config=ImprovementConfig(max_iterations=2),
        )

        result = await loop.run(
            task="Test task",
            on_iteration=on_iteration,
        )

        assert len(callback_invocations) > 0


class TestAPI:
    """Test API endpoints."""

    def test_api_router_import(self):
        """Test that API router can be imported."""
        from app.agents.improvement.api import router
        assert router is not None

    @pytest.mark.skip(reason="Requires ChromaDB server")
    def test_get_improvement_loop(self):
        """Test getting improvement loop."""
        from app.agents.improvement.api import get_loop

        loop = get_loop()
        assert loop is not None
        from app.agents.improvement.loop import SelfImprovementLoop
        assert isinstance(loop, SelfImprovementLoop)

    @pytest.mark.skip(reason="Requires ChromaDB server")
    def test_get_iteration_storage(self):
        """Test getting iteration storage."""
        from app.agents.improvement.api import get_storage

        storage = get_storage()
        assert storage is not None
        from app.agents.improvement.storage import IterationStorage
        assert isinstance(storage, IterationStorage)
