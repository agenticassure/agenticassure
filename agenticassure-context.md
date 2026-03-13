# AgenticAssure — Project Context

## What Is It?

AgenticAssure is an open-source Python SDK for **testing, benchmarking, and validating LLM-powered AI agents** before deployment. You define test scenarios in YAML, point them at your agent via an adapter, and get structured pass/fail reports with scoring.

**PyPI**: `pip install agenticassure` (v0.3.0)
**GitHub**: github.com/agenticassure/agenticassure
**License**: MIT (core), commercial (pro)
**Python**: 3.10+

---

## How It Works

1. **Define scenarios** in YAML — each scenario has an input prompt, optional expected output, expected tool calls, and a list of scorers
2. **Write an adapter** — a simple class with a `run(input, context) -> AgentResult` method that wraps your agent
3. **Run via CLI or Python** — AgenticAssure executes each scenario against your agent, scores the results, and generates reports

### Core Flow
```
YAML Scenarios → Loader (with JSON Schema validation) → Runner → Adapter.run() → Scorers → Reports
```

---

## File Structure

```
agenticassure/
├── core/                          # Open-source package (published to PyPI)
│   ├── pyproject.toml             # Hatchling build config, dependencies, extras
│   ├── src/agenticassure/
│   │   ├── __init__.py            # Public API, __version__
│   │   ├── __main__.py            # python -m agenticassure
│   │   ├── scenario.py            # Pydantic models: Scenario, Suite, SuiteConfig
│   │   ├── results.py             # Pydantic models: AgentResult, ScoreResult, RunResult, ToolCall, TokenUsage
│   │   ├── loader.py              # YAML loading + JSON Schema validation
│   │   ├── runner.py              # Runner class — executes scenarios with retry logic
│   │   ├── cli.py                 # Click CLI — run, init, validate, list commands
│   │   ├── adapters/
│   │   │   ├── base.py            # AgentAdapter protocol
│   │   │   ├── openai.py          # OpenAI adapter (optional)
│   │   │   └── langchain.py       # LangChain adapter (optional)
│   │   ├── scorers/
│   │   │   ├── base.py            # Scorer protocol + global registry
│   │   │   ├── passfail.py        # Default scorer — checks output exists, expected tools called, expected output found
│   │   │   ├── exact.py           # Exact string match
│   │   │   ├── regex.py           # Regex pattern match (via metadata.regex_pattern)
│   │   │   └── similarity.py      # Cosine similarity via sentence-transformers (optional dep)
│   │   └── reports/
│   │       ├── cli_report.py      # Rich terminal table output
│   │       ├── html_report.py     # Standalone HTML report
│   │       └── json_report.py     # JSON file output
│   └── tests/
│       ├── test_loader.py
│       ├── test_results.py
│       ├── test_runner.py
│       ├── test_scenario.py
│       └── test_scorers.py
├── pro/                           # Commercial package (gitignored, closed-source)
├── examples/
│   ├── scenarios/
│   │   └── booking_agent.yaml
│   └── simple_agent/
│       └── example.py
├── docs/                          # Documentation (placeholder)
├── .github/workflows/ci.yml      # CI: ruff, black, pytest on Python 3.10-3.12
├── .env.example                   # HF_TOKEN for similarity scorer
├── README.md
└── LICENSE                        # MIT
```

---

## Key Data Models (Pydantic v2)

### Scenario (scenario.py)
```python
class Scenario:
    id: str                          # Auto-generated UUID
    name: str                        # Required
    input: str                       # Required — the prompt sent to the agent
    description: str | None
    expected_output: str | None      # For passfail/exact/similarity comparison
    expected_tools: list[str] | None # Tool names the agent should call
    expected_tool_args: dict | None  # Expected arguments for those tools
    tags: list[str]                  # For filtering
    metadata: dict[str, Any]         # Scorer-specific config (regex_pattern, similarity_threshold, etc.)
    scorers: list[str]               # Default: ["passfail"]
    timeout_seconds: float           # Default: 30.0
```

### AgentResult (results.py)
```python
class AgentResult:
    output: str                      # The agent's text response
    tool_calls: list[ToolCall]       # Tools the agent called (name, arguments, result)
    reasoning_trace: list[str] | None
    latency_ms: float
    token_usage: TokenUsage | None
    raw_response: Any | None
```

### AgentAdapter Protocol (adapters/base.py)
```python
class AgentAdapter(Protocol):
    def run(self, input: str, context: dict[str, Any] | None = None) -> AgentResult: ...
```

---

## Scorers

Scorers are registered in a global registry. Each has a `score(scenario, agent_result) -> ScoreResult` method.

| Scorer | Key | What It Does |
|---|---|---|
| **PassFail** | `passfail` | Default. Checks: output exists, expected tools called, tool args match, expected_output substring found |
| **Exact Match** | `exact` | Exact string comparison against expected_output |
| **Regex** | `regex` | Matches `metadata.regex_pattern` against output |
| **Similarity** | `similarity` | Cosine similarity via sentence-transformers (requires `pip install agenticassure[similarity]`). Threshold configurable via `metadata.similarity_threshold` (default 0.7) |

A scenario can use multiple scorers — it passes only if **all** scorers pass.

---

## CLI Commands

```bash
agenticassure run <path> --adapter mymodule.MyAgent   # Run scenarios
agenticassure run <path> --dry-run                     # Validate without executing
agenticassure run <path> -o html                       # HTML report output
agenticassure run <path> -o json                       # JSON report output
agenticassure validate <path>                          # Schema validation only
agenticassure list <path>                              # List scenarios
agenticassure init [directory]                         # Scaffold a new project
```

---

## YAML Scenario Format

```yaml
suite:
  name: my-test-suite
  description: Tests for my customer support agent
  config:
    default_timeout: 30
    retries: 1
    default_scorers: ["passfail"]
    fail_fast: false

scenarios:
  - name: Basic greeting
    input: "Hello, who are you?"
    expected_output: "hello"
    scorers:
      - passfail
    tags:
      - basic

  - name: Tool usage check
    input: "Look up order ORD-001"
    expected_tools:
      - get_order
    expected_tool_args:
      get_order:
        order_id: "ORD-001"
    scorers:
      - passfail

  - name: Regex pattern check
    input: "What is your email?"
    scorers:
      - regex
    metadata:
      regex_pattern: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"

  - name: Semantic similarity check
    input: "What is your return policy?"
    expected_output: "We offer a 30-day return policy for all items."
    scorers:
      - similarity
    metadata:
      similarity_threshold: 0.8
```

---

## Dependencies

**Core**: pydantic, pyyaml, click, rich, jsonschema
**Optional**: sentence-transformers (similarity), openai, langchain

---

## Current State (v0.3.0)

- 48+ tests passing, CI green (ruff + black + pytest)
- 4 scorers: passfail, exact, regex, similarity
- 3 report formats: CLI (Rich), HTML, JSON
- Adapter protocol for plugging in any agent
- Suite-level config (timeout, retries, fail_fast, default_scorers)
- Tag-based scenario filtering
- Auto-discovery of adapter via agenticassure.yaml config file
