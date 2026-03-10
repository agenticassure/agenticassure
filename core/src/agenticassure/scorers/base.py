from __future__ import annotations

from typing import Protocol, runtime_checkable

from agenticassure.results import AgentResult, ScoreResult
from agenticassure.scenario import Scenario


@runtime_checkable
class Scorer(Protocol):
    """Protocol that all scorers must implement."""

    name: str

    def score(self, scenario: Scenario, result: AgentResult) -> ScoreResult:
        """Evaluate the agent's result against the scenario's expectations."""
        ...


_SCORER_REGISTRY: dict[str, Scorer] = {}


def register_scorer(scorer: Scorer) -> None:
    """Register a scorer instance in the global registry.

    The scorer is stored under its ``name`` attribute. If a scorer with the
    same name already exists it will be silently replaced, allowing users to
    override built-in scorers with custom implementations.
    """
    _SCORER_REGISTRY[scorer.name] = scorer


def get_scorer(name: str) -> Scorer:
    """Look up a registered scorer by name.

    Raises:
        KeyError: If no scorer with the given name has been registered.
    """
    if name not in _SCORER_REGISTRY:
        raise KeyError(f"Unknown scorer '{name}'. Available: {list(_SCORER_REGISTRY.keys())}")
    return _SCORER_REGISTRY[name]


def list_scorers() -> list[str]:
    """Return the names of all currently registered scorers.

    Useful for CLI help text and introspection. The order matches
    registration order (dict insertion order in Python 3.7+).
    """
    return list(_SCORER_REGISTRY.keys())
