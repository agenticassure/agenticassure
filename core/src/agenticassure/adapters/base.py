from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from agenticassure.results import AgentResult


@runtime_checkable
class AgentAdapter(Protocol):
    """Protocol that all agent adapters must implement."""

    def run(self, input: str, context: dict[str, Any] | None = None) -> AgentResult:
        """Execute the agent with the given input and return structured results."""
        ...
