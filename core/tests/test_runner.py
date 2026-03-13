"""Tests for the test runner."""

from typing import Any

from agenticassure.results import AgentResult, ToolCall
from agenticassure.runner import Runner
from agenticassure.scenario import Scenario, Suite


class MockAdapter:
    """A simple mock agent adapter for testing."""

    def __init__(self, output: str = "mock response", tool_calls: list | None = None):
        self.output = output
        self.tool_calls = tool_calls or []
        self.call_count = 0

    def run(self, input: str, context: dict[str, Any] | None = None) -> AgentResult:
        self.call_count += 1
        return AgentResult(
            output=self.output,
            tool_calls=[ToolCall(**tc) if isinstance(tc, dict) else tc for tc in self.tool_calls],
            latency_ms=10.0,
        )


class FailingAdapter:
    """Adapter that raises on first N calls then succeeds."""

    def __init__(self, fail_count: int = 1):
        self.fail_count = fail_count
        self.call_count = 0

    def run(self, input: str, context: dict[str, Any] | None = None) -> AgentResult:
        self.call_count += 1
        if self.call_count <= self.fail_count:
            raise RuntimeError("Agent failed")
        return AgentResult(output="recovered", latency_ms=5.0)


class TestRunner:
    def test_run_suite(self):
        adapter = MockAdapter(output="Hello!")
        runner = Runner(adapter=adapter)
        suite = Suite(
            name="test",
            scenarios=[
                Scenario(name="s1", input="hi"),
                Scenario(name="s2", input="hello"),
            ],
        )
        result = runner.run_suite(suite)
        assert len(result.scenario_results) == 2
        assert result.pass_rate == 1.0
        assert adapter.call_count == 2

    def test_run_with_tags(self):
        adapter = MockAdapter(output="ok")
        runner = Runner(adapter=adapter)
        suite = Suite(
            name="test",
            scenarios=[
                Scenario(name="s1", input="hi", tags=["fast"]),
                Scenario(name="s2", input="hello", tags=["slow"]),
            ],
        )
        result = runner.run_suite(suite, tags=["fast"])
        assert len(result.scenario_results) == 1
        assert result.scenario_results[0].scenario.name == "s1"

    def test_retry_on_failure(self):
        adapter = FailingAdapter(fail_count=1)
        runner = Runner(adapter=adapter, retries=2)
        scenario = Scenario(name="s", input="test")
        result = runner.run_scenario(scenario)
        assert result.passed is True
        assert result.retry_count == 1

    def test_all_retries_exhausted(self):
        adapter = FailingAdapter(fail_count=5)
        runner = Runner(adapter=adapter, retries=2)
        scenario = Scenario(name="s", input="test")
        result = runner.run_scenario(scenario)
        assert result.passed is False
        assert result.error is not None

    def test_fail_fast(self):
        adapter = MockAdapter(output="")  # empty output fails passfail
        runner = Runner(adapter=adapter, fail_fast=True)
        suite = Suite(
            name="test",
            scenarios=[
                Scenario(name="s1", input="hi"),
                Scenario(name="s2", input="hello"),
                Scenario(name="s3", input="hey"),
            ],
        )
        result = runner.run_suite(suite)
        # Should stop after first failure
        assert len(result.scenario_results) == 1
