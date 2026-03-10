from __future__ import annotations

from rich.console import Console
from rich.table import Table

from agenticassure.results import RunResult


class CLIReporter:
    """Renders test results to the terminal using Rich."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def report(self, result: RunResult) -> None:
        self.console.print(f"\n[bold]Run Results: {result.suite_name}[/bold]")
        self.console.print(f"Run ID: {result.run_id}")
        self.console.print(f"Timestamp: {result.timestamp.isoformat()}")
        self.console.print()

        table = Table()
        table.add_column("Scenario", style="bold")
        table.add_column("Status")
        table.add_column("Score", justify="right")
        table.add_column("Duration", justify="right")
        table.add_column("Details")

        for sr in result.scenario_results:
            status = "[green]PASS[/green]" if sr.passed else "[red]FAIL[/red]"
            if sr.error:
                status = "[red]ERROR[/red]"

            avg_score = sum(s.score for s in sr.scores) / len(sr.scores) if sr.scores else 0.0

            details = sr.error or "; ".join(s.explanation for s in sr.scores)

            table.add_row(
                sr.scenario.name,
                status,
                f"{avg_score:.2f}",
                f"{sr.duration_ms:.0f}ms",
                details,
            )

        self.console.print(table)
        self.console.print()

        if result.pass_rate >= 0.8:
            pass_rate_color = "green"
        elif result.pass_rate >= 0.5:
            pass_rate_color = "yellow"
        else:
            pass_rate_color = "red"
        self.console.print(
            f"[bold]Summary:[/bold] "
            f"[{pass_rate_color}]{result.pass_rate:.0%} passed[/{pass_rate_color}] | "
            f"Score: {result.aggregate_score:.2f} | "
            f"Duration: {result.total_duration_ms:.0f}ms"
        )
