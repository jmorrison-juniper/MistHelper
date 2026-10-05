"""Restricted, allowlisted evidence. Never save screenshots or private values."""

import json  # Serialize only validated public audit records.
import logging  # Log output actions without report bodies.
import os  # Enforce owner-only artifact permissions.
import re  # Redact identifiers even when a future observation accidentally includes one.
import shlex  # Record the actual process command without unsafe shell interpretation.
import subprocess  # Record the selected source revision without network access.
import sys  # Obtain the exact interpreter invocation, not a fabricated validation command.
from pathlib import Path  # Restrict report destinations to the ignored audit directory.

logger = logging.getLogger(__name__)  # Keep artifacts out of log output.


class AuditReportWriter:
    """Separate isolated form evidence from blocked live stages."""

    _FIELDS = {
        "key",
        "status",
        "observations",
        "sdk_signature_verified",
        "cancel",
        "source",
        "reproduction",
        "selectors",
        "ux_review",
    }  # No arbitrary raw evidence.

    @classmethod
    def build(cls, inventory, records, duration_seconds=0, sdk_version=None):
        keys = [record.get("key") for record in records]  # Preserve the complete denominator.
        if not inventory or len(keys) != len(set(keys)) or set(keys) != set(inventory):
            raise ValueError("The report does not cover the complete nonempty inventory.")  # Never hide missing forms.
        if any(set(record) - cls._FIELDS for record in records):
            raise ValueError("The report contains prohibited evidence fields.")  # Reject credentials and screenshots.
        if any(record["status"] not in {"passed", "failed", "blocked", "skipped", "no-data"} for record in records):
            raise ValueError("The report contains an unknown status.")  # Do not widen pass semantics.
        totals = {
            status: sum(record["status"] == status for record in records)
            for status in ("passed", "failed", "blocked", "skipped", "no-data")
        }  # Separate outcomes.
        measured = sum(
            record["status"] in {"passed", "failed"} or "source" in record for record in records
        )  # Rendered forms can have blocked target selection.
        return {
            "inventory": inventory,
            "sdk_version": sdk_version,
            "isolated_inspection": {
                "measured_dialogs": measured,
                "totals": totals,
                "duration_seconds": round(duration_seconds, 3),
                "records": cls.redact(records),
            },
            "live_inspection": {
                "status": "blocked",
                "reason": "This isolated run did not execute live inspection. See the separate live report.",
            },
            "historical_capability": {
                "status": "blocked",
                "reason": "Initial planning: localhost:8055 was unreachable; the worktree environment was absent.",
            },  # Preserve historical evidence without presenting it as the current environment state.
            "live_subscription": {
                "status": "blocked",
                "reason": "This inspection run did not select the opt-in exact-key read-only lifecycle test.",
            },
        }  # Historical blocker, not a new probe.

    @classmethod
    def redact(cls, value):
        if isinstance(value, dict):
            return {key: cls.redact(item) for key, item in value.items()}  # Redact all nested observations.
        if isinstance(value, list):
            return [cls.redact(item) for item in value]  # Never serialize raw selector values.
        if not isinstance(value, str):
            return value  # Counts and booleans contain no private identifiers.
        value = re.sub(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b", "<identifier>", value)  # UUIDs.
        value = re.sub(
            r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b|\b(?:\d{1,3}\.){3}\d{1,3}\b", "<identifier>", value
        )  # MACs and IPv4.
        return re.sub(
            r"(?i)\b(token|password|authorization|secret)\s*[:=]\s*\S+", r"\1=<redacted>", value
        )  # Secret-like assignments.

    @staticmethod
    def write(report, destination):
        root = Path(__file__).resolve().parents[5]  # Bind artifacts to this checkout only.
        expected = root / "test-artifacts" / "websocket-dialog-audit"  # Existing ignore policy covers this directory.
        path = Path(destination).absolute()  # Do not accept arbitrary public or external paths.
        if (
            path != expected
            or path.resolve() != expected
            or any(parent.is_symlink() for parent in (path, *path.parents))
        ):
            raise ValueError(
                "Use the restricted worktree test-artifacts/websocket-dialog-audit directory."
            )  # Reject traversal and symlinks.
        logger.info("Writing restricted audit reports")  # Log before filesystem actions.
        path.mkdir(parents=True, exist_ok=True, mode=0o700)  # Artifacts are owner-only.
        path.chmod(0o700)  # Tighten an existing directory before creating files.
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True
        ).stdout.strip()  # Local revision.
        command = shlex.join(sys.orig_argv)  # Record the actual Python invocation and selected tests.
        command = re.sub(
            r"--ws-audit-base-url(?:=|\s+)\S+", "--ws-audit-base-url=<authorized-origin>", command
        )  # Never save a real origin.
        report = {
            **report,
            "source_revision": revision,
            "command": AuditReportWriter.redact(command),
        }  # Sanitized execution evidence.
        summary = (
            "# WebSocket dialog audit\n\nIsolated measured dialogs: "
            + str(report["isolated_inspection"]["measured_dialogs"])
            + "\nLive measured dialogs: "
            + str(report["live_inspection"].get("measured_dialogs", 0))
            + "\nLive inspection status: "
            + report["live_inspection"]["status"]
            + "\nLive subscription: "
            + report["live_subscription"]["status"]
            + "\n"
            + (
                "Only the reviewed site.stats.devices observation lifecycle was selected.\n"
                if report["live_subscription"].get("key")
                else "No operation was started.\n"
            )
        )  # Never mix isolated and live evidence.
        prefix = (
            "subscription-report"
            if report["live_subscription"].get("key")
            else "live-report" if "measured_dialogs" in report["live_inspection"] else "report"
        )  # Preserve isolated and all-form live evidence.
        for name, text in ((prefix + ".json", json.dumps(report, indent=2)), (prefix + ".md", summary)):
            descriptor = os.open(
                path / name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600
            )  # Refuse final symlink.
            with os.fdopen(descriptor, "w") as output:
                os.fchmod(output.fileno(), 0o600)  # Tighten an existing report before writing.
                output.write(text)  # Save only bounded audit fields.
        logger.debug("Wrote restricted JSON and Markdown reports")  # Do not publish artifacts.
