"""Build the report rows of a run from the results of its targets.

Why:
    The CLI and the portal finish step both hold the same input: one result for
    each attempted switch. This module turns those results into uniform rows. A
    switch that collected gives one row for each hardware item. A switch that did
    not collect gives one outcome row, so the report never hides a missing switch.
"""

from __future__ import annotations

import logging  # Record each add and each build for the operator trace.
from collections.abc import Mapping  # Accept the batch identity as a read-only mapping.
from dataclasses import dataclass  # Keep one target result immutable.

from src.operations.exporting.ex_hardware_inventory.report.columns import CellGuard, ReportColumns  # Column rules.
from src.operations.exporting.ex_hardware_inventory.report.flatten import (
    FlattenError,
    HardwareXmlFlattener,
)  # Read the hardware items of one reply.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


@dataclass(frozen=True)
class TargetResult:
    """The outcome of one target, as the report compiler reads it.

    Attributes:
        identity: The batch identity of the target (org_id, site_id, site_label, device_id, label).
        org_name: The organization name from the scope decision.
        state: The batch state: completed, failed, skipped, or stopped.
        reason: The batch reason code, or an empty string.
        xml_text: The saved reply text for a completed target, or None.
    """

    identity: Mapping[str, object]  # The same identity that the batch records for the target.
    org_name: str  # The batch identity holds the organization identifier only.
    state: str  # The batch state of the target.
    reason: str  # The batch reason code, kept as given.
    xml_text: str | None  # Present only when the target saved a reply.


class RowFactory:
    """Build the rows of one target."""

    DETAILS = {
        "cancelled": "The run was cancelled before this switch finished.",
        "offline": "The switch was offline when its turn came.",
        "unknown_status": "Mist reported no status for the switch when its turn came.",
        "completion_unproven": "The shell did not show a stable prompt.",
        "format_failed": "The reply was not a valid chassis inventory.",
        "target_failed": "The shell could not collect this switch.",
        "output_failed": "The reply could not be saved.",
        "new_targets": "New switches appeared after the confirmation, so this organization was not run.",
        "no_longer_connected": "The switch was no longer connected when the run started.",
        "discovery_failed": "Mist could not list the switches of this organization.",
        "rate_limited": "Mist limited the requests, so this organization was not read.",
        "target_limit": "This organization has more switches than one batch can run.",
    }  # A plain sentence for each reason code. An operator never sees a code.

    @classmethod
    def base(cls, result: TargetResult, scope: str, run_utc: str) -> dict[str, str]:
        """Return the columns that every row of one target shares."""
        identity = result.identity  # Read the batch identity once.
        return {
            "report_run_utc": run_utc,
            "scope": scope,
            "org_id": str(identity.get("org_id") or ""),
            "org_name": result.org_name,
            "site_id": str(identity.get("site_id") or ""),
            "site_name": str(identity.get("site_label") or ""),
            "device_id": str(identity.get("device_id") or identity.get("target_id") or ""),
            "device_name": str(identity.get("label") or ""),
        }  # The identity columns of the contract.

    @classmethod
    def outcome(cls, base: dict[str, str], status: str, detail: str) -> dict[str, str]:
        """Return the one outcome row of a switch that returned no valid reply."""
        return base | {
            "record_type": "device_outcome",
            "collection_status": status,
            "collection_detail": detail,
        }  # The item columns stay empty because the builder fills every missing column.

    @classmethod
    def items(cls, base: dict[str, str], xml_text: str) -> tuple[list[dict[str, str]], set[str]]:
        """Return one row for each hardware item, and the set of field names that the reply returned.

        Raises:
            FlattenError: When the saved reply cannot be read.
        """
        device = HardwareXmlFlattener.flatten(xml_text)  # Read every item of the reply.
        rows: list[dict[str, str]] = []  # One row for each item in document order.
        names: set[str] = set()  # The union of field names, for the column list.
        for item in device.items:  # Visit each item.
            row = base | {
                "record_type": "hardware_item",
                "collection_status": "collected",
                "collection_detail": "",
                "device_cli_banner": device.cli_banner,
                "item_level": str(item.level),
                "item_path": item.path,
                "item_type": item.item_type,
            }  # The fixed columns of an item row.
            row.update({ReportColumns.column_for(name): value for name, value in item.fields.items()})  # Fields.
            rows.append(row)  # Keep the row.
            names.update(item.fields)  # Remember each field name.
        return rows, names  # The rows and the names.

    @classmethod
    def build(cls, result: TargetResult, scope: str, run_utc: str) -> tuple[str, list[dict[str, str]], set[str]]:
        """Return the report status, the rows, and the field names for one target."""
        base = cls.base(result, scope, run_utc)  # The shared identity columns.
        if result.state == "completed" and result.xml_text is None:  # A completed target must have saved a reply.
            return "failed", [cls.outcome(base, "failed", "The reply file is missing.")], set()  # Not collected.
        if result.state == "completed" and result.xml_text is not None:  # The normal collected case.
            try:  # A saved reply can still be unreadable.
                rows, names = cls.items(base, result.xml_text)  # One row for each hardware item.
                return "collected", rows, names  # The device collected.
            except FlattenError:  # The file is truncated, malformed, or not a chassis reply.
                return (
                    "failed",
                    [cls.outcome(base, "failed", "The saved reply could not be read.")],
                    set(),
                )  # Not collected.
        status = {"skipped": "skipped", "stopped": "cancelled"}.get(result.state, "failed")  # Map the batch state.
        detail = cls.DETAILS.get(result.reason, "The switch returned no valid reply.")  # A plain sentence.
        return status, [cls.outcome(base, status, detail)], set()  # One outcome row.


