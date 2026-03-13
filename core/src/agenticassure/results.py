from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A tool call made by the agent."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any | None = None


class TokenUsage(BaseModel):
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class AgentResult(BaseModel):
    """The result of running an agent on a scenario."""

    output: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    reasoning_trace: list[str] | None = None
    latency_ms: float = 0.0
    token_usage: TokenUsage | None = None
    raw_response: Any | None = None


class ScoreResult(BaseModel):
    """The result of scoring an agent's response."""

    scenario_id: str
    scorer_name: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    explanation: str = ""
    details: dict[str, Any] | None = None


class ScenarioRunResult(BaseModel):
    """Complete results for a single scenario run."""

    scenario: Scenario
    agent_result: AgentResult
    scores: list[ScoreResult] = Field(default_factory=list)
    passed: bool = False
    duration_ms: float = 0.0
    error: str | None = None
    retry_count: int = 0


class RunResult(BaseModel):
    """Complete results for a test suite run."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    suite_name: str
    scenario_results: list[ScenarioRunResult] = Field(default_factory=list)
    aggregate_score: float = 0.0
    pass_rate: float = 0.0
    total_duration_ms: float = 0.0
    model_info: dict[str, Any] | None = None

    def compute_aggregates(self) -> None:
        """Recompute aggregate_score, pass_rate, and total_duration_ms from scenario_results."""
        if not self.scenario_results:
            return
        total_score = 0.0
        passed_count = 0
        for sr in self.scenario_results:
            if sr.scores:
                total_score += sum(s.score for s in sr.scores) / len(sr.scores)
            if sr.passed:
                passed_count += 1
            self.total_duration_ms += sr.duration_ms
        n = len(self.scenario_results)
        self.aggregate_score = total_score / n
        self.pass_rate = passed_count / n


# Deferred import for forward reference
from agenticassure.scenario import Scenario  # noqa: E402

ScenarioRunResult.model_rebuild()
