from __future__ import annotations

from pathlib import Path

from agenticassure.results import RunResult


class HTMLReporter:
    """Generates a single-file HTML report with embedded CSS."""

    def report(self, result: RunResult, output_path: str | Path | None = None) -> str:
        """Generate HTML report. Returns the HTML string."""
        rows = ""
        for sr in result.scenario_results:
            status_class = "pass" if sr.passed else "fail"
            status_text = "PASS" if sr.passed else ("ERROR" if sr.error else "FAIL")
            avg_score = sum(s.score for s in sr.scores) / len(sr.scores) if sr.scores else 0.0
            details = sr.error or "; ".join(s.explanation for s in sr.scores)
            rows += f"""
            <tr class="{status_class}">
                <td>{sr.scenario.name}</td>
                <td><span class="badge {status_class}">{status_text}</span></td>
                <td>{avg_score:.2f}</td>
                <td>{sr.duration_ms:.0f}ms</td>
                <td class="details">{details}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AgenticAssure Report — {result.suite_name}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: #f5f5f5; color: #333; padding: 2rem;
    }}
    .container {{
        max-width: 1000px; margin: 0 auto; background: white;
        border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        padding: 2rem;
    }}
    h1 {{ font-size: 1.5rem; margin-bottom: 0.5rem; }}
    .meta {{ color: #666; font-size: 0.875rem; margin-bottom: 1.5rem; }}
    .summary {{
        display: flex; gap: 2rem; margin-bottom: 1.5rem;
        padding: 1rem; background: #f8f9fa; border-radius: 6px;
    }}
    .stat {{ text-align: center; }}
    .stat-value {{ font-size: 1.5rem; font-weight: bold; }}
    .stat-label {{ font-size: 0.75rem; color: #666; text-transform: uppercase; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{
        text-align: left; padding: 0.75rem; background: #f8f9fa;
        border-bottom: 2px solid #dee2e6; font-size: 0.875rem;
    }}
    td {{ padding: 0.75rem; border-bottom: 1px solid #eee; font-size: 0.875rem; }}
    .badge {{ padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }}
    .badge.pass {{ background: #d4edda; color: #155724; }}
    .badge.fail {{ background: #f8d7da; color: #721c24; }}
    .details {{ white-space: pre-wrap; word-break: break-word; }}
    tr.pass {{ background: #f8fff8; }}
    tr.fail {{ background: #fff8f8; }}
</style>
</head>
<body>
<div class="container">
    <h1>AgenticAssure Report</h1>
    <div class="meta">
        Suite: {result.suite_name} | Run: {result.run_id[:8]} | {result.timestamp.isoformat()}
    </div>
    <div class="summary">
        <div class="stat">
            <div class="stat-value">{result.pass_rate:.0%}</div>
            <div class="stat-label">Pass Rate</div>
        </div>
        <div class="stat">
            <div class="stat-value">{result.aggregate_score:.2f}</div>
            <div class="stat-label">Avg Score</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(result.scenario_results)}</div>
            <div class="stat-label">Scenarios</div>
        </div>
        <div class="stat">
            <div class="stat-value">{result.total_duration_ms:.0f}ms</div>
            <div class="stat-label">Duration</div>
        </div>
    </div>
    <table>
        <thead>
            <tr><th>Scenario</th><th>Status</th><th>Score</th><th>Duration</th><th>Details</th></tr>
        </thead>
        <tbody>{rows}
        </tbody>
    </table>
</div>
</body>
</html>"""

        if output_path:
            Path(output_path).write_text(html, encoding="utf-8")

        return html