class ReportBuilder:
    """Collect target results and return uniform, ordered, guarded rows."""

    def __init__(self, scope: str, run_utc: str) -> None:
        """Start an empty report.

        Args:
            scope: ``organization`` or ``msp``.
            run_utc: The run start in UTC, ISO 8601 form, the same on every row.
        """
        self._scope = scope  # Every row repeats the scope.
        self._run_utc = run_utc  # Every row repeats the run time.
        self._fields: set[str] = set()  # The union of item field names.
        self._statuses: list[str] = []  # One report status for each target.
        self._devices: list[tuple[tuple[str, str, str, int], list[dict[str, str]]]] = []  # Sort key and rows.

    def add(self, result: TargetResult) -> None:
        """Add the result of one target.

        Args:
            result: The outcome and the saved reply of one target.
        """
        logger.info("Adding one target result with state %s", result.state)  # Log before the transform.
        status, rows, names = RowFactory.build(result, self._scope, self._run_utc)  # Build this target's rows.
        first = rows[0]  # Every target gives at least one row.
        key = (
            first["org_name"].casefold(),
            first["site_name"].casefold(),
            first["device_name"].casefold(),
        )  # The sort key of the device.
        self._devices.append(((*key, len(self._devices)), rows))  # The count keeps equal keys in input order.
        self._statuses.append(status)  # Remember the status for the summary.
        self._fields |= names  # Remember the field names for the column list.
        logger.debug("Added %d rows with status %s", len(rows), status)  # Log the result size.

    def fieldnames(self) -> list[str]:
        """Return the full column list for the rows added so far."""
        return ReportColumns.fieldnames(self._fields)  # The fixed part and the sorted item part.

    def rows(self) -> list[dict[str, str]]:
        """Return every row, ordered and guarded, with every column present."""
        names = self.fieldnames()  # One column list for all rows.
        ordered = sorted(self._devices, key=lambda entry: entry[0])  # Organization, site, device, input order.
        result: list[dict[str, str]] = []  # The final rows.
        for _, rows in ordered:  # Visit each device in order.
            for raw in rows:  # Visit each row of the device in reply order.
                result.append(
                    {
                        name: raw.get(name, "") if name in CellGuard.EXEMPT else CellGuard.clean(raw.get(name, ""))
                        for name in names
                    }
                )  # Fill missing columns and neutralize formula text.
        return result  # Hand back the finished rows.

    def counts(self) -> dict[str, int]:
        """Return how many targets ended in each status."""
        counts = {"collected": 0, "failed": 0, "skipped": 0, "cancelled": 0}  # All four keys always exist.
        for status in self._statuses:  # Count each target once.
            counts[status] += 1  # The status is one of the four keys.
        return counts  # Hand back the tally.
