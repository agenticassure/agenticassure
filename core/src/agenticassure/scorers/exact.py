from __future__ import annotations

from agenticassure.results import AgentResult, ScoreResult
from agenticassure.scenario import Scenario
from agenticassure.scorers.base import register_scorer


class ExactMatchScorer:
    """Evaluates whether the agent output exactly matches the expected output."""

    name: str = "exact"

    def score(self, scenario: Scenario, result: AgentResult) -> ScoreResult:
        if scenario.expected_output is None:
            return ScoreResult(
                scenario_id=scenario.id,
                scorer_name=self.name,
                score=0.0,
                passed=False,
                explanation="No expected_output defined for this scenario",
            )

        normalize = scenario.metadata.get("exact_normalize", True)
        expected = scenario.expected_output
        actual = result.output

        if normalize:
            expected = expected.strip().lower()
            actual = actual.strip().lower()

        passed = actual == expected
        return ScoreResult(
            scenario_id=scenario.id,
            scorer_name=self.name,
            score=1.0 if passed else 0.0,
            passed=passed,
            explanation=f"Output {'matches' if passed else 'does not match'} expected output"
            + (f" (normalized={normalize})" if normalize else ""),
        )


register_scorer(ExactMatchScorer())
