"""Tests for YAML scenario loader."""

import pytest
from pathlib import Path

from agenticassure.loader import (
    SUITE_SCHEMA,
    load_scenarios,
    validate_scenario_file,
    validate_with_schema,
)


@pytest.fixture
def sample_yaml(tmp_path):
    content = '''suite:
  name: test-suite
  description: Test suite
  config:
    default_timeout: 15
    retries: 1

scenarios:
  - name: basic_test
    input: "Hello world"
    expected_output: "hello"
    scorers:
      - passfail
    tags:
      - basic

  - name: tool_test
    input: "Search for flights"
    expected_tools:
      - search_flights
    scorers:
      - passfail
    tags:
      - tools
'''
    file = tmp_path / "test_scenarios.yaml"
    file.write_text(content, encoding="utf-8")
    return file


@pytest.fixture
def invalid_yaml(tmp_path):
    content = '''scenarios:
  - name: missing_input
    tags: not-a-list
'''
    file = tmp_path / "invalid.yaml"
    file.write_text(content, encoding="utf-8")
    return file


class TestLoadScenarios:
    def test_load_valid(self, sample_yaml):
        suite = load_scenarios(sample_yaml)
        assert suite.name == "test-suite"
        assert len(suite.scenarios) == 2
        assert suite.scenarios[0].name == "basic_test"
        assert suite.config.retries == 1

    def test_load_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            load_scenarios("nonexistent.yaml")

    def test_load_wrong_extension(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        with pytest.raises(ValueError):
            load_scenarios(f)


class TestValidation:
    def test_valid_file(self, sample_yaml):
        issues = validate_scenario_file(sample_yaml)
        assert issues == []

    def test_invalid_file(self, invalid_yaml):
        issues = validate_scenario_file(invalid_yaml)
        assert len(issues) > 0

    def test_nonexistent_file(self):
        issues = validate_scenario_file("nope.yaml")
        assert any("not found" in i.lower() for i in issues)

    def test_schema_errors_in_validate_file(self, tmp_path):
        """validate_scenario_file should include schema errors for wrong types."""
        content = '''scenarios:
  - name: bad_scenario
    input: "hello"
    tags: "not-a-list"
'''
        f = tmp_path / "bad_tags.yaml"
        f.write_text(content, encoding="utf-8")
        issues = validate_scenario_file(f)
        assert any("Schema" in i for i in issues)


class TestSchemaValidation:
    """Tests for validate_with_schema and SUITE_SCHEMA."""

    def test_valid_minimal(self):
        data = {"scenarios": [{"name": "t", "input": "hi"}]}
        assert validate_with_schema(data) == []

    def test_valid_full(self):
        data = {
            "suite": {
                "name": "my-suite",
                "description": "A test suite",
                "config": {
                    "default_timeout": 10,
                    "retries": 2,
                    "default_scorers": ["passfail"],
                    "fail_fast": True,
                },
            },
            "scenarios": [
                {
                    "name": "s1",
                    "input": "hello",
                    "description": "desc",
                    "expected_output": "world",
                    "expected_tools": ["tool_a"],
                    "expected_tool_args": {"key": "val"},
                    "tags": ["tag1"],
                    "metadata": {"k": "v"},
                    "scorers": ["passfail"],
                    "timeout_seconds": 5,
                }
            ],
        }
        assert validate_with_schema(data) == []

    def test_missing_scenarios(self):
        errors = validate_with_schema({"suite": {"name": "x"}})
        assert any("scenarios" in e and "required" in e for e in errors)

    def test_scenario_missing_name(self):
        data = {"scenarios": [{"input": "hi"}]}
        errors = validate_with_schema(data)
        assert any("name" in e and "required" in e for e in errors)

    def test_scenario_missing_input(self):
        data = {"scenarios": [{"name": "t"}]}
        errors = validate_with_schema(data)
        assert any("input" in e and "required" in e for e in errors)

    def test_wrong_type_tags(self):
        data = {"scenarios": [{"name": "t", "input": "hi", "tags": "oops"}]}
        errors = validate_with_schema(data)
        assert any("tags" in e for e in errors)

    def test_wrong_type_scorers(self):
        data = {"scenarios": [{"name": "t", "input": "hi", "scorers": "bad"}]}
        errors = validate_with_schema(data)
        assert any("scorers" in e for e in errors)

    def test_wrong_type_timeout(self):
        data = {"scenarios": [{"name": "t", "input": "hi", "timeout_seconds": "slow"}]}
        errors = validate_with_schema(data)
        assert any("timeout_seconds" in e for e in errors)

    def test_timeout_must_be_positive(self):
        data = {"scenarios": [{"name": "t", "input": "hi", "timeout_seconds": 0}]}
        errors = validate_with_schema(data)
        assert any("timeout_seconds" in e for e in errors)

    def test_suite_missing_name(self):
        data = {"suite": {"description": "no name"}, "scenarios": [{"name": "t", "input": "hi"}]}
        errors = validate_with_schema(data)
        assert any("name" in e and "required" in e for e in errors)

    def test_suite_name_wrong_type(self):
        data = {"suite": {"name": 123}, "scenarios": [{"name": "t", "input": "hi"}]}
        errors = validate_with_schema(data)
        assert any("name" in e for e in errors)

    def test_load_rejects_schema_invalid_file(self, tmp_path):
        """load_scenarios raises ValueError for schema-invalid YAML."""
        content = '''scenarios:
  - name: bad
    input: "hi"
    timeout_seconds: -1
'''
        f = tmp_path / "bad.yaml"
        f.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError, match="Schema validation failed"):
            load_scenarios(f)

    def test_schema_constant_exists(self):
        assert isinstance(SUITE_SCHEMA, dict)
        assert "properties" in SUITE_SCHEMA
        assert "scenarios" in SUITE_SCHEMA["properties"]
