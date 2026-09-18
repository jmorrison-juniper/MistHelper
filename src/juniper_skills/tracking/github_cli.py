"""GitHub CLI access for the Juniper skill factory journal."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GitHubCommandResult:
    """A completed GitHub CLI command."""

    returncode: int
    stdout: str
    stderr: str


class GitHubCliError(RuntimeError):
    """Raised when the GitHub CLI returns an error."""


class GitHubRateLimitExhausted(GitHubCliError):
    """Raised when the GitHub API limit cannot support more writes."""

    def __init__(self, reset_epoch: int) -> None:
        self.reset_epoch = reset_epoch  # Keep the reset time so the queue can report the delay.
        super().__init__(f"GitHub API rate limit exhausted until {reset_epoch}")  # Give operators a clear reason.


class GitHubRateLimitManager:
    """Measure and react to the GitHub API rate limit."""

    def __init__(self, runner: GitHubCliRunner, minimum_remaining: int = 10) -> None:
        self.runner = runner  # Reuse the same runner so tests can mock all `gh` calls.
        self.minimum_remaining = minimum_remaining  # Leave room for the operator and other agents.

    def read_rate_limit(self) -> dict[str, Any]:
        """Return the current GitHub API rate limit object."""
        logging.info("Reading the GitHub API rate limit")  # Record the network check.
        result = self.runner.run(["gh", "api", "rate_limit"])  # Ask GitHub for the measured limit.
        payload = json.loads(result.stdout)  # Parse the CLI JSON so callers can make decisions.
        logging.debug("GitHub core limit has %s calls remaining", payload["rate"]["remaining"])  # Record safe evidence.
        return payload

    def defer_if_needed(self) -> None:
        """Raise a retryable error when the core API limit is too low."""
        rate_limit = self.read_rate_limit()["rate"]  # Read the core bucket that issue writes use.
        remaining = int(rate_limit["remaining"])  # Convert the value for the threshold comparison.
        if remaining >= self.minimum_remaining:  # Continue when enough calls remain.
            logging.debug("GitHub API limit permits a queued write with %d calls remaining", remaining)  # Record state.
            return
        reset_epoch = int(rate_limit["reset"])  # Keep the reset time for the queued retry.
        logging.info("Deferring GitHub sync until rate-limit reset %d", reset_epoch)  # Record nonblocking backoff.
        raise GitHubRateLimitExhausted(reset_epoch)  # Stop the background sync without losing local state.

    def wait_if_needed(self) -> None:
        """Sleep when the core API limit is too low."""
        rate_limit = self.read_rate_limit()["rate"]  # Read the core bucket that issue calls use.
        remaining = int(rate_limit["remaining"])  # Convert the value for the threshold comparison.
        if remaining >= self.minimum_remaining:  # Continue when enough calls remain.
            logging.debug("GitHub API limit is sufficient with %d calls remaining", remaining)  # Record no-wait state.
            return
        wait_seconds = max(1, int(rate_limit["reset"]) - int(time.time()) + 1)  # Wait until reset plus a guard second.
        logging.info("Waiting %d seconds for the GitHub API rate limit", wait_seconds)  # Record the backoff reason.
        time.sleep(wait_seconds)  # Back off to avoid secondary throttling.
        logging.debug("GitHub API rate limit wait finished")  # Record the end of the backoff.


class GitHubCliRunner:
    """Run `gh` commands without reading tokens."""

    def __init__(self, timeout_seconds: int = 60) -> None:
        self.timeout_seconds = timeout_seconds  # Bound each call so the pipeline can continue later.
        self.api_call_count = 0  # Count CLI calls for throughput reports without reading credentials.

    def run(self, command: list[str]) -> GitHubCommandResult:
        """Run one GitHub CLI command and return its output."""
        logging.info("Running a GitHub CLI command: %s", self._safe_command(command))  # Log the action without secrets.
        self.api_call_count += 1  # Measure writes and reads that pass through the GitHub CLI.
        completed = subprocess.run(  # Use subprocess because the contract requires the `gh` CLI.
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=self.timeout_seconds,
        )
        result = GitHubCommandResult(completed.returncode, completed.stdout, completed.stderr)  # Store command output.
        logging.debug("GitHub CLI command returned code %d", result.returncode)  # Record the non-secret result.
        if result.returncode != 0:  # Convert CLI failures into a typed exception.
            raise GitHubCliError(result.stderr.strip() or result.stdout.strip())
        return result

    def run_with_input(self, command: list[str], input_text: str) -> GitHubCommandResult:
        """Run one GitHub CLI command with standard input."""
        logging.info("Running a GitHub CLI command with input: %s", self._safe_command(command))  # Log safe action.
        self.api_call_count += 1  # Count this network operation for throughput reports.
        completed = subprocess.run(  # Use stdin for GitHub API JSON bodies that update labels atomically.
            command,
            capture_output=True,
            check=False,
            input=input_text,
            text=True,
            timeout=self.timeout_seconds,
        )
        result = GitHubCommandResult(completed.returncode, completed.stdout, completed.stderr)  # Store output safely.
        logging.debug("GitHub CLI command with input returned code %d", result.returncode)  # Record safe status.
        if result.returncode != 0:  # Convert CLI failures into a typed exception.
            raise GitHubCliError(result.stderr.strip() or result.stdout.strip())
        return result

    def _safe_command(self, command: list[str]) -> str:
        """Return a log-safe command string."""
        safe_parts = ["***" if "token" in part.lower() else part for part in command]  # Redact token-like arguments.
        return " ".join(safe_parts)  # Store a readable command for logs.
