from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from agenticassure import __version__

console = Console()


def _import_adapter(dotted_path: str) -> Any:
    """Dynamically import and instantiate an adapter class from a dotted path.

    Args:
        dotted_path: A Python dotted path such as ``mymodule.MyAgent``.
            The last component is treated as the class name; everything
            before it is treated as the module path.

    Returns:
        An instance of the adapter class.

    Raises:
        click.ClickException: If the module cannot be imported or the class
            cannot be found / instantiated.
    """
    if "." not in dotted_path:
        raise click.ClickException(
            f"Invalid adapter path '{dotted_path}'. "
            "Expected a dotted path like 'mymodule.MyAdapter'."
        )

    module_path, class_name = dotted_path.rsplit(".", 1)

    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise click.ClickException(
            f"Could not import module '{module_path}': {exc}\n"
            "Make sure the module is installed or on your PYTHONPATH."
        ) from exc

    try:
        adapter_cls = getattr(module, class_name)
    except AttributeError as exc:
        raise click.ClickException(
            f"Module '{module_path}' has no attribute '{class_name}'."
        ) from exc

    try:
        instance = adapter_cls()
    except Exception as exc:
        raise click.ClickException(f"Failed to instantiate adapter '{class_name}': {exc}") from exc

    from agenticassure.adapters.base import AgentAdapter

    if not isinstance(instance, AgentAdapter):
        raise click.ClickException(
            f"'{dotted_path}' does not implement the AgentAdapter protocol. "
            "It must have a run(input, context=None) -> AgentResult method."
        )

    return instance


def _resolve_adapter_from_config() -> str | None:
    """Look for an agenticassure config file in the cwd and return the adapter path."""
    yaml_path = Path("agenticassure.yaml")
    toml_path = Path("agenticassure.toml")

    if yaml_path.exists():
        try:
            import yaml  # type: ignore[import-untyped]

            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            adapter_value = data.get("adapter")
            if adapter_value:
                return str(adapter_value)
        except Exception:
            pass

    if toml_path.exists():
        try:
            if sys.version_info >= (3, 11):
                import tomllib
            else:
                import tomli as tomllib  # type: ignore[no-redef]

            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
            adapter_value = data.get("adapter")
            if adapter_value:
                return str(adapter_value)
        except Exception:
            pass

    return None


def _list_suites_dry_run(suites: list[Any], tags: list[str] | None) -> None:
    """Print a summary table of suites/scenarios for dry-run or no-adapter mode."""
    table = Table(title="Scenarios (dry run)")
    table.add_column("Suite", style="cyan")
    table.add_column("Scenario", style="bold")
    table.add_column("Input", max_width=50)
    table.add_column("Scorers")
    table.add_column("Tags", style="dim")

    count = 0
    for s in suites:
        for scenario in s.scenarios:
            if tags and not set(tags).intersection(scenario.tags):
                continue
            table.add_row(
                s.name,
                scenario.name,
                scenario.input[:50] + ("..." if len(scenario.input) > 50 else ""),
                ", ".join(scenario.scorers),
                ", ".join(scenario.tags) if scenario.tags else "-",
            )
            count += 1

    console.print(table)
    console.print(f"\n[dim]{count} scenario(s) found[/dim]")


