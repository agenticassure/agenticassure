from __future__ import annotations

from agenticassure.results import AgentResult, ScoreResult
from agenticassure.scenario import Scenario
from agenticassure.scorers.base import register_scorer


class PassFailScorer:
    """Evaluates whether the agent called the expected tools and produced output."""

    name: str = "passfail"

    def score(self, scenario: Scenario, result: AgentResult) -> ScoreResult:
        checks: list[str] = []
        passed = True

        # Check output is non-empty
        if not result.output.strip():
            passed = False
            checks.append("Agent produced empty output")
        else:
            checks.append("Agent produced output")

        # Check expected tools
        if scenario.expected_tools is not None:
            called_tools = {tc.name for tc in result.tool_calls}
            expected = set(scenario.expected_tools)
            missing = expected - called_tools
            if missing:
                passed = False
                checks.append(f"Missing tool calls: {missing}")
            else:
                checks.append("All expected tools were called")

        # Check expected tool arguments — verifies that each expected tool
        # was called with the correct arguments (key-by-key comparison).
        if scenario.expected_tool_args is not None:
            for tool_name, expected_args in scenario.expected_tool_args.items():
                # Find all calls to this tool; use the first match for comparison
                matching_calls = [tc for tc in result.tool_calls if tc.name == tool_name]
                if not matching_calls:
                    passed = False
                    checks.append(f"Tool '{tool_name}' was not called")
                    continue
                actual_args = matching_calls[0].arguments
                # Compare each expected key-value pair against the actual args
                for key, value in expected_args.items():
                    if key not in actual_args:
                        # Argument was expected but not present at all
                        passed = False
                        checks.append(f"Tool '{tool_name}' missing arg '{key}'")
                    elif actual_args[key] != value:
                        # Argument present but value does not match (exact equality)
                        passed = False
                        checks.append(
                            f"Tool '{tool_name}' arg '{key}': "
                            f"expected '{value}', got '{actual_args[key]}'"
                        )
                    else:
                        checks.append(f"Tool '{tool_name}' arg '{key}' matches")

        # Check expected output
        if scenario.expected_output is not None:
            if scenario.expected_output.lower() in result.output.lower():
                checks.append("Expected output found in response")
            else:
                passed = False
                checks.append("Expected output not found in response")

        return ScoreResult(
            scenario_id=scenario.id,
            scorer_name=self.name,
            score=1.0 if passed else 0.0,
            passed=passed,
            explanation="; ".join(checks),
        )


register_scorer(PassFailScorer())
