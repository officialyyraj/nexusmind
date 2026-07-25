"""Logging utilities for MCP module."""

import logging
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Get a logger for MCP.
    
    Args:
        name: Logger name
        level: Optional logging level
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(f"mcp.{name}")
    if level is not None:
        logger.setLevel(level)
    elif not logger.level:
        logger.setLevel(logging.INFO)
    return logger
