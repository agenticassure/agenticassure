"""Tests for built-in scorers."""

from agenticassure.results import AgentResult, ToolCall
from agenticassure.scenario import Scenario
from agenticassure.scorers.passfail import PassFailScorer
from agenticassure.scorers.regex import RegexScorer
from agenticassure.scorers.exact import ExactMatchScorer


class TestPassFailScorer:
    def setup_method(self):
        self.scorer = PassFailScorer()

    def test_pass_with_output(self):
        scenario = Scenario(name="t", input="hi")
        result = AgentResult(output="Hello there!")
        score = self.scorer.score(scenario, result)
        assert score.passed is True
        assert score.score == 1.0

    def test_fail_empty_output(self):
        scenario = Scenario(name="t", input="hi")
        result = AgentResult(output="")
        score = self.scorer.score(scenario, result)
        assert score.passed is False

    def test_pass_expected_tools(self):
        scenario = Scenario(name="t", input="hi", expected_tools=["search"])
        result = AgentResult(
            output="found it",
            tool_calls=[ToolCall(name="search", arguments={"q": "test"})],
        )
        score = self.scorer.score(scenario, result)
        assert score.passed is True

    def test_fail_missing_tools(self):
        scenario = Scenario(name="t", input="hi", expected_tools=["search"])
        result = AgentResult(output="no tools")
        score = self.scorer.score(scenario, result)
        assert score.passed is False

    def test_expected_tool_args(self):
        scenario = Scenario(
            name="t",
            input="hi",
            expected_tools=["search"],
            expected_tool_args={"search": {"q": "test"}},
        )
        result = AgentResult(
            output="ok",
            tool_calls=[ToolCall(name="search", arguments={"q": "test"})],
        )
        score = self.scorer.score(scenario, result)
        assert score.passed is True


class TestRegexScorer:
    def setup_method(self):
        self.scorer = RegexScorer()

    def test_match(self):
        scenario = Scenario(name="t", input="hi", metadata={"regex_pattern": r"\d+"})
        result = AgentResult(output="Found 42 results")
        score = self.scorer.score(scenario, result)
        assert score.passed is True

    def test_no_match(self):
        scenario = Scenario(name="t", input="hi", metadata={"regex_pattern": r"\d+"})
        result = AgentResult(output="No numbers here")
        score = self.scorer.score(scenario, result)
        assert score.passed is False

    def test_no_pattern(self):
        scenario = Scenario(name="t", input="hi")
        result = AgentResult(output="test")
        score = self.scorer.score(scenario, result)
        assert score.passed is False


class TestExactMatchScorer:
    def setup_method(self):
        self.scorer = ExactMatchScorer()

    def test_exact_match(self):
        scenario = Scenario(name="t", input="hi", expected_output="Hello World")
        result = AgentResult(output="hello world")
        score = self.scorer.score(scenario, result)
        assert score.passed is True  # normalized

    def test_no_match(self):
        scenario = Scenario(name="t", input="hi", expected_output="foo")
        result = AgentResult(output="bar")
        score = self.scorer.score(scenario, result)
        assert score.passed is False

    def test_no_expected(self):
        scenario = Scenario(name="t", input="hi")
        result = AgentResult(output="test")
        score = self.scorer.score(scenario, result)
        assert score.passed is False
