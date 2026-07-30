"""Storage for improvement loop iterations using ChromaDB."""

import uuid
from datetime import datetime
from typing import Any

import chromadb
from chromadb.config import Settings

from app.agents.improvement.schemas import (
    CritiqueResult,
    ImprovementConfig,
    ImprovementIteration,
    ImprovementLoop,
    ImprovementStatus,
    IterationPhase,
)


class IterationStorage:
    """ChromaDB storage for improvement iterations."""

    COLLECTION_NAME = "improvement_iterations"

    def __init__(self, persist_directory: str = "/tmp/chroma_db"):
        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
            )
        )
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Ensure the collection exists."""
        try:
            self._client.get_collection(self.COLLECTION_NAME)
        except Exception:
            self._client.create_collection(
                self.COLLECTION_NAME,
                metadata={"description": "Improvement loop iterations"},
            )

    def _collection(self):
        """Get the collection."""
        return self._client.get_collection(self.COLLECTION_NAME)

    def save_loop(self, loop: ImprovementLoop) -> str:
        """Save an improvement loop.
        
        Args:
            loop: ImprovementLoop to save
            
        Returns:
            Loop ID
        """
        collection = self._collection()

        # Save loop metadata
        loop_doc = {
            "loop_id": loop.loop_id,
            "task": loop.task,
            "status": loop.status.value,
            "current_iteration": loop.current_iteration,
            "max_iterations": loop.max_iterations,
            "quality_threshold": loop.quality_threshold,
            "started_at": loop.started_at.isoformat(),
            "completed_at": loop.completed_at.isoformat() if loop.completed_at else None,
            "final_solution": loop.final_solution or "",
            "error": loop.error or "",
        }

        collection.add(
            documents=[str(loop_doc)],
            ids=[f"loop_{loop.loop_id}"],
            metadatas=[{
                "type": "loop",
                "loop_id": loop.loop_id,
                "task": loop.task[:100],
                "status": loop.status.value,
                "quality": loop.latest_quality or 0.0,
            }],
        )

        # Save each iteration
        for iteration in loop.iterations:
            self._save_iteration(loop.loop_id, iteration)

        return loop.loop_id

    def _save_iteration(
        self,
        loop_id: str,
        iteration: ImprovementIteration,
    ) -> None:
        """Save a single iteration.
        
        Args:
            loop_id: Parent loop ID
            iteration: Iteration to save
        """
        collection = self._collection()

        # Create iteration document
        iteration_doc = {
            "loop_id": loop_id,
            "iteration": iteration.iteration,
            "phase": iteration.phase.value,
            "solution": iteration.solution,
            "changes": iteration.changes,
            "quality_score": iteration.critique.quality_score if iteration.critique else 0.0,
        }

        iteration_id = f"{loop_id}_iter_{iteration.iteration}"

        collection.add(
            documents=[str(iteration_doc)],
            ids=[iteration_id],
            metadatas=[{
                "type": "iteration",
                "loop_id": loop_id,
                "iteration": iteration.iteration,
                "phase": iteration.phase.value,
                "quality_score": iteration.critique.quality_score if iteration.critique else 0.0,
            }],
        )

    def get_loop(self, loop_id: str) -> ImprovementLoop | None:
        """Get a loop by ID.
        
        Args:
            loop_id: Loop ID
            
        Returns:
            ImprovementLoop or None
        """
        collection = self._collection()

        try:
            result = collection.get(
                where={"loop_id": loop_id, "type": "loop"},
                limit=1,
            )

            if not result["ids"]:
                return None

            # Get all iterations for this loop
            iterations_result = collection.get(
                where={"loop_id": loop_id, "type": "iteration"},
            )

            # Parse iterations
            iterations = []
            for i, iteration_id in enumerate(iterations_result["ids"]):
                doc = eval(iterations_result["documents"][i])
                iterations.append(ImprovementIteration(
                    iteration=doc.get("iteration", i + 1),
                    phase=IterationPhase(doc.get("phase", "generate")),
                    solution=doc.get("solution", ""),
                    changes=doc.get("changes", ""),
                    critique=CritiqueResult(
                        quality_score=doc.get("quality_score", 0.0),
                        issues=[],
                        suggestions=[],
                    ) if doc.get("quality_score") else None,
                ))

            # Sort by iteration number
            iterations.sort(key=lambda x: x.iteration)

            # Parse loop metadata
            loop_doc = eval(result["documents"][0])
            metadata = result["metadatas"][0]

            return ImprovementLoop(
                loop_id=loop_id,
                task=loop_doc.get("task", ""),
                status=ImprovementStatus(metadata.get("status", "running")),
                current_iteration=loop_doc.get("current_iteration", 0),
                max_iterations=loop_doc.get("max_iterations", 10),
                quality_threshold=loop_doc.get("quality_threshold", 0.9),
                started_at=datetime.fromisoformat(loop_doc.get("started_at", datetime.utcnow().isoformat())),
                completed_at=datetime.fromisoformat(loop_doc["completed_at"]) if loop_doc.get("completed_at") else None,
                iterations=iterations,
                final_solution=loop_doc.get("final_solution") or None,
                error=loop_doc.get("error") or None,
            )

        except Exception:
            return None

    def get_iterations(
        self,
        loop_id: str,
        limit: int = 100,
    ) -> list[ImprovementIteration]:
        """Get iterations for a loop.
        
        Args:
            loop_id: Loop ID
            limit: Maximum iterations to return
            
        Returns:
            List of iterations
        """
        collection = self._collection()

        result = collection.get(
            where={"loop_id": loop_id, "type": "iteration"},
            limit=limit,
        )

        iterations = []
        for i, doc_str in enumerate(result["documents"]):
            doc = eval(doc_str)
            iterations.append(ImprovementIteration(
                iteration=doc.get("iteration", i + 1),
                phase=IterationPhase(doc.get("phase", "generate")),
                solution=doc.get("solution", ""),
                changes=doc.get("changes", ""),
            ))

        return sorted(iterations, key=lambda x: x.iteration)

    def search_loops(
        self,
        task_query: str | None = None,
        min_quality: float | None = None,
        status: ImprovementStatus | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for loops.
        
        Args:
            task_query: Text to search in tasks
            min_quality: Minimum quality score
            status: Filter by status
            limit: Maximum results
            
        Returns:
            List of loop metadata dicts
        """
        collection = self._collection()

        where_filter = {"type": "loop"}
        if status:
            where_filter["status"] = status.value

        result = collection.get(
            where=where_filter,
            limit=limit * 2,  # Get more for filtering
        )

        loops = []
        for i, metadata in enumerate(result["metadatas"]):
            if metadata.get("type") != "loop":
                continue

            # Apply additional filters
            if min_quality and metadata.get("quality", 0.0) < min_quality:
                continue

            loops.append({
                "loop_id": metadata.get("loop_id"),
                "task": metadata.get("task", ""),
                "status": metadata.get("status"),
                "quality": metadata.get("quality", 0.0),
            })

        return loops[:limit]

    def list_recent_loops(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent loops.
        
        Args:
            limit: Maximum results
            
        Returns:
            List of recent loops
        """
        collection = self._collection()

        result = collection.get(
            where={"type": "loop"},
            limit=limit,
        )

        loops = []
        for i, metadata in enumerate(result["metadatas"]):
            if metadata.get("type") == "loop":
                loops.append({
                    "loop_id": metadata.get("loop_id"),
                    "task": metadata.get("task", ""),
                    "status": metadata.get("status"),
                    "quality": metadata.get("quality", 0.0),
                })

        return loops

    def delete_loop(self, loop_id: str) -> bool:
        """Delete a loop and its iterations.
        
        Args:
            loop_id: Loop ID
            
        Returns:
            True if deleted
        """
        collection = self._collection()

        # Get all IDs for this loop
        result = collection.get(
            where={"loop_id": loop_id},
        )

        if result["ids"]:
            collection.delete(ids=result["ids"])
            return True

        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Statistics dict
        """
        collection = self._collection()

        # Count loops
        loops_result = collection.get(where={"type": "loop"})
        total_loops = len(loops_result["ids"])

        # Count iterations
        iterations_result = collection.get(where={"type": "iteration"})
        total_iterations = len(iterations_result["ids"])

        # Count by status
        status_counts = {}
        for metadata in loops_result["metadatas"]:
            status = metadata.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Average quality
        qualities = [
            m.get("quality", 0.0)
            for m in loops_result["metadatas"]
            if m.get("quality") is not None
        ]
        avg_quality = sum(qualities) / len(qualities) if qualities else 0.0

        return {
            "total_loops": total_loops,
            "total_iterations": total_iterations,
            "status_counts": status_counts,
            "average_quality": avg_quality,
        }


# Global storage instance
_iteration_storage: IterationStorage | None = None


def get_iteration_storage() -> IterationStorage:
    """Get the global iteration storage.
    
    Returns:
        IterationStorage instance
    """
    global _iteration_storage
    if _iteration_storage is None:
        _iteration_storage = IterationStorage()
    return _iteration_storage