@click.group()
@click.version_option(version=__version__, prog_name="agenticassure")
def cli() -> None:
    """AgenticAssure — Test and benchmark LLM-powered AI agents."""
    pass


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--suite", "-s", help="Run only the named suite")
@click.option("--tag", "-t", multiple=True, help="Filter scenarios by tag")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["cli", "json", "html"]),
    default="cli",
    help="Output format",
)
@click.option("--timeout", type=float, default=30.0, help="Default timeout in seconds")
@click.option("--retry", type=int, default=0, help="Number of retries per scenario")
@click.option(
    "--adapter",
    "-a",
    default=None,
    help="Python dotted path to an AgentAdapter class (e.g. 'mymodule.MyAgent')",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Validate and list scenarios without running them",
)
def run(
    path: str,
    suite: str | None,
    tag: tuple[str, ...],
    output: str,
    timeout: float,
    retry: int,
    adapter: str | None,
    dry_run: bool,
) -> None:
    """Run test scenarios against an agent."""
    from agenticassure.loader import load_scenarios, load_scenarios_from_dir

    # --- Load suites ---
    p = Path(path)
    try:
        if p.is_file():
            suites = [load_scenarios(p)]
        elif p.is_dir():
            suites = load_scenarios_from_dir(p)
        else:
            console.print(f"[red]Invalid path: {path}[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error loading scenarios: {e}[/red]")
        sys.exit(1)

    if suite:
        suites = [s for s in suites if s.name == suite]
        if not suites:
            console.print(f"[red]Suite '{suite}' not found[/red]")
            sys.exit(1)

    tags = list(tag) if tag else None

    total_scenarios = sum(len(s.scenarios) for s in suites)
    console.print(f"[bold]Loaded {total_scenarios} scenario(s) from {len(suites)} suite(s)[/bold]")

    # --- Dry-run mode ---
    if dry_run:
        _list_suites_dry_run(suites, tags)
        return

    # --- Resolve adapter ---
    adapter_path = adapter
    if adapter_path is None:
        adapter_path = _resolve_adapter_from_config()

    if adapter_path is None:
        console.print()
        _list_suites_dry_run(suites, tags)
        console.print()
        console.print(
            "[yellow]No adapter provided. Scenarios were validated but not executed.[/yellow]"
        )
        console.print("[yellow]To run scenarios, supply an adapter in one of these ways:[/yellow]")
        console.print(
            "  1. [bold]--adapter[/bold] flag:  "
            "agenticassure run --adapter mymodule.MyAgent scenarios/"
        )
        console.print(
            "  2. [bold]Config file[/bold]:     "
            "create agenticassure.yaml with 'adapter: mymodule.MyAgent'"
        )
        return

    adapter_instance = _import_adapter(adapter_path)
    console.print(f"[dim]Using adapter: {adapter_path}[/dim]")

    # --- Run suites ---
    from agenticassure.reports import CLIReporter, HTMLReporter, JSONReporter
    from agenticassure.runner import Runner

    runner = Runner(
        adapter=adapter_instance,
        default_timeout=timeout,
        retries=retry,
    )

    from rich.status import Status

    all_results = []
    for s in suites:
        with Status(
            f"[bold cyan]Running suite: {s.name}[/bold cyan]",
            console=console,
            spinner="dots",
        ):
            result = runner.run_suite(s, tags=tags)
        all_results.append(result)

    # --- Report ---
    for result in all_results:
        if output == "cli":
            cli_reporter = CLIReporter(console=console)
            cli_reporter.report(result)
        elif output == "json":
            json_reporter = JSONReporter()
            filename = f"results_{result.run_id}.json"
            json_reporter.report(result, output_path=filename)
            console.print(f"[green]JSON report written to {filename}[/green]")
        elif output == "html":
            html_reporter = HTMLReporter()
            filename = f"report_{result.run_id}.html"
            html_reporter.report(result, output_path=filename)
            console.print(f"[green]HTML report written to {filename}[/green]")

    # --- Final summary across all suites ---
    if len(all_results) > 1:
        total_scenarios_run = sum(len(r.scenario_results) for r in all_results)
        total_passed = sum(sum(1 for sr in r.scenario_results if sr.passed) for r in all_results)
        console.print(
            f"\n[bold]Overall: {total_passed}/{total_scenarios_run} scenarios passed "
            f"across {len(all_results)} suite(s)[/bold]"
        )

    # Exit with non-zero if any scenario failed
    any_failed = any(not sr.passed for r in all_results for sr in r.scenario_results)
    if any_failed:
        sys.exit(1)


