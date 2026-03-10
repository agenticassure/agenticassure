from __future__ import annotations

from pathlib import Path

import jsonschema
import yaml

from agenticassure.scenario import Scenario, Suite, SuiteConfig

# -------------------------------------------------------------------
# JSON Schema for the scenario YAML format
# -------------------------------------------------------------------
SUITE_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["scenarios"],
    "additionalProperties": False,
    "properties": {
        "suite": {
            "type": "object",
            "required": ["name"],
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "config": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "default_timeout": {"type": "number"},
                        "retries": {"type": "integer"},
                        "default_scorers": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "fail_fast": {"type": "boolean"},
                    },
                },
            },
        },
        "scenarios": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["name", "input"],
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "input": {"type": "string"},
                    "description": {"type": "string"},
                    "expected_output": {"type": "string"},
                    "expected_tools": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "expected_tool_args": {"type": "object"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "metadata": {"type": "object"},
                    "scorers": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "timeout_seconds": {
                        "type": "number",
                        "exclusiveMinimum": 0,
                    },
                },
            },
        },
    },
}


def validate_with_schema(data: dict) -> list[str]:
    """Validate parsed YAML data against ``SUITE_SCHEMA``.

    Returns a list of human-readable error messages (empty if valid).
    """
    validator = jsonschema.Draft202012Validator(SUITE_SCHEMA)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"Schema: {path}: {error.message}")
    return errors


def load_scenarios(path: str | Path) -> Suite:
    """Load a test suite from a YAML file.

    Supports both single-suite files and files with just a scenarios list.
    """
    path = Path(path)

    # Guard: file must exist and have a YAML extension
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")
    if path.suffix not in (".yml", ".yaml"):
        raise ValueError(f"Expected YAML file, got: {path.suffix}")

    # Parse the raw YAML into a Python dict
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Reject empty files early before schema validation
    if data is None:
        raise ValueError(f"Empty YAML file: {path}")

    # Validate structure against the JSON Schema; collect all errors at once
    schema_errors = validate_with_schema(data)
    if schema_errors:
        raise ValueError(f"Schema validation failed for {path}:\n" + "\n".join(schema_errors))

    # Convert the validated dict into typed domain objects
    return _parse_suite_data(data, source_path=path)


def load_scenarios_from_dir(directory: str | Path) -> list[Suite]:
    """Load all YAML scenario files from a directory."""
    directory = Path(directory)
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    suites = []
    for path in sorted(directory.glob("**/*.y*ml")):
        if path.suffix in (".yml", ".yaml"):
            try:
                suites.append(load_scenarios(path))
            except Exception as e:
                raise ValueError(f"Error loading {path}: {e}") from e
    return suites


def validate_scenario_file(path: str | Path) -> list[str]:
    """Validate a YAML scenario file and return a list of issues (empty = valid)."""
    issues: list[str] = []
    path = Path(path)

    if not path.exists():
        return [f"File not found: {path}"]
    if path.suffix not in (".yml", ".yaml"):
        return [f"Not a YAML file: {path}"]

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    if data is None:
        return ["Empty YAML file"]

    if not isinstance(data, dict):
        return ["Root element must be a mapping"]

    # First pass: run JSON Schema validation for structural correctness
    issues.extend(validate_with_schema(data))

    # Second pass: semantic checks that the schema cannot express
    if "suite" in data:
        suite_data = data["suite"]
        if not isinstance(suite_data, dict):
            issues.append("'suite' must be a mapping")
        elif "name" not in suite_data:
            issues.append("Suite missing required field 'name'")

    # Validate each scenario entry for required fields and correct types
    scenarios_data = data.get("scenarios", [])
    if not scenarios_data:
        issues.append("No scenarios defined")
    elif not isinstance(scenarios_data, list):
        issues.append("'scenarios' must be a list")
    else:
        for i, s in enumerate(scenarios_data):
            prefix = f"Scenario [{i}]"
            if not isinstance(s, dict):
                issues.append(f"{prefix}: must be a mapping")
                continue
            if "name" not in s:
                issues.append(f"{prefix}: missing required field 'name'")
            if "input" not in s:
                issues.append(f"{prefix}: missing required field 'input'")
            if "scorers" in s and not isinstance(s["scorers"], list):
                issues.append(f"{prefix}: 'scorers' must be a list")
            if "tags" in s and not isinstance(s["tags"], list):
                issues.append(f"{prefix}: 'tags' must be a list")
            if "timeout_seconds" in s:
                try:
                    float(s["timeout_seconds"])
                except (TypeError, ValueError):
                    issues.append(f"{prefix}: 'timeout_seconds' must be a number")

    return issues


def _parse_suite_data(data: dict, source_path: Path | None = None) -> Suite:
    """Parse raw YAML data into a Suite."""
    suite_info = data.get("suite", {})
    if not isinstance(suite_info, dict):
        suite_info = {}

    config_data = suite_info.get("config", {})
    config = SuiteConfig(**config_data) if config_data else SuiteConfig()

    scenarios_data = data.get("scenarios", [])
    scenarios: list[Scenario] = []
    for s_data in scenarios_data:
        scenarios.append(Scenario(**s_data))

    suite_name = suite_info.get("name", source_path.stem if source_path else "unnamed")

    return Suite(
        name=suite_name,
        description=suite_info.get("description"),
        scenarios=scenarios,
        tags=suite_info.get("tags", []),
        config=config,
    )
