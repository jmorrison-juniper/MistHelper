"""GitHub issue tracker for the Juniper skill factory."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from src.juniper_skills.tracking.comment_codec import StageCommentCodec
from src.juniper_skills.tracking.github_cli import GitHubCliError, GitHubCliRunner, GitHubRateLimitManager
from src.juniper_skills.tracking.models import DocumentRecord, ResumePoint, StageEvent, StageName
from src.juniper_skills.tracking.recovery import SkillIssueRecoveryReader
from src.juniper_skills.tracking.store import FactoryJournalStore


class SkillIssueTracker:
    """Open and update lazy GitHub journal issues for skill factory work."""

    def __init__(
        self,
        database_path: Path,
        repo: str = "jmorrison-juniper/MistHelper",
        parent_issue: int = 2925,
        issue_shape: str = "domain",
        runner: GitHubCliRunner | None = None,
    ) -> None:
        self.repo = repo  # Store the repository owner and name for each `gh` command.
        self.parent_issue = parent_issue  # Link created journals back to the factory issue.
        self.issue_shape = issue_shape  # Select domain journals by default to avoid 1,500 visible issues.
        self.runner = runner or GitHubCliRunner()  # Allow tests to supply a fake `gh` runner.
        self.rate_limit = GitHubRateLimitManager(self.runner)  # Measure real limits before GitHub calls.
        self.store = FactoryJournalStore(database_path)  # Persist all work before any network call.
        self.codec = StageCommentCodec()  # Encode journal comments in one stable format.

    def ensure_issue(self, document: DocumentRecord) -> int | None:
        """Return the journal issue number, creating it lazily if needed."""
        logging.info("Ensuring a lazy GitHub journal issue exists")  # Record the high-level action.
        self.store.save_document(document, self.issue_shape)  # Mirror document metadata before a network action.
        issue_number = self.store.get_issue_number(document.document_key)  # Reuse a local issue link if it exists.
        if issue_number is not None:  # Avoid duplicate issue creation on retries.
            logging.debug("Using local journal issue %d", issue_number)  # Record the idempotent result.
            return issue_number
        issue_number = self._find_or_create_issue(document)  # Search GitHub before creating a lazy issue.
        self.store.save_issue_number(document.document_key, issue_number)  # Persist the link for future retries.
        logging.debug("Ensured GitHub journal issue %d", issue_number)  # Record the created or found issue.
        return issue_number

    def record_stage(
        self,
        document: DocumentRecord,
        stage: StageName,
        details: dict[str, object] | None = None,
        sync: bool = True,
    ) -> int:
        """Store a stage event and optionally sync one GitHub comment."""
        logging.info("Recording a skill factory stage transition")  # Record the durable journal action.
        issue_number = self.ensure_issue(document)  # Create the journal only when the document enters the pipeline.
        event = self._stage_event(document, stage, issue_number, details or {})  # Build the exact recovery state.
        comment_body = self.codec.build_comment(event)  # Create the GitHub-ready comment text.
        event_id = self.store.enqueue_stage_event(event, comment_body)  # Save the local mirror before the network call.
        self.sync_pending(limit=1) if sync else logging.debug("Deferred GitHub sync for stage event %d", event_id)
        return event_id

    def sync_pending(self, limit: int = 25) -> int:
        """Send queued comments to GitHub."""
        logging.info("Reconciling local journal events to GitHub")  # Record the sync action.
        synced_count = 0  # Count successful comments for caller evidence.
        for event in self.store.unsynced_stage_events(limit):  # Send a bounded batch to respect the API limit.
            synced_count += self._sync_one_event(event)  # Try one event and keep later events available.
        logging.debug("Synced %d journal events to GitHub", synced_count)  # Record the sync result.
        return synced_count

    def resume_point(self, document: DocumentRecord) -> ResumePoint:
        """Return the next action for a document after a crash."""
        logging.info("Reading the crash recovery point for a document")  # Record the recovery action.
        issue_number = self.store.get_issue_number(document.document_key)  # Use the local issue link if present.
        reader = SkillIssueRecoveryReader(self.store, self.runner, self.rate_limit, self.repo)  # Build the reader.
        return reader.resume_point(document.document_key, issue_number)  # Reconstruct the exact resume point.

    def _find_or_create_issue(self, document: DocumentRecord) -> int:
        """Search for a journal issue and create one only when absent."""
        title = self._issue_title(document)  # Build the idempotency key that GitHub search can find.
        found_issue = self._search_issue(title)  # Search before create to avoid duplicate issues.
        if found_issue is not None:  # Reuse the existing issue when a prior run created it.
            return found_issue
        return self._create_issue(document, title)  # Create the lazy issue only after no match exists.

    def _search_issue(self, title: str) -> int | None:
        """Search GitHub for an exact journal title."""
        logging.info("Searching GitHub for an existing journal issue")  # Record the idempotency search.
        self.rate_limit.wait_if_needed()  # Avoid rate-limit failures before search.
        query = f'repo:{self.repo} in:title "{title}"'  # Scope search to this repository and exact title text.
        result = self.runner.run(  # Ask GitHub for a small JSON result set.
            ["gh", "issue", "list", "--repo", self.repo, "--state", "all", "--search", query, "--json", "number,title"]
        )
        matches = json.loads(result.stdout)  # Decode the result set for exact title comparison.
        issue_number = next(
            (int(item["number"]) for item in matches if item["title"] == title),
            None,
        )  # Find exact match.
        logging.debug("GitHub journal issue search found %s", issue_number)  # Record the idempotency result.
        return issue_number

    def _create_issue(self, document: DocumentRecord, title: str) -> int:
        """Create a GitHub journal issue."""
        logging.info("Creating a lazy GitHub journal issue")  # Record the network create action.
        self._ensure_labels(document.domain)  # Ensure filters exist before the issue uses them.
        self.rate_limit.wait_if_needed()  # Avoid rate-limit failures before issue creation.
        result = self.runner.run(  # Create one issue for the selected safe shape.
            [
                "gh",
                "issue",
                "create",
                "--repo",
                self.repo,
                "--title",
                title,
                "--body",
                self._issue_body(document),
                "--label",
                f"skill-factory,domain:{document.domain}",
            ]
        )
        issue_number = self._issue_number_from_url(result.stdout)  # Read the created number from the CLI URL.
        issue_id = self._issue_id(issue_number)  # Read the REST ID that the sub-issue API needs.
        self._link_parent_issue(issue_number, issue_id)  # Try to connect the issue to #2925.
        logging.debug("Created GitHub journal issue %d", issue_number)  # Record the created issue number.
        return issue_number

    def _issue_number_from_url(self, output: str) -> int:
        """Read the issue number from the `gh issue create` output URL."""
        issue_number = int(output.rstrip().split("/")[-1])  # The CLI returns the issue URL on success.
        logging.debug("Parsed created issue number %d", issue_number)  # Record the parsed issue number.
        return issue_number

    def _issue_id(self, issue_number: int) -> int:
        """Read the database ID that the GitHub sub-issue API uses."""
        logging.info("Reading the GitHub issue REST ID")  # Record the metadata read.
        result = self.runner.run(  # Ask `gh` for the issue ID after creation.
            ["gh", "issue", "view", str(issue_number), "--repo", self.repo, "--json", "id"]
        )
        payload = json.loads(result.stdout)  # Decode the issue metadata response.
        logging.debug("Read GitHub issue REST ID for issue %d", issue_number)  # Record safe issue context.
        return int(payload["id"])

    def _ensure_labels(self, domain: str) -> None:
        """Create the labels that make journal issues easy to filter."""
        labels = [("skill-factory", "0969da"), (f"domain:{domain}", "d4c5f9")]  # Use predictable label names.
        for name, color in labels:  # Create both labels if the repository does not have them yet.
            self._ensure_one_label(name, color)  # Keep one label create small and recoverable.

    def _ensure_one_label(self, name: str, color: str) -> None:
        """Create one GitHub label if it does not exist."""
        try:
            self.runner.run(["gh", "label", "create", name, "--repo", self.repo, "--color", color])  # Create label.
            logging.debug("Created GitHub label %s", name)  # Record the created label.
        except GitHubCliError as error:
            logging.debug("GitHub label %s already exists or cannot be created: %s", name, error)  # Keep idempotency.

    def _link_parent_issue(self, issue_number: int, issue_id: int) -> None:
        """Attach the journal issue to the parent issue when the API permits it."""
        logging.info("Linking the journal issue to the parent issue")  # Record the parent-link action.
        try:
            self.runner.run(  # Use the GitHub sub-issue API when it is available for this repository.
                [
                    "gh",
                    "api",
                    f"repos/{self.repo}/issues/{self.parent_issue}/sub_issues",
                    "-f",
                    f"sub_issue_id={issue_id}",
                ]
            )
            logging.debug("Linked issue %d as a sub-issue of %d", issue_number, self.parent_issue)  # Record success.
        except GitHubCliError as error:
            logging.debug("Sub-issue link failed for issue %d: %s", issue_number, error)  # Preserve core tracking.

    def _sync_one_event(self, event: dict[str, object]) -> int:
        """Send one queued stage event to GitHub."""
        try:
            self.rate_limit.wait_if_needed()  # Measure the API bucket before the comment call.
            self.runner.run(  # Write the crash-recovery journal comment to GitHub.
                [
                    "gh",
                    "issue",
                    "comment",
                    str(event["issue_number"]),
                    "--repo",
                    self.repo,
                    "--body",
                    str(event["comment_body"]),
                ]
            )
            self.store.mark_stage_event_synced(int(event["id"]))  # Mark the row only after GitHub accepts it.
            return 1
        except GitHubCliError as error:
            logging.debug("Deferred GitHub journal sync after error: %s", error)  # Leave the row queued for retry.
            return 0

    def _stage_event(
        self,
        document: DocumentRecord,
        stage: StageName,
        issue_number: int | None,
        details: dict[str, object],
    ) -> StageEvent:
        """Create a stage event with a deterministic next action."""
        created_at = datetime.now(UTC).isoformat()  # Use UTC so comments sort the same on every machine.
        next_action = self._next_action_for_stage(stage)  # Store the exact action the recovery reader reports.
        return StageEvent(document.document_key, stage, next_action, issue_number, created_at, details)  # Return state.

    def _next_action_for_stage(self, stage: StageName) -> str:
        """Return the stored next action for one completed stage."""
        if stage == StageName.FAILED:  # A failed stage requires repair before more pipeline work.
            return "repair the failed stage"
        if stage == StageName.VERIFIED:  # A verified document completed the pipeline.
            return "no action"
        return "continue the document pipeline"  # The codec expands this from the exact completed stage.

    def _issue_title(self, document: DocumentRecord) -> str:
        """Return the selected issue title."""
        if self.issue_shape == "document":  # Support the original one-issue-per-document shape when required.
            return f"[skill-factory] Convert {document.title} ({document.document_key})"
        return f"[skill-factory] Domain {document.domain} conversion journal"  # Default to the safer domain shape.

    def _issue_body(self, document: DocumentRecord) -> str:
        """Return the GitHub issue body for the journal."""
        checklist = "\n".join(f"- [ ] {stage.value}" for stage in StageName)  # Show every required stage.
        shape_note = self._shape_note(document)  # Explain the chosen scale-safe journal shape.
        return "\n".join(  # Build clear STE prose for recovery readers.
            [
                "This issue is a crash-recovery journal for the Juniper skill factory.",
                "",
                f"Source document: {document.title}",
                f"Category: {document.category}",
                f"Page count: {document.page_count}",
                f"Source path: `{document.source_path}`",
                f"Assigned domain skill: `juniper-{document.domain}`",
                f"Journal shape: {self.issue_shape}",
                "",
                shape_note,
                "",
                "Stage checklist:",
                checklist,
                "",
                f"Parent factory issue: #{self.parent_issue}",
            ]
        )

    def _shape_note(self, document: DocumentRecord) -> str:
        """Explain the issue shape tradeoff in the issue body."""
        if self.issue_shape == "document":  # Explain the explicit high-detail shape.
            return "This document entered the pipeline, so the factory created its issue lazily."
        return (  # Explain why one domain issue can hold many document events.
            "This domain journal prevents the repository issue list from holding one issue for each source document. "
            f"Comments identify each document with the key `{document.document_key}`."
        )