@cli.command()
@click.argument("directory", default=".", type=click.Path())
def init(directory: str) -> None:
    """Scaffold a new AgenticAssure project with example scenarios."""
    target = Path(directory)
    scenarios_dir = target / "scenarios"
    scenarios_dir.mkdir(parents=True, exist_ok=True)

    example_yaml = """suite:
  name: example-agent-tests
  description: Example test scenarios for your AI agent
  config:
    default_timeout: 30
    retries: 1

scenarios:
  - name: basic_greeting
    input: "Hello, how are you?"
    expected_output: "hello"
    scorers:
      - passfail
    tags:
      - basic

  - name: tool_usage
    input: "What is the weather in San Francisco?"
    expected_tools:
      - get_weather
    expected_tool_args:
      get_weather:
        location: "San Francisco"
    scorers:
      - passfail
    tags:
      - tools
"""
    example_file = scenarios_dir / "example_scenarios.yaml"
    example_file.write_text(example_yaml, encoding="utf-8")

    console.print(f"[green]Initialized AgenticAssure project in {target.resolve()}[/green]")
    console.print(f"  Created: {example_file}")
    console.print("\nNext steps:")
    console.print("  1. Edit scenarios in the 'scenarios/' directory")
    console.print("  2. Create an adapter for your agent")
    console.print("  3. Run: agenticassure run scenarios/")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def validate(path: str) -> None:
    """Validate YAML scenario files without running them."""
    from agenticassure.loader import validate_scenario_file

    p = Path(path)
    files = list(p.glob("**/*.y*ml")) if p.is_dir() else [p]
    files = [f for f in files if f.suffix in (".yml", ".yaml")]

    if not files:
        console.print("[yellow]No YAML files found[/yellow]")
        return

    all_valid = True
    for f in files:
        issues = validate_scenario_file(f)
        if issues:
            all_valid = False
            console.print(f"[red]FAIL {f}[/red]")
            for issue in issues:
                console.print(f"    {issue}")
        else:
            console.print(f"[green]OK {f}[/green]")

    if all_valid:
        console.print(f"\n[green]All {len(files)} file(s) valid[/green]")
    else:
        console.print("\n[red]Validation failed[/red]")
        sys.exit(1)


@cli.command("list")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--tag", "-t", multiple=True, help="Filter by tag")
@click.option("--json-output", is_flag=True, help="Output as JSON")
def list_scenarios(path: str, tag: tuple[str, ...], json_output: bool) -> None:
    """List all scenarios with metadata."""
    from agenticassure.loader import load_scenarios, load_scenarios_from_dir

    p = Path(path)
    try:
        suites = [load_scenarios(p)] if p.is_file() else load_scenarios_from_dir(p)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    tags = set(tag) if tag else None

    if json_output:
        output_data = []
        for s in suites:
            for scenario in s.scenarios:
                if tags and not tags.intersection(scenario.tags):
                    continue
                output_data.append(
                    {
                        "suite": s.name,
                        "name": scenario.name,
                        "input": scenario.input[:80],
                        "scorers": scenario.scorers,
                        "tags": scenario.tags,
                    }
                )
        click.echo(json.dumps(output_data, indent=2))
        return

    table = Table(title="Scenarios")
    table.add_column("Suite", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Input", max_width=50)
    table.add_column("Scorers")
    table.add_column("Tags", style="dim")

    count = 0
    for s in suites:
        for scenario in s.scenarios:
            if tags and not tags.intersection(scenario.tags):
                continue
            table.add_row(
                s.name,
                scenario.name,
                scenario.input[:50] + ("..." if len(scenario.input) > 50 else ""),
                ", ".join(scenario.scorers),
                ", ".join(scenario.tags) if scenario.tags else "-",
            )
            count += 1

    console.print(table)
    console.print(f"\n[dim]{count} scenario(s) found[/dim]")


if __name__ == "__main__":
    cli()
