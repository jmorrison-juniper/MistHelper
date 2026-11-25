"""Compile the combined CSV report of a portal hardware run from its saved replies.

Why:
    The Multi Site action saves one XML reply for each connected switch and ends
    with a manifest. The CSV output needs one more file at the end of the run. The
    run finish step of the artifact service owns the run folder and its quota, so
    this module takes only what it needs: a function that reads one saved reply,
    and the scope of the run. It returns the bytes of the report, and the artifact
    service decides where to publish them. That keeps the report code free of any
    portal storage detail, and the portal code free of any report detail.
"""

from __future__ import annotations

import logging  # Record each compile for the operator trace.
from collections.abc import Callable, Mapping, Sequence  # The outcomes and the scope are read-only mappings.
from datetime import UTC, datetime  # The report carries the run end time in UTC.

from src.operations.exporting.ex_hardware_inventory.report.builder import ReportBuilder, TargetResult  # Report rows.
from src.operations.exporting.ex_hardware_inventory.report.csv_file import CsvRenderer, CsvVerifier  # The file.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


class ReportHook:
    """Turn the final outcomes of a hardware run into the bytes of the combined CSV."""

    def __init__(self, read_reply: Callable[[str], str], scope: Mapping[str, object] | None = None) -> None:
        """Store the reply reader and the scope.

        Args:
            read_reply: Returns the saved XML text for one recorded file name. It raises OSError,
                UnicodeDecodeError, or ValueError when the file is missing or unsafe to read.
            scope: ``mode`` (organization or msp), ``organizations`` (identifier to name), and ``failed``
                (identifier to reason code of an organization that could not be read). None means
                organization scope with no name.
        """
        self._read_reply = read_reply  # The artifact service checks each path before it reads.
        self._scope: Mapping[str, object] = scope or {}  # An absent scope is an organization run.

    def compile(self, outcomes: Sequence[Mapping[str, object]], limit_bytes: int) -> bytes:
        """Build the CSV bytes.

        Args:
            outcomes: The final target outcomes of the run: target identity, state, reason code, and files.
            limit_bytes: The most bytes that the file may hold.

        Returns:
            The bytes of the report.

        Raises:
            ReportTooLarge: When the file would pass the limit.
            ReportCheckError: When the rendered bytes do not match the rows.
        """
        logger.info("Compiling the combined CSV of %d outcomes", len(outcomes))  # Log before the transform.
        builder = ReportBuilder(
            str(self._scope.get("mode") or "organization"), datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        for result in (*self._results(outcomes), *self._failed()):  # Switches first, then unread organizations.
            builder.add(result)  # One or more rows for each result.
        rows, names = builder.rows(), builder.fieldnames()  # Ordered, guarded rows with every column present.
        data = CsvRenderer.render(rows, names, limit_bytes)  # Refuses a report over the limit.
        CsvVerifier.verify(data, names, len(rows))  # A rendered report must read back as the same rows.
        logger.debug("Compiled the combined CSV with %d rows and %d bytes", len(rows), len(data))  # Log the size.
        return data  # The artifact service publishes it.

    def _results(self, outcomes: Sequence[Mapping[str, object]]) -> list[TargetResult]:
        """Build one result for each target outcome."""
        organizations = self._scope.get("organizations")  # Identifier to name.
        names = organizations if isinstance(organizations, Mapping) else {}  # A bad shape gives no name.
        results: list[TargetResult] = []  # One for each target, in manifest order.
        for outcome in outcomes:  # Each outcome is one attempted target.
            identity = outcome.get("target")  # The redacted identity of the target.
            identity = identity if isinstance(identity, Mapping) else {}  # A bad shape gives an empty identity.
            org_id = str(identity.get("org_id") or "")  # The report names the organization of the target.
            state, reason = str(outcome.get("state") or "failed"), str(outcome.get("reason_code") or "")
            xml_text = self._reply(outcome) if state == "completed" else None  # Only a collected target has a reply.
            results.append(TargetResult(identity, str(names.get(org_id) or org_id), state, reason, xml_text))
        return results

    def _failed(self) -> list[TargetResult]:
        """Build one failed result for each organization that could not be read."""
        failed = self._scope.get("failed")  # Identifier to reason code.
        organizations = self._scope.get("organizations")  # Identifier to name.
        names = organizations if isinstance(organizations, Mapping) else {}  # A bad shape gives no name.
        pairs = failed.items() if isinstance(failed, Mapping) else ()  # A bad shape gives no failure.
        return [
            TargetResult({"org_id": str(org_id)}, str(names.get(org_id) or org_id), "failed", str(reason), None)
            for org_id, reason in pairs
        ]  # One outcome row for each unread organization.

    def _reply(self, outcome: Mapping[str, object]) -> str | None:
        """Read the saved XML reply of one outcome, or None when it is missing or unreadable."""
        files = outcome.get("files")  # The relative names that the run recorded.
        name = next((str(item) for item in files if str(item).endswith(".xml")), "") if isinstance(files, list) else ""
        if not name:  # Nothing was saved for this target.
            return None  # The report says that the reply is missing.
        try:  # A missing or unsafe file is not a failure of the whole report.
            return self._read_reply(name)  # The artifact service checks the path and the size.
        except (OSError, UnicodeDecodeError, ValueError):  # The file is gone, is not UTF-8, or is not safe.
            logger.warning("A saved reply could not be read for the combined CSV")  # Log without the name.
            return None  # The report says that the reply is missing.
