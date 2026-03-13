from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class Scenario(BaseModel):
    """A single test scenario for an AI agent."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str | None = None
    input: str
    expected_output: str | None = None
    expected_tools: list[str] | None = None
    expected_tool_args: dict[str, Any] | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    scorers: list[str] = Field(default_factory=lambda: ["passfail"])
    timeout_seconds: float = 30.0


class SuiteConfig(BaseModel):
    """Configuration for a test suite."""

    default_timeout: float = 30.0
    retries: int = 0
    default_scorers: list[str] = Field(default_factory=lambda: ["passfail"])
    fail_fast: bool = False


class Suite(BaseModel):
    """A collection of test scenarios."""

    name: str
    description: str | None = None
    scenarios: list[Scenario] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    config: SuiteConfig = Field(default_factory=SuiteConfig)
