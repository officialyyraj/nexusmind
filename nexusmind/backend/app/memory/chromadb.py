"""ChromaDB memory service for semantic storage and retrieval."""

import uuid
from datetime import datetime
from typing import Any

import chromadb

from app.config import get_settings


class MemoryService:
    """Memory service using ChromaDB for semantic storage."""

    def __init__(self):
        self.settings = get_settings()
        self.client = chromadb.PersistentClient(
            path=self.settings.chromadb_persist_directory,
        )
        self.collection = self.client.get_or_create_collection(
            name=self.settings.chromadb_collection_name,
        )

    async def store(
        self,
        content: str,
        session_id: str,
        metadata: dict[str, Any] | None = None,
        document_id: str | None = None,
    ) -> str:
        """Store a memory entry."""
        doc_id = document_id or str(uuid.uuid4())
        doc_metadata = metadata or {}
        doc_metadata.update({
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
        })

        self.collection.add(
            documents=[content],
            ids=[doc_id],
            metadatas=[doc_metadata],
        )

        return doc_id

    async def search(
        self,
        query: str,
        session_id: str | None = None,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for relevant memories."""
        where_filter = {"session_id": session_id} if session_id else None

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )

        memories = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                memories.append({
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })

        return memories

    async def delete(self, document_id: str) -> bool:
        """Delete a memory entry."""
        try:
            self.collection.delete(ids=[document_id])
            return True
        except Exception:
            return False

    async def get(self, document_id: str) -> dict[str, Any] | None:
        """Get a specific memory entry."""
        try:
            result = self.collection.get(ids=[document_id])
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                }
            return None
        except Exception:
            return None

    async def clear_session(self, session_id: str) -> int:
        """Clear all memories for a session."""
        try:
            result = self.collection.get(where={"session_id": session_id})
            if result["ids"]:
                self.collection.delete(ids=result["ids"])
                return len(result["ids"])
            return 0
        except Exception:
            return 0

    async def count(self, session_id: str | None = None) -> int:
        """Count memories."""
        try:
            if session_id:
                result = self.collection.get(where={"session_id": session_id})
            else:
                result = self.collection.get()
            return len(result["ids"])
        except Exception:
            return 0


_memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """Get the global memory service."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
