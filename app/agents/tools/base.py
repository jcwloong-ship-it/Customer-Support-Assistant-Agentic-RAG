"""Abstract base class for all agent tools."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class BaseTool(ABC):

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]: ...

    def validate_params(
        self, required: List[str], provided: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Return (is_valid, list_of_missing_params)."""
        missing = [p for p in required if not provided.get(p)]
        return (not missing), missing

    def _ok(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "result": result, "error": None}

    def _err(self, msg: str) -> Dict[str, Any]:
        logger.error(f"[{self.name}] {msg}")
        return {"success": False, "result": None, "error": msg}
