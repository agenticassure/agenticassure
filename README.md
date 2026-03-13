# AgenticAssure

**Test and benchmark your AI agents before they go live.**

[![PyPI version](https://img.shields.io/pypi/v/agenticassure)](https://pypi.org/project/agenticassure/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/agenticassure/agenticassure/actions/workflows/ci.yml/badge.svg)](https://github.com/agenticassure/agenticassure/actions/workflows/ci.yml)

AgenticAssure is an open-source SDK for testing, benchmarking, and validating
LLM-powered AI agents. Define test scenarios in YAML, run them against your
agent via a simple adapter, and get structured reports on quality and performance.

---

## Quick Install

```bash
pip install agenticassure
```

For optional extras:

```bash
pip install agenticassure[similarity]   # cosine similarity scorer
pip install agenticassure[openai]       # OpenAI adapter
pip install agenticassure[langchain]    # LangChain adapter
pip install agenticassure[all]          # everything
```

## Usage

### 1. Define scenarios in YAML

```yaml
# scenarios/support_agent.yaml
suite:
  name: support-agent-tests
  description: Validate our customer support agent
  config:
    default_timeout: 30
    retries: 1

scenarios:
  - name: greeting
    input: "Hello, who are you?"
    expected_output: "hello"
    scorers:
      - passfail

  - name: order_lookup
    input: "Look up order ORD-123"
    expected_tools:
      - get_order
    expected_tool_args:
      get_order:
        order_id: "ORD-123"
    scorers:
      - passfail

  - name: email_in_response
    input: "What is your contact email?"
    scorers:
      - regex
    metadata:
      regex_pattern: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
```

### 2. Write an adapter for your agent

```python
from agenticassure import AgentResult

class MyAgent:
    """Wrap your agent so AgenticAssure can call it."""

    def run(self, input: str, context=None) -> AgentResult:
        response = your_agent.invoke(input)  # call your agent here
        return AgentResult(
            output=response.text,
            tool_calls=[],
            latency_ms=response.latency,
        )
```

### 3. Run with Python

```python
from agenticassure.loader import load_scenarios
from agenticassure.runner import Runner
from agenticassure.reports.cli_report import CLIReporter

suite = load_scenarios("scenarios/support_agent.yaml")
runner = Runner(adapter=MyAgent())
result = runner.run_suite(suite)

CLIReporter().report(result)

print(f"Pass rate: {result.pass_rate:.0%}")
print(f"Aggregate score: {result.aggregate_score:.2f}")
```

### 4. Or use the CLI

```bash
# Run scenarios with a custom adapter
agenticassure run scenarios/ --adapter mymodule.MyAgent

# Dry-run (validate without executing)
agenticassure run scenarios/ --dry-run

# Output as HTML or JSON
agenticassure run scenarios/ --adapter mymodule.MyAgent -o html
agenticassure run scenarios/ --adapter mymodule.MyAgent -o json

# Validate YAML without running
agenticassure validate scenarios/

# List all scenarios
agenticassure list scenarios/
```

## Scorers

Scenarios can use one or more scorers. A scenario passes only if **all** scorers pass.

| Scorer | Key | What It Checks |
|---|---|---|
| **Pass/Fail** | `passfail` | Output exists, expected tools called, tool args match, expected output found |
| **Exact Match** | `exact` | Exact string match against `expected_output` |
| **Regex** | `regex` | Pattern from `metadata.regex_pattern` matches output |
| **Similarity** | `similarity` | Cosine similarity via sentence-transformers (requires `[similarity]` extra) |

## Features

### Core (open-source)

- YAML-based scenario definitions with JSON Schema validation
- Pluggable scorer system (passfail, exact, regex, similarity)
- Sequential test runner with retry logic and fail-fast support
- Tag-based scenario filtering
- Suite-level configuration (timeout, retries, default scorers)
- CLI and Python API
- Three report formats: Rich terminal, HTML, JSON
- OpenAI and LangChain agent adapters
- Extensible adapter and scorer protocols

### Pro (commercial)

- LLM-as-judge scorer for nuanced evaluation
- Multi-model comparison engine
- Regression tracking and historical benchmarks
- PDF reports and trend visualizations
- Slack and email notifications
- CI/CD integration (GitHub Actions, GitLab CI)

## Project Structure

```
agenticassure/
  core/       # Open-source agenticassure package (MIT)
  pro/        # Commercial agenticassure-pro package
  examples/   # Example scenarios and adapters
```

## Development

```bash
# Clone the repo
git clone https://github.com/agenticassure/agenticassure.git
cd agenticassure

# Install core in dev mode
pip install -e "core[dev]"

# Run tests
pytest core/tests/

# Lint and format
ruff check .
black --check .
```

## Documentation

Full documentation is available at [docs.agenticassure.com](https://docs.agenticassure.com).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on
[GitHub](https://github.com/agenticassure/agenticassure).

## License

The core package is released under the [MIT License](LICENSE).
The pro package is available under a commercial license -- see `pro/` for details.
