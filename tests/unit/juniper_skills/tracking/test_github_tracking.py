"""Tests for the Juniper skill factory GitHub journal."""

from __future__ import annotations

import json
from pathlib import Path

from src.juniper_skills.tracking.comment_codec import StageCommentCodec
from src.juniper_skills.tracking.github_cli import GitHubCommandResult, GitHubRateLimitManager
from src.juniper_skills.tracking.github_tracker import SkillIssueTracker
from src.juniper_skills.tracking.models import DocumentRecord, StageEvent, StageName


class FakeGitHubRunner:
    """Mock `gh` calls without network access."""

    def __init__(self) -> None:
        self.commands: list[list[str]] = []  # Keep every command so tests can assert idempotency.
        self.comments: list[str] = []  # Store issue comments for recovery tests.

    def run(self, command: list[str]) -> GitHubCommandResult:
        """Return deterministic output for known `gh` commands."""
        self.commands.append(command)  # Record the command before returning a fake response.
        if command[:3] == ["gh", "api", "rate_limit"]:  # Simulate a healthy core API bucket.
            return GitHubCommandResult(0, json.dumps({"rate": {"remaining": 5000, "reset": 2000}}), "")
        if command[:4] == ["gh", "issue", "list", "--repo"]:  # Simulate no existing issue.
            return GitHubCommandResult(0, "[]", "")
        if command[:3] == ["gh", "label", "create"]:  # Simulate successful label creation.
            return GitHubCommandResult(0, "", "")
        if command[:3] == ["gh", "issue", "create"]:  # Simulate a created issue URL.
            return GitHubCommandResult(0, "https://github.com/jmorrison-juniper/MistHelper/issues/9999\n", "")
        if command[:3] == ["gh", "issue", "view"]:  # Return issue metadata or comments.
            return self._issue_view(command)
        if command[:3] == ["gh", "issue", "comment"]:  # Store the stage comment body.
            self.comments.append(command[-1])  # The `--body` value is the final argument.
            return GitHubCommandResult(0, "https://example.invalid/comment\n", "")
        if command[:2] == ["gh", "api"]:  # Simulate a successful sub-issue link.
            return GitHubCommandResult(0, "{}", "")
        return GitHubCommandResult(1, "", "unexpected command")  # Fail unknown commands.

    def _issue_view(self, command: list[str]) -> GitHubCommandResult:
        """Return fake issue metadata or fake comments."""
        if "comments" in command[-1]:  # Detect the recovery comment read request.
            payload = {"comments": [{"body": comment} for comment in self.comments]}  # Mirror GitHub JSON shape.
            return GitHubCommandResult(0, json.dumps(payload), "")
        return GitHubCommandResult(0, json.dumps({"id": 123456}), "")  # Return the REST ID for sub-issues.


class TestStageCommentCodec:
    """Verify the comment format that crash recovery reads."""

    def test_comment_round_trip_returns_exact_resume_point(self) -> None:
        document_key = "guides-junos-beginners-guide-md"  # Use the stable key shape the tracker creates.
        event = StageEvent(document_key, StageName.REWRITTEN, "continue", 99, "2026-09-18T03:00:00Z")  # Seed state.
        codec = StageCommentCodec()  # Use the production parser and renderer.
        comment = codec.build_comment(event)  # Render the GitHub issue comment.
        resume_point = codec.parse_comments([comment], document_key)  # Parse the comment back into recovery state.
        assert resume_point.completed_stage == StageName.REWRITTEN  # Confirm the exact completed stage.
        assert resume_point.next_action == "run the guarded stage"  # Confirm the next action follows stage order.
        assert resume_point.issue_number == 99  # Confirm the issue link survives the round trip.


