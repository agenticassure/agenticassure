from __future__ import annotations

import time
from typing import Any

from agenticassure.adapters.base import AgentAdapter
from agenticassure.results import AgentResult, RunResult, ScenarioRunResult
from agenticassure.scenario import Scenario, Suite
from agenticassure.scorers.base import get_scorer


class Runner:
    """Sequential test runner that executes scenarios against an agent adapter."""

    def __init__(
        self,
        adapter: AgentAdapter,
        default_timeout: float = 30.0,
        retries: int = 0,
        fail_fast: bool = False,
    ) -> None:
        self.adapter = adapter
        self.default_timeout = default_timeout
        self.retries = retries
        self.fail_fast = fail_fast

    def run_suite(
        self,
        suite: Suite,
        tags: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> RunResult:
        """Run all scenarios in a suite and return aggregated results."""
        scenarios = suite.scenarios
        # Filter scenarios down to only those matching the requested tags
        if tags:
            tag_set = set(tags)
            scenarios = [s for s in scenarios if tag_set.intersection(s.tags)]

        # Suite-level config overrides runner defaults when present
        retries = suite.config.retries if suite.config.retries else self.retries
        fail_fast = suite.config.fail_fast if suite.config.fail_fast else self.fail_fast

        run_result = RunResult(suite_name=suite.name)
        total_start = time.perf_counter()

        for scenario in scenarios:
            scenario_result = self._run_scenario(scenario, context=context, retries=retries)
            run_result.scenario_results.append(scenario_result)

            # Stop early on first failure when fail_fast is enabled
            if fail_fast and not scenario_result.passed:
                break

        # Record wall-clock time and compute aggregate pass rate / scores
        run_result.total_duration_ms = (time.perf_counter() - total_start) * 1000
        run_result.compute_aggregates()
        return run_result

    def run_scenario(
        self,
        scenario: Scenario,
        context: dict[str, Any] | None = None,
    ) -> ScenarioRunResult:
        """Run a single scenario."""
        return self._run_scenario(scenario, context=context, retries=self.retries)

    def _run_scenario(
        self,
        scenario: Scenario,
        context: dict[str, Any] | None = None,
        retries: int = 0,
    ) -> ScenarioRunResult:
        """Internal: run a scenario with retry logic."""
        last_error: str | None = None
        retry_count = 0

        # Attempt up to (retries + 1) times; return on first success
        for attempt in range(retries + 1):
            start = time.perf_counter()
            try:
                # Execute the agent adapter with the scenario input
                agent_result = self.adapter.run(scenario.input, context=context)
                duration_ms = (time.perf_counter() - start) * 1000

                # Run each configured scorer against the agent's output
                scores = []
                for scorer_name in scenario.scorers:
                    scorer = get_scorer(scorer_name)
                    score_result = scorer.score(scenario, agent_result)
                    scores.append(score_result)

                # A scenario passes only if every scorer passes
                all_passed = all(s.passed for s in scores) if scores else False

                return ScenarioRunResult(
                    scenario=scenario,
                    agent_result=agent_result,
                    scores=scores,
                    passed=all_passed,
                    duration_ms=duration_ms,
                    retry_count=attempt,
                )
            except Exception as e:
                # Record the error and continue to the next retry attempt
                duration_ms = (time.perf_counter() - start) * 1000
                last_error = f"{type(e).__name__}: {e}"
                retry_count = attempt

        # All retries exhausted — return a failing result with the last error
        return ScenarioRunResult(
            scenario=scenario,
            agent_result=AgentResult(output=""),
            passed=False,
            duration_ms=duration_ms,
            error=last_error,
            retry_count=retry_count,
        )
