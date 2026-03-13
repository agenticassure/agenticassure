"""Example: Running AgenticAssure with a simple mock agent."""

from agenticassure import AgentResult, Scenario, Suite
from agenticassure.results import ToolCall
from agenticassure.runner import Runner


class MySimpleAgent:
    """A mock agent for demonstration purposes."""

    def run(self, input: str, context=None):
        # Simulate an agent that always searches and responds
        return AgentResult(
            output=f"I found results for: {input}",
            tool_calls=[
                ToolCall(name="search", arguments={"query": input}, result="Some results"),
            ],
            latency_ms=150.0,
        )


def main():
    # Create scenarios programmatically
    suite = Suite(
        name="demo-suite",
        scenarios=[
            Scenario(
                name="basic_search",
                input="What is the weather in NYC?",
                expected_tools=["search"],
                scorers=["passfail"],
            ),
            Scenario(
                name="greeting",
                input="Hello!",
                scorers=["passfail"],
            ),
        ],
    )

    # Run with the mock agent
    runner = Runner(adapter=MySimpleAgent())
    result = runner.run_suite(suite)

    # Print results
    from agenticassure.reports.cli_report import CLIReporter

    CLIReporter().report(result)


if __name__ == "__main__":
    main()
