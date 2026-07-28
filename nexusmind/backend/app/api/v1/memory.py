"""Memory API endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import AuthenticatedUser, DbSession
from app.db.session import Session
from app.memory.chromadb import ChromaMemoryService, get_memory_service, MemoryType
from app.api.v1.schemas import (
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult,
    MemoryStoreRequest,
    MemoryStoreResponse,
    SessionMemoryResponse,
    MemoryClearResponse,
)

router = APIRouter(prefix="/memory", tags=["memory"])


async def verify_session_ownership(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> Session:
    """Verify user owns the session for memory operations."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )
    
    result = await db.execute(
        select(Session).where(Session.id == session_uuid)
    )
    session = result.scalar_one_or_none()
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    if session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this session",
        )
    
    return session


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(
    data: MemorySearchRequest,
    user: AuthenticatedUser,
) -> MemorySearchResponse:
    """Search memory using semantic search."""
    memory_service = get_memory_service()
    
    # Map schema memory type to ChromaDB memory type
    chroma_mem_type = None
    if data.memory_type:
        try:
            chroma_mem_type = MemoryType(data.memory_type.value)
        except ValueError:
            pass
    
    # Perform semantic search
    results = await memory_service.semantic_search(
        query=data.query,
        memory_type=chroma_mem_type,
        session_id=data.session_id,
        n_results=data.n_results,
    )
    
    return MemorySearchResponse(
        results=[
            MemorySearchResult(
                id=r["id"],
                content=r["content"],
                distance=r.get("distance"),
                metadata=r.get("metadata", {}),
            )
            for r in results
        ],
        query=data.query,
    )


@router.post("/store", response_model=MemoryStoreResponse)
async def store_memory(
    data: MemoryStoreRequest,
    user: AuthenticatedUser,
) -> MemoryStoreResponse:
    """Store a memory entry."""
    memory_service = get_memory_service()
    
    # Map schema memory type to ChromaDB memory type
    try:
        chroma_mem_type = MemoryType(data.memory_type.value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid memory type: {data.memory_type}",
        )
    
    # Store based on memory type
    entry_id = str(uuid.uuid4())
    
    if chroma_mem_type == MemoryType.CONVERSATION:
        entry_id = await memory_service.store_conversation(
            session_id=data.session_id,
            role=data.metadata.get("role", "user"),
            content=data.content,
            agent_type=data.metadata.get("agent_type"),
            metadata=data.metadata,
        )
    elif chroma_mem_type == MemoryType.PLAN:
        entry_id = await memory_service.store_plan(
            session_id=data.session_id,
            plan_id=data.metadata.get("plan_id", str(uuid.uuid4())),
            task=data.metadata.get("task", ""),
            steps=data.metadata.get("steps", []),
            metadata=data.metadata,
        )
    elif chroma_mem_type == MemoryType.CODE:
        entry_id = await memory_service.store_code(
            session_id=data.session_id,
            code=data.content,
            language=data.metadata.get("language", "unknown"),
            file_path=data.metadata.get("file_path"),
            description=data.metadata.get("description"),
            metadata=data.metadata,
        )
    else:
        # Generic storage for other types
        entry_id = await memory_service.store_conversation(
            session_id=data.session_id,
            role="system",
            content=data.content,
            metadata=data.metadata,
        )
    
    return MemoryStoreResponse(id=entry_id, stored=True)


@router.get("/{session_id}", response_model=SessionMemoryResponse)
async def get_session_memory(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    memory_type: str | None = None,
    limit: int = 50,
) -> SessionMemoryResponse:
    """Get all memories for a session."""
    # Verify ownership first
    await verify_session_ownership(session_id, user, db)
    
    memory_service = get_memory_service()
    
    # Map string memory type to enum if provided
    chroma_mem_type = None
    if memory_type:
        try:
            chroma_mem_type = MemoryType(memory_type.lower())
        except ValueError:
            pass
    
    # Get conversation memory (default)
    memories = await memory_service.get_conversation(
        session_id=session_id,
        limit=limit,
    )
    
    return SessionMemoryResponse(
        session_id=session_id,
        memories=[
            MemorySearchResult(
                id=m["id"],
                content=m["content"],
                metadata=m.get("metadata", {}),
            )
            for m in memories
        ],
    )


@router.delete("/{session_id}", response_model=MemoryClearResponse)
async def clear_session_memory(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> MemoryClearResponse:
    """Clear all memories for a session."""
    # Verify ownership first
    await verify_session_ownership(session_id, user, db)
    
    memory_service = get_memory_service()
    
    # Clear all memories for this session
    deleted_counts = await memory_service.clear_session(session_id)
    
    return MemoryClearResponse(
        session_id=session_id,
        cleared=True,
        deleted_counts=deleted_counts,
    )


@router.get("/{session_id}/plans", response_model=list[MemorySearchResult])
async def get_session_plans(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
) -> list[MemorySearchResult]:
    """Get all plans for a session."""
    # Verify ownership first
    await verify_session_ownership(session_id, user, db)
    
    memory_service = get_memory_service()
    
    # Get all plans from the plans collection
    try:
        collection = memory_service.collections.get(MemoryType.PLAN)
        if collection:
            results = collection.get(where={"session_id": session_id})
            return [
                MemorySearchResult(
                    id=doc_id,
                    content=results["documents"][i] if results.get("documents") else "",
                    metadata=results["metadatas"][i] if results.get("metadatas") else {},
                )
                for i, doc_id in enumerate(results["ids"])
                if results["ids"]
            ]
    except Exception:
        pass
    
    return []


@router.get("/{session_id}/code", response_model=list[MemorySearchResult])
async def get_session_code(
    session_id: str,
    user: AuthenticatedUser,
    db: DbSession,
    language: str | None = None,
) -> list[MemorySearchResult]:
    """Get all code snippets for a session."""
    # Verify ownership first
    await verify_session_ownership(session_id, user, db)
    
    memory_service = get_memory_service()
    
    # Search code semantically
    results = await memory_service.search_code(
        query="",  # Empty query to get all
        language=language,
        session_id=session_id,
        n_results=100,
    )
    
    return [
        MemorySearchResult(
            id=r["id"],
            content=r["content"],
            distance=r.get("distance"),
            metadata=r.get("metadata", {}),
        )
        for r in results
    ]
