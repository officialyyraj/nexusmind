"""Agent types and capabilities."""

from enum import Enum


class AgentType(str, Enum):
    """Enumeration of agent types."""

    PLANNER = "planner"
    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DOCUMENTATION = "documentation"
    MANAGER = "manager"


AGENT_CAPABILITIES = {
    AgentType.PLANNER: {
        "description": "Breaks down complex tasks into actionable steps",
        "tools": ["task_planning", "dependency_analysis", "priority_setting"],
        "model": "reasoning",
    },
    AgentType.RESEARCHER: {
        "description": "Gathers information and explores topics deeply",
        "tools": ["web_search", "file_read", "code_search", "documentation_search"],
        "model": "reasoning",
    },
    AgentType.CODER: {
        "description": "Writes and modifies code files",
        "tools": ["file_write", "file_edit", "code_complete", "refactor"],
        "model": "coding",
    },
    AgentType.REVIEWER: {
        "description": "Reviews code for quality, bugs, and best practices",
        "tools": ["code_analysis", "security_scan", "style_check"],
        "model": "reasoning",
    },
    AgentType.TESTER: {
        "description": "Writes and runs tests to verify functionality",
        "tools": ["test_write", "test_run", "coverage_analysis"],
        "model": "coding",
    },
    AgentType.DOCUMENTATION: {
        "description": "Generates documentation for code and features",
        "tools": ["doc_generate", "readme_write", "api_docs"],
        "model": "writing",
    },
    AgentType.MANAGER: {
        "description": "Coordinates other agents and manages workflow",
        "tools": ["task_delegate", "progress_track", "agent_coordinate"],
        "model": "reasoning",
    },
}


def get_agent_capabilities(agent_type: AgentType) -> dict:
    """Get capabilities for an agent type."""
    return AGENT_CAPABILITIES.get(agent_type, {})


def get_all_agent_types() -> list[dict]:
    """Get all agent types with their capabilities."""
    return [
        {
            "type": agent_type.value,
            **capabilities,
        }
        for agent_type, capabilities in AGENT_CAPABILITIES.items()
    ]
