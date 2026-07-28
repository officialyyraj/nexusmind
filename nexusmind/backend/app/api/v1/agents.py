"""Agents API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.agents.types import AgentType, AGENT_CAPABILITIES, get_all_agent_types
from app.api.v1.schemas import AgentTypeInfo, AgentCapabilitiesResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/types", response_model=list[AgentTypeInfo])
async def list_agent_types() -> list[AgentTypeInfo]:
    """List all available agent types with their capabilities."""
    return [
        AgentTypeInfo(
            type=agent_type.value,
            description=capabilities.get("description", ""),
            tools=capabilities.get("tools", []),
            model=capabilities.get("model", "reasoning"),
        )
        for agent_type, capabilities in AGENT_CAPABILITIES.items()
    ]


@router.get("/{agent_type}/capabilities", response_model=AgentCapabilitiesResponse)
async def get_agent_capabilities(agent_type: str) -> AgentCapabilitiesResponse:
    """Get detailed capabilities for a specific agent type."""
    try:
        agent_enum = AgentType(agent_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown agent type: {agent_type}. Available types: {[t.value for t in AgentType]}",
        )
    
    capabilities = AGENT_CAPABILITIES.get(agent_enum, {})
    
    return AgentCapabilitiesResponse(
        type=agent_type,
        capabilities=[
            "reasoning" if capabilities.get("model") == "reasoning" else "coding"
        ],
        tools=capabilities.get("tools", []),
    )
