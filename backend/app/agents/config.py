"""Agent configuration loading.

This module loads agent definitions from a YAML file
and provides a simple way to access them.
"""
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

_agent_configs: Optional[Dict[str, Any]] = None

def load_agent_configs():
    """Load agent configurations from the YAML file."""
    global _agent_configs
    if _agent_configs is None:
        config_path = Path(__file__).parent / "agents.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                _agent_configs = yaml.safe_load(f).get("agents", {})
        else:
            _agent_configs = {}

def get_agent_config(agent_name: str) -> Optional[Dict[str, Any]]:
    """Get the configuration for a specific agent.

    Args:
        agent_name: The name of the agent (e.g., "planner").

    Returns:
        A dictionary with the agent's configuration, or None if not found.
    """
    if _agent_configs is None:
        load_agent_configs()
    
    return _agent_configs.get(agent_name)

