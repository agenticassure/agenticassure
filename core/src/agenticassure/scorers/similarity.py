from __future__ import annotations

import contextlib

from agenticassure.results import AgentResult, ScoreResult
from agenticassure.scenario import Scenario
from agenticassure.scorers.base import register_scorer


class SimilarityScorer:
    """Evaluate semantic similarity between agent output and expected output.

    Uses sentence-transformers for embedding-based comparison.
    """

    name: str = "similarity"

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", threshold: float = 0.7) -> None:
        self.model_name = model_name
        self.threshold = threshold
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is required for SimilarityScorer. "
                    "Install it with: pip install agenticassure[similarity]"
                ) from e
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def score(self, scenario: Scenario, result: AgentResult) -> ScoreResult:
        if scenario.expected_output is None:
            return ScoreResult(
                scenario_id=scenario.id,
                scorer_name=self.name,
                score=0.0,
                passed=False,
                explanation="No expected_output defined for this scenario",
            )

        import numpy as np

        model = self._get_model()
        threshold = scenario.metadata.get("similarity_threshold", self.threshold)

        embeddings = model.encode([scenario.expected_output, result.output])
        cosine_sim = float(
            np.dot(embeddings[0], embeddings[1])
            / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
        )

        passed = cosine_sim >= threshold
        return ScoreResult(
            scenario_id=scenario.id,
            scorer_name=self.name,
            score=max(0.0, min(1.0, cosine_sim)),
            passed=passed,
            explanation=f"Cosine similarity: {cosine_sim:.3f} (threshold: {threshold})",
            details={"cosine_similarity": cosine_sim, "threshold": threshold},
        )


# Only register if dependencies available — don't fail on import
with contextlib.suppress(Exception):
    register_scorer(SimilarityScorer())
