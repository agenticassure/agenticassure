"""Tests for scenario and suite data models."""

from agenticassure.scenario import Scenario, Suite, SuiteConfig


class TestScenario:
    def test_minimal_scenario(self):
        s = Scenario(name="test", input="hello")
        assert s.name == "test"
        assert s.input == "hello"
        assert s.id  # auto-generated
        assert s.scorers == ["passfail"]
        assert s.timeout_seconds == 30.0
        assert s.tags == []
        assert s.metadata == {}

    def test_full_scenario(self):
        s = Scenario(
            name="full",
            input="test input",
            description="A test",
            expected_output="expected",
            expected_tools=["tool1", "tool2"],
            expected_tool_args={"tool1": {"arg": "val"}},
            tags=["tag1"],
            metadata={"key": "value"},
            scorers=["passfail", "regex"],
            timeout_seconds=60.0,
        )
        assert s.expected_tools == ["tool1", "tool2"]
        assert s.expected_tool_args == {"tool1": {"arg": "val"}}
        assert s.tags == ["tag1"]
        assert s.scorers == ["passfail", "regex"]

    def test_scenario_auto_id(self):
        s1 = Scenario(name="a", input="x")
        s2 = Scenario(name="b", input="y")
        assert s1.id != s2.id


class TestSuiteConfig:
    def test_defaults(self):
        config = SuiteConfig()
        assert config.default_timeout == 30.0
        assert config.retries == 0
        assert config.default_scorers == ["passfail"]
        assert config.fail_fast is False


class TestSuite:
    def test_empty_suite(self):
        suite = Suite(name="test-suite")
        assert suite.name == "test-suite"
        assert suite.scenarios == []
        assert isinstance(suite.config, SuiteConfig)

    def test_suite_with_scenarios(self):
        scenarios = [
            Scenario(name="s1", input="i1"),
            Scenario(name="s2", input="i2"),
        ]
        suite = Suite(name="suite", scenarios=scenarios, tags=["integration"])
        assert len(suite.scenarios) == 2
        assert suite.tags == ["integration"]
