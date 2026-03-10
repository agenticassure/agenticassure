from __future__ import annotations

import json
from pathlib import Path

from agenticassure.results import RunResult


class JSONReporter:
    """Exports test results to a JSON file."""

    def report(self, result: RunResult, output_path: str | Path | None = None) -> str:
        """Generate JSON report. Returns the JSON string."""
        data = result.model_dump(mode="json")
        json_str = json.dumps(data, indent=2, default=str)

        if output_path:
            Path(output_path).write_text(json_str, encoding="utf-8")

        return json_str
