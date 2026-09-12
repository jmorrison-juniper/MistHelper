"""Report a branch that holds finished work and has no pull request.

A branch with commits above `main` and no pull request has one copy. A cleanup
deletes that copy, and git prints no warning. The repository squash-merges, so
`git branch --merged` never reports a feature branch as merged, and a cleanup
that trusts `--merged` is unsafe.

A pull request makes a branch head permanent, because `refs/pull/<n>/head`
survives a branch deletion. This tool reports every branch that has no such
protection, so an operator can open a pull request before any cleanup.

Issue #1980 recorded five stranded branches. Issue #2251 recorded the deletion
of all five, and one head was unrecoverable.

Run the tool from the repository root.

    python scripts/report_stranded_branches.py
    python scripts/report_stranded_branches.py --min-age-days 14 --fail-on-find
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

# The repository that the tool reads. The tool reports one repository at a time.
DEFAULT_REPOSITORY = "jmorrison-juniper/MistHelper"

# The branch that every feature branch merges into. A branch is stranded only
# when it holds commits that this branch does not hold.
DEFAULT_BASE_BRANCH = "main"

# The age below which the tool stays quiet. A branch that an engineer pushed
# today is active work, and a report on it is noise.
DEFAULT_MIN_AGE_DAYS = 7

# A branch name that the tool never reports. A protected branch and a bot branch
# both follow their own lifecycle, so neither one needs a pull request warning.
IGNORED_PREFIXES = ("dependabot/", "gh-readonly-queue/", "revert-")

# The gh call reaches the GitHub API over the network. A stalled read has no
# bound of its own, so this cap stops it from hanging the whole gate.
_GH_TIMEOUT_SECONDS = 120

# The number of branches that one API page returns. The API caps a page at 100.
_PAGE_SIZE = 100

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class BranchRecord:
    """One branch, with the facts that decide whether it is stranded."""

    name: str
    """The short branch name, such as `fix/1234-a-defect`."""

    sha: str
    """The head commit of the branch."""

    ahead_by: int
    """The count of commits that the branch holds above the base branch."""

    last_commit_at: datetime
    """The commit date of the head, read as an aware UTC value."""

    def age_days(self, now: datetime) -> int:
        """Report the whole days between the head commit and `now`."""
        return max((now - self.last_commit_at).days, 0)  # A negative age means a clock skew.

    def is_stranded(self, open_heads: frozenset[str], min_age_days: int, now: datetime) -> bool:
        """Report whether the branch holds unprotected work.

        A branch is stranded when it holds work above the base branch, no open
        pull request names it as the head, and it is older than the threshold.
        """
        if self.ahead_by < 1:  # A branch at or behind the base holds nothing to lose.
            return False
        if self.name in open_heads:  # An open pull request already protects the head.
            return False
        if self.name.startswith(IGNORED_PREFIXES):  # A bot branch follows its own lifecycle.
            return False
        return self.age_days(now) >= min_age_days  # Recent work is active, not stranded.


class GitHubReader:
    """Read the branch facts from the GitHub API through the `gh` command."""

    def __init__(self, repository: str, base_branch: str) -> None:
        """Store the repository and the base branch that every read uses."""
        self._repository = repository  # The owner and name pair that each path needs.
        self._base_branch = base_branch  # The branch that every comparison starts from.

    def _api(self, path: str) -> object:
        """Call one GitHub API path and return the decoded body."""
        _LOG.info("Reading the GitHub API path %s", path)  # Report the read before the network call.
        command = ["gh", "api", f"repos/{self._repository}/{path}"]  # Build the read-only call.
        result = subprocess.run(  # The argument list is built here, not by a shell.
            command, capture_output=True, text=True, check=True, timeout=_GH_TIMEOUT_SECONDS
        )
        body = json.loads(result.stdout)  # The API answers JSON for every path this tool reads.
        _LOG.debug("The path %s answered %d bytes", path, len(result.stdout))  # Record the size.
        return body

    def list_open_pull_request_heads(self) -> frozenset[str]:
        """Report the head branch name of every open pull request."""
        _LOG.info("Listing the open pull requests")  # Report the plan before the read.
        rows = self._api(f"pulls?state=open&per_page={_PAGE_SIZE}")  # One page holds every open row.
        heads = {_head_ref(row) for row in _as_rows(rows)}  # Keep the head name only.
        _LOG.debug("Found %d open pull requests", len(heads))  # Record the count after the read.
        return frozenset(heads - {""})  # Drop the empty name that an unreadable row answers.

    def list_branches(self) -> list[str]:
        """Report the short name of every branch in the repository."""
        _LOG.info("Listing the branches")  # Report the plan before the read.
        rows = self._api(f"branches?per_page={_PAGE_SIZE}")  # One page holds every branch today.
        names = [str(row["name"]) for row in _as_rows(rows)]  # Keep the branch name only.
        _LOG.debug("Found %d branches", len(names))  # Record the count after the read.
        return names

    def read_branch(self, name: str) -> BranchRecord | None:
        """Compare one branch against the base and build its record."""
        _LOG.info("Comparing the branch %s against %s", name, self._base_branch)  # Report the plan.
        body = self._api(f"compare/{self._base_branch}...{name}")  # The API reports the ahead count.
        if not isinstance(body, dict):  # A malformed body cannot decide a deletion, so skip it.
            return None
        commits = body.get("commits") or []  # An empty list means the branch adds nothing.
        record = BranchRecord(
            name=name,  # Keep the name the caller asked for.
            sha=str(body.get("merge_base_commit", {}).get("sha", ""))[:40],  # Record the fork point.
            ahead_by=int(body.get("ahead_by", 0)),  # The count of commits above the base branch.
            last_commit_at=_head_date(commits),  # The date that decides the age test.
        )
        _LOG.debug("The branch %s is %d commits ahead", name, record.ahead_by)  # Record the result.
        return record


class StrandedBranchReporter:
    """Find every branch that holds work with no pull request behind it."""

    def __init__(
        self,
        list_branches: Callable[[], list[str]],
        read_branch: Callable[[str], BranchRecord | None],
        list_open_heads: Callable[[], frozenset[str]],
        min_age_days: int = DEFAULT_MIN_AGE_DAYS,
    ) -> None:
        """Store the three readers and the age threshold that the report uses."""
        self._list_branches = list_branches  # Answers every branch name in the repository.
        self._read_branch = read_branch  # Answers one branch record, or None when unreadable.
        self._list_open_heads = list_open_heads  # Answers the head name of every open pull request.
        self._min_age_days = min_age_days  # The age below which the report stays quiet.

    def find(self, base_branch: str = DEFAULT_BASE_BRANCH) -> list[BranchRecord]:
        """Report every stranded branch, ordered from the oldest head first."""
        _LOG.info("Searching for a branch with no pull request")  # Report the plan before the work.
        open_heads = self._list_open_heads()  # Read the protection set one time, not per branch.
        now = datetime.now(UTC)  # Read the clock one time, so every age uses the same instant.
        stranded: list[BranchRecord] = []  # Collect the branches that fail every protection test.
        for name in self._list_branches():  # Test each branch in the repository.
            if name == base_branch:  # The base branch is never stranded against itself.
                continue
            record = self._read_branch(name)  # Build the record that the tests read.
            if record is None:  # An unreadable branch cannot support a deletion decision.
                continue
            if record.is_stranded(open_heads, self._min_age_days, now):  # Apply the three tests.
                stranded.append(record)  # Keep the branch for the report.
        stranded.sort(key=lambda item: item.last_commit_at)  # Report the oldest head first.
        _LOG.debug("Found %d stranded branches", len(stranded))  # Record the count after the search.
        return stranded

    def render(self, stranded: list[BranchRecord]) -> str:
        """Build the Markdown report that an operator or an issue body reads."""
        _LOG.info("Rendering the report for %d branches", len(stranded))  # Report before the build.
        if not stranded:  # A clean repository still needs a clear answer.
            return "Every branch with work above the base branch has an open pull request.\n"
        now = datetime.now(UTC)  # Read the clock one time, so every age column agrees.
        lines = [
            "The branches below hold commits above the base branch and have no open",
            "pull request. Open a pull request for each one before any cleanup, because",
            "`refs/pull/<n>/head` is the only reference that survives a branch deletion.",
            "",
            "| Branch | Commits ahead | Age in days |",
            "| - | - | - |",
        ]  # The header states the rule, so the reader needs no other page.
        for record in stranded:  # Add one row for each stranded branch.
            lines.append(f"| `{record.name}` | {record.ahead_by} | {record.age_days(now)} |")
        return "\n".join(lines) + "\n"  # A trailing newline keeps the Markdown well formed.


def _head_ref(row: dict[str, object]) -> str:
    """Read the head branch name of one pull request row."""
    head = row.get("head")  # The API nests the head reference inside one object.
    if not isinstance(head, dict):  # A row with no head object names no branch.
        return ""  # An empty name never matches a real branch.
    ref = head.get("ref")  # The short branch name lives under the `ref` key.
    return ref if isinstance(ref, str) else ""  # Only a string can match a branch name.


def _as_rows(body: object) -> Iterable[dict[str, object]]:
    """Read a JSON array of objects, and answer nothing for any other shape."""
    if not isinstance(body, list):  # A single object or an error body holds no rows.
        return []
    return [row for row in body if isinstance(row, dict)]  # Drop any element that is not an object.


def _head_date(commits: object) -> datetime:
    """Read the commit date of the newest commit in a compare response."""
    rows = list(_as_rows(commits))  # The compare response orders the commits oldest first.
    if not rows:  # A branch with no commit above the base has no head date to read.
        return datetime.now(UTC)  # A current date keeps the branch below every age threshold.
    raw = rows[-1].get("commit", {})  # The last row is the head of the branch.
    stamp = raw.get("committer", {}).get("date") if isinstance(raw, dict) else None
    if not isinstance(stamp, str):  # A missing date cannot support a deletion decision.
        return datetime.now(UTC)  # Treat the branch as new, so the report stays quiet.
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))  # The API answers RFC 3339.


def _build_parser() -> argparse.ArgumentParser:
    """Build the command line parser for the tool."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY, help="The owner and name pair to read.")
    parser.add_argument("--base-branch", default=DEFAULT_BASE_BRANCH, help="The branch every feature merges into.")
    parser.add_argument("--min-age-days", type=int, default=DEFAULT_MIN_AGE_DAYS, help="The quiet period in days.")
    parser.add_argument("--fail-on-find", action="store_true", help="Exit with status 1 when a branch is stranded.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Read the repository, print the report, and answer the exit status."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")  # One line per event.
    args = _build_parser().parse_args(argv)  # Read the command line before any network call.
    _LOG.info("Reporting the stranded branches of %s", args.repository)  # Report the plan.
    reader = GitHubReader(args.repository, args.base_branch)  # Bind the reader to one repository.
    reporter = StrandedBranchReporter(
        reader.list_branches, reader.read_branch, reader.list_open_pull_request_heads, args.min_age_days
    )
    stranded = reporter.find(args.base_branch)  # Apply the three protection tests to every branch.
    sys.stdout.write(reporter.render(stranded))  # Print the Markdown report for the caller.
    _LOG.debug("The report named %d branches", len(stranded))  # Record the count after the render.
    return 1 if stranded and args.fail_on_find else 0  # Only --fail-on-find turns a find into a failure.


if __name__ == "__main__":
    raise SystemExit(main())
