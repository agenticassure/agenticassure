from __future__ import annotations

import re

from agenticassure.results import AgentResult, ScoreResult
from agenticassure.scenario import Scenario
from agenticassure.scorers.base import register_scorer


class RegexScorer:
    """Evaluates agent output against a regex pattern from scenario metadata."""

    name: str = "regex"

    def score(self, scenario: Scenario, result: AgentResult) -> ScoreResult:
        pattern = scenario.metadata.get("regex_pattern")
        if pattern is None:
            return ScoreResult(
                scenario_id=scenario.id,
                scorer_name=self.name,
                score=0.0,
                passed=False,
                explanation="No 'regex_pattern' found in scenario metadata",
            )

        try:
            match = re.search(pattern, result.output)
        except re.error as e:
            return ScoreResult(
                scenario_id=scenario.id,
                scorer_name=self.name,
                score=0.0,
                passed=False,
                explanation=f"Invalid regex pattern: {e}",
            )

        passed = match is not None
        return ScoreResult(
            scenario_id=scenario.id,
            scorer_name=self.name,
            score=1.0 if passed else 0.0,
            passed=passed,
            explanation=f"Pattern '{pattern}' {'matched' if passed else 'did not match'} in output",
            details={"pattern": pattern, "match": match.group(0) if match else None},
        )


register_scorer(RegexScorer())
