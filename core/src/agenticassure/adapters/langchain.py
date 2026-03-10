from __future__ import annotations

import time
from typing import Any

from agenticassure.results import AgentResult, ToolCall


class LangChainAdapter:
    """Adapter for LangChain AgentExecutor."""

    def __init__(self, agent_executor: Any) -> None:
        try:
            from langchain.agents import AgentExecutor
        except ImportError as e:
            raise ImportError(
                "langchain package is required for LangChainAdapter. "
                "Install it with: pip install agenticassure[langchain]"
            ) from e
        if not isinstance(agent_executor, AgentExecutor):
            raise TypeError(f"Expected AgentExecutor, got {type(agent_executor)}")
        self.agent_executor = agent_executor

    def run(self, input: str, context: dict[str, Any] | None = None) -> AgentResult:
        """Run the LangChain agent and return structured results."""
        invoke_input: dict[str, Any] = {"input": input}
        if context:
            invoke_input.update(context)

        start = time.perf_counter()
        result = self.agent_executor.invoke(invoke_input, return_only_outputs=False)
        latency_ms = (time.perf_counter() - start) * 1000

        tool_calls: list[ToolCall] = []
        intermediate_steps = result.get("intermediate_steps", [])
        reasoning_trace: list[str] = []
        for action, observation in intermediate_steps:
            tool_calls.append(
                ToolCall(
                    name=action.tool,
                    arguments=(
                        action.tool_input
                        if isinstance(action.tool_input, dict)
                        else {"input": action.tool_input}
                    ),
                    result=str(observation),
                )
            )
            reasoning_trace.append(f"Tool: {action.tool} -> {observation}")

        return AgentResult(
            output=result.get("output", ""),
            tool_calls=tool_calls,
            reasoning_trace=reasoning_trace if reasoning_trace else None,
            latency_ms=latency_ms,
        )
