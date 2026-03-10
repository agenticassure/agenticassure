"""Built-in scorers for evaluating agent responses."""

import contextlib

from agenticassure.scorers.base import Scorer, get_scorer
from agenticassure.scorers.exact import ExactMatchScorer
from agenticassure.scorers.passfail import PassFailScorer
from agenticassure.scorers.regex import RegexScorer

# Similarity scorer requires optional dependencies (sentence-transformers)
with contextlib.suppress(ImportError):
    from agenticassure.scorers.similarity import SimilarityScorer

__all__ = ["ExactMatchScorer", "PassFailScorer", "RegexScorer", "Scorer", "get_scorer"]
