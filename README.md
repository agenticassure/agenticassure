# AgenticAssure

**Test and benchmark your AI agents before they go live.**

[![PyPI version](https://img.shields.io/pypi/v/agenticassure)](https://pypi.org/project/agenticassure/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/agenticassure/agenticassure/actions/workflows/ci.yml/badge.svg)](https://github.com/agenticassure/agenticassure/actions/workflows/ci.yml)

AgenticAssure is an open-source SDK for testing, benchmarking, and validating
LLM-powered AI agents. Define test scenarios in YAML, run them with Python,
and get structured reports on agent quality, safety, and performance.

---

## Quick Install

```bash
pip install agenticassure
```

For optional extras:

```bash
pip install agenticassure[similarity]   # semantic similarity assertions
pip install agenticassure[openai]       # OpenAI integration
pip install agenticassure[all]          # everything
```

## Usage

### 1. Define a scenario in YAML

```yaml
# scenarios/greeting.yaml
name: greeting-test
description: Verify the agent responds with a polite greeting

steps:
  - input: "Hello, who are you?"
    assertions:
      - type: contains
        value: "hello"
      - type: tone
        value: polite
```

### 2. Run with Python

```python
from agenticassure import ScenarioRunner

runner = ScenarioRunner.from_yaml("scenarios/greeting.yaml")
result = runner.run(agent=my_agent)

print(result.passed)   # True / False
print(result.summary)  # Structured report
```

### 3. Or use the CLI

```bash
agenticassure run scenarios/greeting.yaml --agent my_agent
```

## Features

### Core (open-source)

- YAML-based scenario definitions
- Built-in assertion library (contains, regex, JSON schema, tone)
- Semantic similarity assertions (optional)
- CLI and Python API
- Structured test reports with Rich output
- OpenAI and LangChain agent adapters
- Extensible plugin system

### Pro (commercial)

- Advanced HTML and PDF report generation
- Multi-agent orchestration testing
- Regression tracking and historical benchmarks
- Slack and email notifications
- Priority support and SLA

## Project Structure

```
agenticassure/
  core/       # Open-source agenticassure package (MIT)
  pro/        # Commercial agenticassure-pro package
```

## Development

```bash
# Clone the repo
git clone https://github.com/agenticassure/agenticassure.git
cd agenticassure

# Install core in dev mode
pip install -e "core[dev]"

# Run tests
pytest core/tests

# Lint and format
ruff check core/src
black --check core/src
```

## Documentation

Full documentation is available at [docs.agenticassure.com](https://docs.agenticassure.com).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on
[GitHub](https://github.com/agenticassure/agenticassure).

## License

The core package is released under the [MIT License](LICENSE).
The pro package is available under a commercial license -- see `pro/` for details.