class TestSkillIssueTracker:
    """Verify local mirroring, idempotency, and crash recovery."""

    def test_tracker_records_and_recovers_after_mid_stage_crash(self) -> None:
        database_path = self._database_path("roundtrip")  # Use a repo-local database for the test.
        self._remove_database(database_path)  # Start with a clean local mirror.
        runner = FakeGitHubRunner()  # Use a fake runner so no network call occurs.
        tracker = SkillIssueTracker(database_path, issue_shape="document", runner=runner)  # Build the real tracker.
        document = self._document()  # Build one source document for the journal.
        tracker.record_stage(document, StageName.QUEUED)  # Record the queued stage as complete.
        tracker.record_stage(document, StageName.SEGMENTED)  # Record the segmented stage as complete.
        tracker.record_stage(document, StageName.REWRITTEN)  # Simulate a crash before the guarded stage completes.
        resume_point = tracker.resume_point(document)  # Recover from GitHub comments and the local mirror.
        assert resume_point.completed_stage == StageName.REWRITTEN  # Confirm no uncompleted stage advanced.
        assert resume_point.next_action == "run the guarded stage"  # Confirm the resumed action is exact.
        assert len(runner.comments) == 3  # Confirm each stage produced one GitHub journal comment.
        self._remove_database(database_path)  # Clean the repo-local database after the test.

    def test_tracker_does_not_create_duplicate_issue_after_restart(self) -> None:
        database_path = self._database_path("idempotent")  # Use a repo-local database for the test.
        self._remove_database(database_path)  # Start with no prior local issue link.
        runner = FakeGitHubRunner()  # Use a fake runner to count issue creation calls.
        tracker = SkillIssueTracker(database_path, issue_shape="document", runner=runner)  # Build the first tracker.
        document = self._document()  # Build the same document for both calls.
        first_issue = tracker.ensure_issue(document)  # Create the lazy issue on first use.
        second_issue = tracker.ensure_issue(document)  # Reuse the local issue link on second use.
        create_calls = [
            command for command in runner.commands if command[:3] == ["gh", "issue", "create"]
        ]  # Count creates.
        assert first_issue == second_issue == 9999  # Confirm both calls return the same issue.
        assert len(create_calls) == 1  # Confirm idempotency prevents a duplicate issue.
        self._remove_database(database_path)  # Clean the repo-local database after the test.

    def _document(self) -> DocumentRecord:
        """Return one document record for tests."""
        return DocumentRecord(  # Keep the test document small and deterministic.
            Path("guides") / "junos-beginners-guide.md",
            "Junos Beginners Guide",
            "guides",
            42,
            "junos",
        )

    def _database_path(self, name: str) -> Path:
        """Return a repo-local SQLite path for one test."""
        return Path("data") / "juniper_skills" / f"test_tracking_{name}.db"  # Avoid external temporary paths.

    def _remove_database(self, database_path: Path) -> None:
        """Remove a repo-local SQLite path if it exists."""
        if database_path.exists():  # Leave the test independent of earlier failures.
            database_path.unlink()  # Remove only the test database file.


class TestGitHubRateLimitManager:
    """Verify rate-limit backoff behavior."""

    def test_rate_limit_backoff_waits_until_reset(self, monkeypatch) -> None:
        waits: list[int] = []  # Capture sleep calls without delaying the test.
        runner = LowLimitRunner()  # Return a low rate limit to trigger backoff.
        manager = GitHubRateLimitManager(runner, minimum_remaining=10)  # Require more calls than remain.
        monkeypatch.setattr("src.juniper_skills.tracking.github_cli.time.time", lambda: 1000)  # Freeze current time.
        monkeypatch.setattr("src.juniper_skills.tracking.github_cli.time.sleep", waits.append)  # Capture sleep seconds.
        manager.wait_if_needed()  # Exercise the backoff path.
        assert waits == [6]  # Confirm reset minus current time plus one guard second.


class LowLimitRunner:
    """Mock a rate-limit response that requires backoff."""

    def run(self, command: list[str]) -> GitHubCommandResult:
        """Return one low-limit response."""
        payload = {"rate": {"remaining": 1, "reset": 1005}}  # Force a small wait from the manager.
        return GitHubCommandResult(0, json.dumps(payload), "")  # Match the GitHub CLI result shape.
