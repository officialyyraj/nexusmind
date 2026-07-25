"""ChromaDB memory service for semantic storage and retrieval."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import chromadb
from chromadb.config import Settings

from app.config import get_settings


class MemoryType(str, Enum):
    """Types of memory that can be stored."""

    CONVERSATION = "conversation"
    PLAN = "plan"
    FIX = "fix"
    OUTPUT = "output"
    EMBEDDING = "embedding"
    CODE = "code"
    DOCUMENTATION = "documentation"
    TASK = "task"


@dataclass
class MemoryEntry:
    """A memory entry with metadata."""

    id: str
    content: str
    memory_type: MemoryType
    session_id: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embeddings: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class ConversationMemory:
    """Store for conversation messages."""

    messages: list[dict[str, Any]]
    agent_type: str | None = None
    turn_count: int = 0


@dataclass
class PlanMemory:
    """Store for task plans."""

    plan_id: str
    task: str
    steps: list[dict[str, Any]]
    status: str = "pending"
    completed_steps: list[str] = field(default_factory=list)


@dataclass
class FixMemory:
    """Store for bug fixes."""

    bug_description: str
    root_cause: str
    fix_code: str
    verification: str | None = None


@dataclass
class OutputMemory:
    """Store for previous outputs/artifacts."""

    output_type: str  # file, artifact, result
    path: str | None = None
    content: str | None = None
    mime_type: str | None = None


class ChromaMemoryService:
    """ChromaDB-based memory service for all memory types."""

    COLLECTION_CONVERSATIONS = "conversations"
    COLLECTION_PLANS = "plans"
    COLLECTION_FIXES = "fixes"
    COLLECTION_OUTPUTS = "outputs"
    COLLECTION_EMBEDDINGS = "embeddings"
    COLLECTION_CODE = "code"
    COLLECTION_DOCS = "documentation"
    COLLECTION_TASKS = "tasks"

    def __init__(self):
        self.settings = get_settings()
        self.client = chromadb.PersistentClient(
            path=self.settings.chromadb_persist_directory,
        )

        # Create collections for each memory type
        self._init_collections()

    def _init_collections(self) -> None:
        """Initialize all memory collections."""
        self.collections = {
            MemoryType.CONVERSATION: self.client.get_or_create_collection(
                name=self.COLLECTION_CONVERSATIONS,
                metadata={"description": "Conversation messages"},
            ),
            MemoryType.PLAN: self.client.get_or_create_collection(
                name=self.COLLECTION_PLANS,
                metadata={"description": "Task plans"},
            ),
            MemoryType.FIX: self.client.get_or_create_collection(
                name=self.COLLECTION_FIXES,
                metadata={"description": "Bug fixes"},
            ),
            MemoryType.OUTPUT: self.client.get_or_create_collection(
                name=self.COLLECTION_OUTPUTS,
                metadata={"description": "Previous outputs"},
            ),
            MemoryType.EMBEDDING: self.client.get_or_create_collection(
                name=self.COLLECTION_EMBEDDINGS,
                metadata={"description": "Embeddings"},
            ),
            MemoryType.CODE: self.client.get_or_create_collection(
                name=self.COLLECTION_CODE,
                metadata={"description": "Code snippets"},
            ),
            MemoryType.DOCUMENTATION: self.client.get_or_create_collection(
                name=self.COLLECTION_DOCS,
                metadata={"description": "Documentation"},
            ),
            MemoryType.TASK: self.client.get_or_create_collection(
                name=self.COLLECTION_TASKS,
                metadata={"description": "Tasks"},
            ),
        }

    # ==================== CONVERSATION MEMORY ====================

    async def store_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a conversation message."""
        entry_id = str(uuid.uuid4())
        meta = metadata or {}
        meta.update({
            "session_id": session_id,
            "role": role,
            "agent_type": agent_type or "",
            "created_at": datetime.utcnow().isoformat(),
        })

        self.collections[MemoryType.CONVERSATION].add(
            documents=[content],
            ids=[entry_id],
            metadatas=[meta],
        )
        return entry_id

    async def get_conversation(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get conversation history for a session."""
        results = self.collections[MemoryType.CONVERSATION].get(
            where={"session_id": session_id},
            limit=limit,
        )

        messages = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                messages.append({
                    "id": doc_id,
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })

        return sorted(messages, key=lambda x: x["metadata"].get("created_at", ""))

    async def search_conversations(
        self,
        query: str,
        session_id: str | None = None,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Semantic search in conversations."""
        where_filter = {"session_id": session_id} if session_id else None

        results = self.collections[MemoryType.CONVERSATION].query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )

        return self._format_search_results(results)

    # ==================== PLAN MEMORY ====================

    async def store_plan(
        self,
        session_id: str,
        plan_id: str,
        task: str,
        steps: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a task plan."""
        entry_id = f"{session_id}_{plan_id}"
        content = json.dumps({"task": task, "steps": steps})
        meta = metadata or {}
        meta.update({
            "session_id": session_id,
            "plan_id": plan_id,
            "task": task,
            "step_count": len(steps),
            "created_at": datetime.utcnow().isoformat(),
        })

        self.collections[MemoryType.PLAN].add(
            documents=[content],
            ids=[entry_id],
            metadatas=[meta],
        )
        return entry_id

    async def get_plan(
        self,
        session_id: str,
        plan_id: str,
    ) -> dict[str, Any] | None:
        """Get a specific plan."""
        entry_id = f"{session_id}_{plan_id}"
        try:
            result = self.collections[MemoryType.PLAN].get(ids=[entry_id])
            if result["ids"]:
                content = json.loads(result["documents"][0])
                return {
                    "id": entry_id,
                    **content,
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                }
        except Exception:
            pass
        return None

    async def update_plan_status(
        self,
        session_id: str,
        plan_id: str,
        status: str,
        completed_steps: list[str] | None = None,
    ) -> bool:
        """Update plan execution status."""
        entry_id = f"{session_id}_{plan_id}"
        try:
            existing = self.collections[MemoryType.PLAN].get(ids=[entry_id])
            if not existing["ids"]:
                return False

            meta = dict(existing["metadatas"][0])
            meta["status"] = status
            if completed_steps:
                meta["completed_steps"] = json.dumps(completed_steps)
            meta["updated_at"] = datetime.utcnow().isoformat()

            self.collections[MemoryType.PLAN].update(
                ids=[entry_id],
                metadatas=[meta],
            )
            return True
        except Exception:
            return False

    async def search_plans(
        self,
        query: str,
        session_id: str | None = None,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search plans semantically."""
        where_filter = {"session_id": session_id} if session_id else None

        results = self.collections[MemoryType.PLAN].query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )

        formatted = []
        for i, doc_id in enumerate(results["ids"][0] if results["ids"] else []):
            try:
                content = json.loads(results["documents"][0][i])
                formatted.append({
                    "id": doc_id,
                    **content,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                })
            except (json.JSONDecodeError, IndexError):
                pass
        return formatted

    # ==================== FIX MEMORY ====================

    async def store_fix(
        self,
        session_id: str,
        bug_description: str,
        root_cause: str,
        fix_code: str,
        verification: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a bug fix."""
        entry_id = str(uuid.uuid4())
        content = json.dumps({
            "bug_description": bug_description,
            "root_cause": root_cause,
            "fix_code": fix_code,
            "verification": verification,
        })
        meta = metadata or {}
        meta.update({
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
        })

        self.collections[MemoryType.FIX].add(
            documents=[content],
            ids=[entry_id],
            metadatas=[meta],
        )
        return entry_id

    async def get_fix(
        self,
        fix_id: str,
    ) -> dict[str, Any] | None:
        """Get a specific fix."""
        try:
            result = self.collections[MemoryType.FIX].get(ids=[fix_id])
            if result["ids"]:
                content = json.loads(result["documents"][0])
                return {
                    "id": fix_id,
                    **content,
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                }
        except Exception:
            pass
        return None

    async def search_fixes(
        self,
        query: str,
        session_id: str | None = None,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for similar fixes."""
        where_filter = {"session_id": session_id} if session_id else None

        results = self.collections[MemoryType.FIX].query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )

        formatted = []
        for i, doc_id in enumerate(results["ids"][0] if results["ids"] else []):
            try:
                content = json.loads(results["documents"][0][i])
                formatted.append({
                    "id": doc_id,
                    **content,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                })
            except (json.JSONDecodeError, IndexError):
                pass
        return formatted

    # ==================== OUTPUT MEMORY ====================

    async def store_output(
        self,
        session_id: str,
        output_type: str,
        content: str | None = None,
        path: str | None = None,
        mime_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a previous output/artifact."""
        entry_id = str(uuid.uuid4())
        doc_content = content or path or ""
        meta = metadata or {}
        meta.update({
            "session_id": session_id,
            "output_type": output_type,
            "path": path or "",
            "mime_type": mime_type or "",
            "created_at": datetime.utcnow().isoformat(),
        })

        self.collections[MemoryType.OUTPUT].add(
            documents=[doc_content],
            ids=[entry_id],
            metadatas=[meta],
        )
        return entry_id

    async def get_outputs(
        self,
        session_id: str,
        output_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all outputs for a session."""
        where_filter = {"session_id": session_id}
        if output_type:
            where_filter["output_type"] = output_type

        results = self.collections[MemoryType.OUTPUT].get(where=where_filter)

        outputs = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                outputs.append({
                    "id": doc_id,
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })
        return outputs

    # ==================== EMBEDDINGS MEMORY ====================

    async def store_embedding(
        self,
        session_id: str,
        content: str,
        vector: list[float],
        content_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store an embedding with its vector."""
        entry_id = str(uuid.uuid4())
        meta = metadata or {}
        meta.update({
            "session_id": session_id,
            "content_type": content_type,
            "created_at": datetime.utcnow().isoformat(),
        })

        self.collections[MemoryType.EMBEDDING].add(
            documents=[content],
            embeddings=[vector],
            ids=[entry_id],
            metadatas=[meta],
        )
        return entry_id

    async def search_by_embedding(
        self,
        query_vector: list[float],
        session_id: str | None = None,
        content_type: str | None = None,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search by embedding vector similarity."""
        where_filter = {}
        if session_id:
            where_filter["session_id"] = session_id
        if content_type:
            where_filter["content_type"] = content_type

        results = self.collections[MemoryType.EMBEDDING].query(
            query_embeddings=[query_vector],
            n_results=n_results,
            where=where_filter if where_filter else None,
        )

        return self._format_search_results(results)

    async def semantic_search(
        self,
        query: str,
        memory_type: MemoryType | None = None,
        session_id: str | None = None,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Semantic search across memory types."""
        collection = self.collections.get(memory_type)
        if not collection:
            # Search all collections
            all_results = []
            for coll in self.collections.values():
                results = coll.query(
                    query_texts=[query],
                    n_results=n_results,
                    where={"session_id": session_id} if session_id else None,
                )
                all_results.extend(self._format_search_results(results))
            return sorted(all_results, key=lambda x: x.get("distance", float("inf")))[:n_results]

        where_filter = {"session_id": session_id} if session_id else None
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )
        return self._format_search_results(results)

    # ==================== CODE MEMORY ====================

    async def store_code(
        self,
        session_id: str,
        code: str,
        language: str,
        file_path: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store code snippet."""
        entry_id = str(uuid.uuid4())
        meta = metadata or {}
        meta.update({
            "session_id": session_id,
            "language": language,
            "file_path": file_path or "",
            "description": description or "",
            "created_at": datetime.utcnow().isoformat(),
        })

        self.collections[MemoryType.CODE].add(
            documents=[code],
            ids=[entry_id],
            metadatas=[meta],
        )
        return entry_id

    async def get_code(
        self,
        code_id: str,
    ) -> dict[str, Any] | None:
        """Get code snippet."""
        try:
            result = self.collections[MemoryType.CODE].get(ids=[code_id])
            if result["ids"]:
                return {
                    "id": code_id,
                    "code": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                }
        except Exception:
            pass
        return None

    async def search_code(
        self,
        query: str,
        language: str | None = None,
        session_id: str | None = None,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search code semantically."""
        where_filter = {"session_id": session_id} if session_id else {}
        if language:
            where_filter["language"] = language

        results = self.collections[MemoryType.CODE].query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter if where_filter else None,
        )
        return self._format_search_results(results)

    # ==================== UTILITY METHODS ====================

    def _format_search_results(self, results: dict) -> list[dict[str, Any]]:
        """Format ChromaDB results into standard format."""
        formatted = []
        if results.get("ids"):
            for i, doc_id in enumerate(results["ids"][0]):
                formatted.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                })
        return formatted

    async def clear_session(self, session_id: str) -> dict[str, int]:
        """Clear all memories for a session across all collections."""
        deleted_counts = {}
        for mem_type, collection in self.collections.items():
            try:
                result = collection.get(where={"session_id": session_id})
                if result["ids"]:
                    collection.delete(ids=result["ids"])
                    deleted_counts[mem_type.value] = len(result["ids"])
                else:
                    deleted_counts[mem_type.value] = 0
            except Exception:
                deleted_counts[mem_type.value] = 0
        return deleted_counts

    async def count_by_type(self, session_id: str | None = None) -> dict[str, int]:
        """Count memories by type."""
        counts = {}
        for mem_type, collection in self.collections.items():
            try:
                where_filter = {"session_id": session_id} if session_id else None
                result = collection.get(where=where_filter)
                counts[mem_type.value] = len(result["ids"])
            except Exception:
                counts[mem_type.value] = 0
        return counts

    async def delete(self, memory_type: MemoryType, entry_id: str) -> bool:
        """Delete a specific memory entry."""
        try:
            self.collections[memory_type].delete(ids=[entry_id])
            return True
        except Exception:
            return False


_memory_service: ChromaMemoryService | None = None


def get_memory_service() -> ChromaMemoryService:
    """Get the global memory service."""
    global _memory_service
    if _memory_service is None:
        _memory_service = ChromaMemoryService()
    return _memory_service

