"""Agents API endpoints."""

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/types")
async def list_agent_types() -> list[dict[str, Any]]:
    """List all agent types."""
    return [
        {"type": "planner", "description": "Task decomposition and planning"},
        {"type": "researcher", "description": "Context gathering and research"},
        {"type": "coder", "description": "Code implementation"},
        {"type": "reviewer", "description": "Code quality analysis"},
        {"type": "tester", "description": "Testing and validation"},
        {"type": "documentation", "description": "Documentation generation"},
        {"type": "manager", "description": "Agent coordination"},
    ]


@router.get("/{agent_type}/capabilities")
async def get_agent_capabilities(agent_type: str) -> dict[str, Any]:
    """Get capabilities for an agent type."""
    return {
        "type": agent_type,
        "capabilities": ["reasoning", "planning", "execution"],
        "tools": ["terminal", "file_editor", "search"],
    }
