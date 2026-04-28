"""Tool registry — maps tool names to their implementations."""

import logging
from typing import Any, Dict

from .base import BaseTool
from .calendar_tool import calendar_tool
from .email_tool import email_tool

logger = logging.getLogger(__name__)

_REGISTRY: Dict[str, BaseTool] = {
    calendar_tool.name: calendar_tool,
    email_tool.name:    email_tool,
}


def execute_tool(name: str, **kwargs) -> Dict[str, Any]:
    """Look up a tool by name and execute it with the given arguments."""
    tool = _REGISTRY.get(name)
    if tool is None:
        logger.error(f"Unknown tool: {name}")
        return {"success": False, "result": None, "error": f"Unknown tool: {name}"}
    return tool.execute(**kwargs)
