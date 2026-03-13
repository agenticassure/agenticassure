"""Tests for result data models."""

import pytest

from agenticassure.results import (
    AgentResult,
    RunResult,
    ScenarioRunResult,
    ScoreResult,
    TokenUsage,
    ToolCall,
)
from agenticassure.scenario import Scenario


class TestToolCall:
    def test_basic(self):
        tc = ToolCall(name="search", arguments={"q": "test"}, result="found")
        assert tc.name == "search"
        assert tc.arguments == {"q": "test"}
        assert tc.result == "found"


class TestTokenUsage:
    def test_total(self):
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        assert usage.total_tokens == 150


class TestAgentResult:
    def test_minimal(self):
        r = AgentResult(output="hello")
        assert r.output == "hello"
        assert r.tool_calls == []
        assert r.latency_ms == 0.0


class TestScoreResult:
    def test_score_bounds(self):
        sr = ScoreResult(scenario_id="x", scorer_name="test", score=0.5, passed=True)
        assert sr.score == 0.5

    def test_score_invalid(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ScoreResult(scenario_id="x", scorer_name="test", score=1.5, passed=True)


class TestRunResult:
    def test_compute_aggregates(self):
        scenario = Scenario(name="s1", input="test")
        agent_result = AgentResult(output="response")
        score = ScoreResult(scenario_id=scenario.id, scorer_name="passfail", score=1.0, passed=True)
        sr = ScenarioRunResult(
            scenario=scenario,
            agent_result=agent_result,
            scores=[score],
            passed=True,
            duration_ms=100.0,
        )
        run = RunResult(suite_name="test", scenario_results=[sr])
        run.compute_aggregates()
        assert run.pass_rate == 1.0
        assert run.aggregate_score == 1.0
        assert run.total_duration_ms == 100.0
