# AgenticAssure — Claude Code Context

## Project Overview
AgenticAssure is a Python SDK for testing LLM-powered AI agents before deployment.
- `core/` = open-source (MIT), published to public PyPI as `agenticassure`
- `pro/` = commercial (proprietary), distributed via private PyPI as `agenticassure-pro`
- `pro/` is gitignored — closed-source, developed separately

## Tech Stack
- Python 3.10+, Pydantic v2, Click, Rich, pytest
- Ruff for linting, Black for formatting
- jsonschema for YAML validation
- SQLite for Pro run history (planned)

## Development Rules
- All public functions/classes must have docstrings
- Type hints on every function signature
- Tests required for every new module (pytest)
- Run `ruff check .` and `black --check .` before every commit
- Keep Core and Pro cleanly separated — Pro imports Core, never the reverse

## Architecture
- Core defines protocols (AgentAdapter, Scorer); implementations are pluggable
- YAML is the primary scenario definition format
- Runner is synchronous; async support planned for v2
- Scorers are registered in a global registry (`scorers/base.py`)
- Pro extends Core's CLI via Click command groups

## Key Paths
- Core source: `core/src/agenticassure/`
- Tests: `core/tests/`
- Examples: `examples/`
- CI: `.github/workflows/ci.yml`

## Current State (v0.3.0)
- Sprint 1 complete: data models, loader, runner, CLI, 4 scorers, 3 report formats
- 48 tests passing, CI green
- Pro scaffold exists (all stubs, implementation in Sprint 2)
