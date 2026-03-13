from __future__ import annotations

import time
from typing import Any

from agenticassure.results import AgentResult, TokenUsage, ToolCall


class OpenAIAdapter:
    """Adapter for OpenAI chat completion agents with function calling."""

    def __init__(
        self,
        model: str = "gpt-4",
        tools: list[dict[str, Any]] | None = None,
        system_prompt: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        try:
            import openai
        except ImportError as e:
            raise ImportError(
                "openai package is required for OpenAIAdapter. "
                "Install it with: pip install agenticassure[openai]"
            ) from e
        self.model = model
        self.tools = tools
        self.system_prompt = system_prompt
        self.client = openai.OpenAI(api_key=api_key) if api_key else openai.OpenAI()
        self.kwargs = kwargs

    def run(self, input: str, context: dict[str, Any] | None = None) -> AgentResult:
        """Run the OpenAI agent and return structured results."""
        import json

        messages: list[dict[str, Any]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": input})

        kwargs: dict[str, Any] = {"model": self.model, "messages": messages, **self.kwargs}
        if self.tools:
            kwargs["tools"] = self.tools

        start = time.perf_counter()
        response = self.client.chat.completions.create(**kwargs)
        latency_ms = (time.perf_counter() - start) * 1000

        choice = response.choices[0]
        message = choice.message

        tool_calls: list[ToolCall] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        name=tc.function.name,
                        arguments=(
                            json.loads(tc.function.arguments) if tc.function.arguments else {}
                        ),
                    )
                )

        token_usage = None
        if response.usage:
            token_usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            )

        return AgentResult(
            output=message.content or "",
            tool_calls=tool_calls,
            latency_ms=latency_ms,
            token_usage=token_usage,
            raw_response=response.model_dump(),
        )
