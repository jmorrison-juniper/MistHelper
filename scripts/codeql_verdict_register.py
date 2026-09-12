"""Build and check the CodeQL verdict register.

The register is the audit record for every dismissed CodeQL alert. A dismissal
accepts a security risk, so the register states who accepted the risk, when they
accepted it, and why.

The tool has two modes. The `generate` mode writes the register from the live
GitHub code scanning API. The `check` mode compares the register against the same
API and reports every difference. The `check` mode is the reconciliation that
clause C-8 of the superseded contract describes.

Run the tool from the repository root.

    python scripts/codeql_verdict_register.py generate
    python scripts/codeql_verdict_register.py check
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

# The rule that the register governs. The register covers one rule at a time.
DEFAULT_RULE_ID = "py/clear-text-logging-sensitive-data"

# The register path. The record lives outside a feature folder, because the
# record outlives the feature that created it.
DEFAULT_REGISTER_PATH = Path("documentation") / "security" / "codeql-verdict-register.md"

# The number of days between a dismissal and the review that the register forces.
REVIEW_INTERVAL_DAYS = 180

# The gh call reaches the GitHub API over the network. A stalled read has no
# bound of its own, so this cap stops it from hanging the whole gate.
_GH_TIMEOUT_SECONDS = 120

# The map from an API dismissal reason to a register verdict. The API accepts
# three reasons, so the register holds one verdict for each reason.
API_REASON_TO_VERDICT = {
    "false positive": "false_positive",
    "won't fix": "accepted_with_rationale",
    "used in tests": "test_fixture",
}

# The text that a row carries when the dismissal recorded no reason. The cell is
# never blank, because a blank cell hides the gap instead of reporting it.
MISSING_REASON_TEXT = "Warning: the dismissal recorded no reason. A reviewer must write one."

# The trigger that a row carries when the dismissal recorded no reason.
MISSING_REASON_TRIGGER = "A reviewer writes the missing reason."

# The trigger that a row carries when the dismissal recorded a reason.
DEFAULT_TRIGGER = "A later CodeQL scan raises the same alert again."

# The eleven column names. Clause C-1 fixes the order, so a move breaks a
# plain text comparison between two revisions.
COLUMNS = (
    "Alert",
    "Issue",
    "File",
    "Line",
    "Anchor",
    "Verdict",
    "Reason",
    "Author",
    "Decided",
    "Review",
    "Trigger",
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VerdictRow:
    """One register row. The row records one accepted security risk."""

    alert: int
    issue: str
    file: str
    line: str
    anchor: str
    verdict: str
    reason: str
    author: str
    decided: str
    review: str
    trigger: str

    def to_markdown(self) -> str:
        """Return the row as one markdown table line."""
        # Collect the cells in the fixed column order that clause C-1 states.
        cells = [
            str(self.alert),
            self.issue,
            self.file,
            self.line,
            self.anchor,
            self.verdict,
            self.reason,
            self.author,
            self.decided,
            self.review,
            self.trigger,
        ]
        # Escape a pipe inside a cell, because a raw pipe ends the cell early.
        safe = [cell.replace("|", "\\|") for cell in cells]
        # Join the cells into the markdown row format.
        return "| " + " | ".join(safe) + " |"


class AlertSource:
    """Read dismissed CodeQL alerts from the GitHub code scanning API."""

    def __init__(self, repository: str, rule_id: str = DEFAULT_RULE_ID) -> None:
        # Store the repository in owner/name form for the API path.
        self.repository = repository
        # Store the rule, because the register covers one rule at a time.
        self.rule_id = rule_id

    def fetch(self) -> list[dict]:
        """Return every dismissed alert that matches the rule."""
        # Build the paginated API path for the dismissed alerts.
        path = f"repos/{self.repository}/code-scanning/alerts?state=dismissed&per_page=100"
        logger.info("Reading dismissed CodeQL alerts for rule %s", self.rule_id)
        # Call the GitHub CLI, because it carries the credentials the user holds.
        try:
            raw = subprocess.run(
                ["gh", "api", "--paginate", path],
                capture_output=True,
                text=True,
                check=True,
                timeout=_GH_TIMEOUT_SECONDS,  # A stalled network read must not hang the gate.
            ).stdout
        except subprocess.TimeoutExpired:
            # Name the bound, so the operator can tell a stall from a crash.
            logger.error("The gh api call passed the %ds bound and was stopped", _GH_TIMEOUT_SECONDS)
            msg = f"The GitHub API read passed the {_GH_TIMEOUT_SECONDS}s bound"
            raise RuntimeError(msg) from None  # Fail loudly instead of returning an empty register.
        # Parse the response into Python objects.
        alerts = json.loads(raw)
        # Keep only the alerts that the register governs.
        matched = [item for item in alerts if item.get("rule", {}).get("id") == self.rule_id]
        logger.debug("Read %d dismissed alerts and matched %d", len(alerts), len(matched))
        return matched


class RowBuilder:
    """Turn one API alert into one register row."""

    def build(self, alert: dict) -> VerdictRow:
        """Return the register row for one dismissed alert."""
        # Read the code location, because the row names the file and the line.
        location = alert.get("most_recent_instance", {}).get("location", {})
        # Read the file path and fall back to a clear marker when it is absent.
        file_path = location.get("path", "unknown")
        # Read the start line and fall back to a clear marker when it is absent.
        line = str(location.get("start_line", "-"))
        # Read the dismissal reason that the API recorded.
        api_reason = alert.get("dismissed_reason") or ""
        # Map the API reason onto the register verdict vocabulary.
        verdict = API_REASON_TO_VERDICT.get(api_reason, "accepted_with_rationale")
        # Read the dismissal comment and strip the surrounding blank space.
        comment = (alert.get("dismissed_comment") or "").strip()
        # Replace a blank comment with the warning, because C-4 forbids a blank cell.
        reason = self._flatten(comment) if comment else MISSING_REASON_TEXT
        # Read the account that accepted the risk.
        author = (alert.get("dismissed_by") or {}).get("login", "unknown")
        # Read the dismissal timestamp and reduce it to an ISO date.
        decided = self._to_date(alert.get("dismissed_at"))
        return VerdictRow(
            alert=int(alert.get("number", 0)),
            issue=self._issue_for(comment),
            file=file_path,
            line=line,
            anchor=f"{file_path}::L{line}",
            verdict=verdict,
            reason=reason,
            author=author,
            decided=decided,
            review=self._review_date(decided),
            trigger=DEFAULT_TRIGGER if comment else MISSING_REASON_TRIGGER,
        )

    def _flatten(self, text: str) -> str:
        """Return the comment as one line, because a table cell holds one line."""
        # Replace every line break with a space so the markdown table stays valid.
        return " ".join(text.split())

    def _issue_for(self, comment: str) -> str:
        """Return the issue reference that the comment names, or a dash."""
        # Look for a hash reference, because a dismissal often names its issue.
        for token in comment.replace("(", " ").replace(")", " ").split():
            # Accept a token that starts with a hash and holds digits after it.
            if token.startswith("#") and token[1:].rstrip(".,").isdigit():
                return "#" + token[1:].rstrip(".,")
        return "-"

    def _to_date(self, stamp: str | None) -> str:
        """Return the ISO date part of an API timestamp."""
        # Report a dash when the API recorded no timestamp.
        if not stamp:
            return "-"
        # Keep the first ten characters, because they hold the ISO date.
        return stamp[:10]

    def _review_date(self, decided: str) -> str:
        """Return the date when a reviewer must revisit the accepted risk."""
        # Report a dash when the decision carries no date to count from.
        if decided == "-":
            return "-"
        # Parse the decision date so the tool can add the review interval.
        start = datetime.strptime(decided, "%Y-%m-%d").replace(tzinfo=UTC)
        # Add the interval and format the result as an ISO date.
        return (start + timedelta(days=REVIEW_INTERVAL_DAYS)).strftime("%Y-%m-%d")


class RegisterWriter:
    """Write the register file."""

    def __init__(self, path: Path, rule_id: str = DEFAULT_RULE_ID) -> None:
        # Store the target path for the register file.
        self.path = path
        # Store the rule so the header states what the register governs.
        self.rule_id = rule_id

    def write(self, rows: list[VerdictRow]) -> None:
        """Write the header, the table, and the summary to the register file."""
        logger.info("Writing %d register rows to %s", len(rows), self.path)
        # Create the parent directory, because the security folder may be new.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Sort the rows by alert number so a difference stays readable.
        ordered = sorted(rows, key=lambda row: row.alert)
        # Join the document parts into the final text.
        text = "\n".join([self._header(ordered), self._table(ordered), self._summary(ordered)])
        # Write the file with an explicit encoding for Windows and Linux.
        self.path.write_text(text, encoding="utf-8")
        logger.debug("Wrote the register file with %d characters", len(text))

    def _header(self, rows: list[VerdictRow]) -> str:
        """Return the register header text."""
        # Record the generation date so a reader knows how fresh the record is.
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        return (
            "# CodeQL verdict register\n\n"
            f"**Rule**: `{self.rule_id}`\n\n"
            "**Owner**: The repository security reviewer.\n\n"
            f"**Generated**: {today}\n\n"
            f"**Rows**: {len(rows)}\n\n"
            "A dismissed CodeQL alert is a decision to accept a security risk. This register\n"
            "records that decision. Each row names the alert, the code location, the verdict,\n"
            "the reason, the account that decided, and the date of the next review.\n\n"
            "Do not edit this file by hand. The tool `scripts/codeql_verdict_register.py`\n"
            "writes it from the GitHub code scanning API.\n\n"
            "Refresh the register with the command below.\n\n"
            "```bash\n"
            "python scripts/codeql_verdict_register.py generate\n"
            "```\n\n"
            "Check the register against the API with the command below. The command exits\n"
            "with a non-zero status when a row and an alert disagree.\n\n"
            "```bash\n"
            "python scripts/codeql_verdict_register.py check\n"
            "```\n\n"
            "The `Anchor` column holds the file path and the line of the reported expression.\n"
            "A row with the reason `Warning: the dismissal recorded no reason` needs a written\n"
            "reason. Add the reason to the alert on GitHub, then run `generate` again.\n"
        )

    def _table(self, rows: list[VerdictRow]) -> str:
        """Return the markdown table for the rows."""
        # Build the header row from the fixed column order.
        head = "| " + " | ".join(COLUMNS) + " |"
        # Build the separator row that markdown requires under the header.
        rule = "| " + " | ".join("-" for _ in COLUMNS) + " |"
        # Build one line for each row.
        body = [row.to_markdown() for row in rows]
        return "\n".join(["\n## Register", "", head, rule, *body, ""])

    def _summary(self, rows: list[VerdictRow]) -> str:
        """Return the counts that a reviewer checks first."""
        # Count the rows for each verdict so a reader sees the risk shape.
        counts: dict[str, int] = {}
        for row in rows:
            counts[row.verdict] = counts.get(row.verdict, 0) + 1
        # Count the rows that still need a written reason.
        missing = sum(1 for row in rows if row.reason == MISSING_REASON_TEXT)
        # Build one table line for each verdict.
        lines = [f"| {name} | {count} |" for name, count in sorted(counts.items())]
        return "\n".join(
            [
                "\n## Summary",
                "",
                "| Verdict | Rows |",
                "| - | - |",
                *lines,
                f"| **Total** | {len(rows)} |",
                "",
                f"Rows that still need a written reason: {missing}.",
                "",
            ]
        )


class RegisterReconciler:
    """Compare the register against the live alert data."""

    def __init__(self, path: Path) -> None:
        # Store the register path that the check reads.
        self.path = path

    def parse(self) -> dict[int, str]:
        """Return the verdict of each alert number that the register records."""
        # Report an empty record when the register file is absent.
        if not self.path.exists():
            logger.warning("The register file %s does not exist", self.path)
            return {}
        found: dict[int, str] = {}
        # Read each line and keep the table rows that start with an alert number.
        for line in self.path.read_text(encoding="utf-8").splitlines():
            # Hide an escaped pipe, because a raw split would cut the cell in two.
            masked = line.replace("\\|", "\x00")
            # Split the markdown row into its cells.
            cells = [cell.strip().replace("\x00", "|") for cell in masked.strip().strip("|").split("|")]
            # Skip a line that does not hold the eleven columns.
            if len(cells) != len(COLUMNS) or not cells[0].isdigit():
                continue
            # Record the alert number and the verdict for the comparison.
            found[int(cells[0])] = cells[5]
        logger.debug("Parsed %d rows from the register", len(found))
        return found

    def compare(self, rows: list[VerdictRow]) -> list[str]:
        """Return one message for each difference between the register and the API."""
        # Read the register rows that the file records.
        recorded = self.parse()
        # Build the live view from the API rows.
        live = {row.alert: row.verdict for row in rows}
        problems: list[str] = []
        # Report every alert that the API dismisses and the register misses.
        for number in sorted(set(live) - set(recorded)):
            problems.append(f"Alert {number} is dismissed and the register holds no row.")
        # Report every register row that no dismissed alert supports.
        for number in sorted(set(recorded) - set(live)):
            problems.append(f"The register holds row {number} and no dismissed alert matches it.")
        # Report every row whose verdict disagrees with the API reason.
        for number in sorted(set(recorded) & set(live)):
            if recorded[number] != live[number]:
                problems.append(
                    f"Alert {number} records the verdict {live[number]} " f"and the register reads {recorded[number]}."
                )
        return problems


class RegisterConsole:
    """Run the tool from the command line."""

    def __init__(self, repository: str, path: Path, rule_id: str) -> None:
        # Build the alert source for the repository and the rule.
        self.source = AlertSource(repository, rule_id)
        # Build the row builder that maps an alert onto a register row.
        self.builder = RowBuilder()
        # Store the register path for the writer and the reconciler.
        self.path = path
        # Store the rule so the writer states it in the header.
        self.rule_id = rule_id

    def generate(self) -> int:
        """Write the register and report the row count."""
        logger.info("Starting the register generation")
        # Build one row for each dismissed alert.
        rows = [self.builder.build(alert) for alert in self.source.fetch()]
        # Write the register file.
        RegisterWriter(self.path, self.rule_id).write(rows)
        print(f"Wrote {len(rows)} rows to {self.path}")
        logger.debug("Finished the register generation with %d rows", len(rows))
        return 0

    def check(self) -> int:
        """Compare the register against the API and report every difference."""
        logger.info("Starting the register reconciliation")
        # Build the live rows from the API.
        rows = [self.builder.build(alert) for alert in self.source.fetch()]
        # Compare the live rows against the recorded rows.
        problems = RegisterReconciler(self.path).compare(rows)
        # Report success when the register and the API agree.
        if not problems:
            print(f"The register matches all {len(rows)} dismissed alerts.")
            return 0
        # Report each difference on its own line for a readable log.
        for problem in problems:
            print(problem)
        print(f"The reconciliation found {len(problems)} differences.")
        logger.debug("Finished the reconciliation with %d differences", len(problems))
        return 1


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and run the selected mode."""
    # Configure logging before any action, so every step reaches the log.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Build and check the CodeQL verdict register.")
    # Accept the mode as the single positional argument.
    parser.add_argument("mode", choices=("generate", "check"))
    # Accept a repository override for a fork or a test run.
    parser.add_argument("--repository", default="jmorrison-juniper/MistHelper")
    # Accept a register path override for a test run.
    parser.add_argument("--path", type=Path, default=DEFAULT_REGISTER_PATH)
    # Accept a rule override, because the tool can govern another rule later.
    parser.add_argument("--rule-id", default=DEFAULT_RULE_ID)
    args = parser.parse_args(argv)
    # Build the console for the selected repository, path, and rule.
    console = RegisterConsole(args.repository, args.path, args.rule_id)
    # Run the selected mode and return its exit status.
    return console.generate() if args.mode == "generate" else console.check()


if __name__ == "__main__":
    sys.exit(main())
