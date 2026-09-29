"""Pure models for the Mist Edge lifecycle operation.

Why:
    The menu operation is destructive. These models build the exact request
    bodies and redacted evidence rows before any API request can be sent.
"""

from __future__ import annotations  # WHY: allow concise type syntax on Python 3.13.

from dataclasses import dataclass  # WHY: immutable data bundles keep step data explicit.
from datetime import UTC, datetime  # WHY: CSV evidence uses one UTC time base.
from typing import Any, ClassVar  # WHY: Mist responses contain dynamic JSON values.

STEP_CLAIM = "claim"  # WHY: stable step key for logs and tests.
STEP_ASSIGN = "assign"  # WHY: stable step key for logs and tests.
STEP_UNASSIGN = "unassign"  # WHY: stable step key for logs and tests.
STEP_BOUNCE = "bounce"  # WHY: stable step key for logs and tests.
STEP_UPGRADE = "upgrade"  # WHY: stable step key for logs and tests.

STATUS_CANCELLED = "cancelled"  # WHY: evidence row when confirmation fails.
STATUS_DRY_RUN = "dry_run"  # WHY: evidence row when no request is sent.
STATUS_ERROR = "error"  # WHY: evidence row when an API call fails.
STATUS_SENT = "sent"  # WHY: evidence row when Mist accepts a request.
STATUS_TIMEOUT = "timeout"  # WHY: evidence row when polling reaches the timeout.

REDACTED_VALUE = "REDACTED"  # WHY: claim codes must not reach logs or CSV output.
TERMINAL_STATUSES = frozenset(  # WHY: terminal words stop the upgrade poll loop.
    {"complete", "completed", "success", "succeeded", "failed", "error", "canceled", "cancelled"}
)
CSV_FIELDNAMES = (  # WHY: a fixed schema lets operators compare runs.
    "timestamp_utc",
    "org_id",
    "step",
    "target",
    "dry_run",
    "status",
    "detail",
)


@dataclass(frozen=True)
class LifecycleRequest:
    """One validated lifecycle request.

    Why:
        The operation asks for confirmation after this object exists, so tests
        can prove the body shape before a client sends it.
    """

    step: str  # WHY: identify the action in the CSV row.
    confirmation_word: str  # WHY: destructive actions need an exact typed word.
    body: dict[str, Any]  # WHY: this payload goes to the Mist API after confirmation.
    target_summary: str  # WHY: this redacted text is safe for logs and CSV rows.
    dry_run: bool = False  # WHY: dry-run sends no request.

    def as_row(self, org_id: str, status: str, detail: str) -> dict[str, object]:
        """Return a redacted CSV row for this request."""
        return {  # WHY: one dictionary maps directly to DictWriter.
            "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),  # WHY: record run time.
            "org_id": org_id,  # WHY: show which organization was targeted.
            "step": self.step,  # WHY: show which lifecycle step ran.
            "target": self.target_summary,  # WHY: keep claim codes out of evidence.
            "dry_run": self.dry_run,  # WHY: distinguish preview rows from live requests.
            "status": status,  # WHY: show the outcome in one column.
            "detail": detail,  # WHY: preserve a short redacted result.
        }


class MxEdgeLifecycleModels:
    """Build OpenAPI-shaped Mist Edge lifecycle requests.

    Why:
        Pure builders let contract tests validate body shape without a session.
    """

    DEFAULT_STRATEGY: ClassVar[str] = "serial"  # WHY: serial is safest for lifecycle maintenance.

    @staticmethod
    def claim(claim_code: str, dry_run: bool = False) -> LifecycleRequest:
        """Build a claim request with a redacted target summary."""
        body = {"code": claim_code}  # WHY: OpenAPI `code_string` requires `code`.
        return LifecycleRequest(STEP_CLAIM, "CLAIM", body, REDACTED_VALUE, dry_run)  # WHY: hide claim code.

    @staticmethod
    def assign(mxedge_ids: list[str], site_id: str, dry_run: bool = False) -> LifecycleRequest:
        """Build an assign-to-site request."""
        checked_ids = MxEdgeLifecycleModels._require_ids(mxedge_ids, "mxedge_ids")  # WHY: API needs targets.
        body = {"mxedge_ids": checked_ids, "site_id": site_id}  # WHY: OpenAPI `mxedges_assign` shape.
        target = f"mxedges={','.join(checked_ids)} site={site_id}"  # WHY: describe the target safely.
        return LifecycleRequest(STEP_ASSIGN, "ASSIGN", body, target, dry_run)  # WHY: operation uses this guard.

    @staticmethod
    def unassign(mxedge_ids: list[str], dry_run: bool = False) -> LifecycleRequest:
        """Build an unassign-from-site request."""
        checked_ids = MxEdgeLifecycleModels._require_ids(mxedge_ids, "mxedge_ids")  # WHY: API needs targets.
        body = {"mxedge_ids": checked_ids}  # WHY: OpenAPI `mxedges_unassign` shape.
        target = f"mxedges={','.join(checked_ids)}"  # WHY: describe targets without secrets.
        return LifecycleRequest(STEP_UNASSIGN, "UNASSIGN", body, target, dry_run)  # WHY: operation uses this guard.

    @staticmethod
    def bounce(mxedge_id: str, ports: list[str], dry_run: bool = False) -> LifecycleRequest:
        """Build a data-port bounce request."""
        checked_ports = MxEdgeLifecycleModels._require_ids(ports, "ports")  # WHY: empty bounce is unsafe.
        body = {"ports": checked_ports}  # WHY: OpenAPI `utils_tunterm_bounce_port` shape.
        target = f"mxedge={mxedge_id} ports={','.join(checked_ports)}"  # WHY: help the operator audit the bounce.
        return LifecycleRequest(STEP_BOUNCE, "BOUNCE", body, target, dry_run)  # WHY: operation uses this guard.

    @staticmethod
    def upgrade(mxedge_ids: list[str], version: str, dry_run: bool = False) -> LifecycleRequest:
        """Build a Mist Edge upgrade request."""
        checked_ids = MxEdgeLifecycleModels._require_ids(mxedge_ids, "mxedge_ids")  # WHY: API needs targets.
        body = MxEdgeLifecycleModels._upgrade_body(checked_ids, version)  # WHY: keep body construction testable.
        target = f"mxedges={','.join(checked_ids)} version={version}"  # WHY: show upgrade target.
        return LifecycleRequest(STEP_UPGRADE, "UPGRADE", body, target, dry_run)  # WHY: operation uses this guard.

    @staticmethod
    def _upgrade_body(mxedge_ids: list[str], version: str) -> dict[str, object]:
        """Return the OpenAPI-shaped upgrade body."""
        return {  # WHY: these fields match the documented multi-upgrade example.
            "mxedge_ids": mxedge_ids,  # WHY: identify the Mist Edges to upgrade.
            "strategy": MxEdgeLifecycleModels.DEFAULT_STRATEGY,  # WHY: serial reduces concurrent outage risk.
            "versions": {"tunterm": version},  # WHY: tunnel service version is the safest default target.
        }

    @staticmethod
    def _require_ids(values: list[str], field_name: str) -> list[str]:
        """Return non-empty stripped identifiers or raise `ValueError`."""
        cleaned = [value.strip() for value in values if value.strip()]  # WHY: ignore accidental blank tokens.
        if not cleaned:  # WHY: Mist should never receive an empty target list.
            raise ValueError(f"{field_name} must contain at least one value")  # WHY: name the bad field.
        return cleaned  # WHY: downstream request bodies use cleaned values.


@dataclass(frozen=True)
class UpgradePollResult:
    """Final result from the upgrade poll loop."""

    upgrade_id: str  # WHY: identify the status object that was read.
    status: str  # WHY: preserve the last Mist status string.
    terminal: bool  # WHY: tell the operator whether Mist reached a final state.
    timed_out: bool  # WHY: distinguish timeout from a terminal failure.
    poll_count: int  # WHY: show how many reads occurred.


class UpgradeStatusReader:
    """Read terminal status words from Mist upgrade objects."""

    @staticmethod
    def status_from(document: dict[str, Any]) -> str:
        """Return the best status value from a Mist upgrade document."""
        for key in ("status", "state", "upgrade_status"):  # WHY: Mist responses vary by endpoint version.
            value = document.get(key)  # WHY: inspect one candidate field.
            if isinstance(value, str) and value:  # WHY: a non-empty string can be compared.
                return value.lower()  # WHY: terminal matching is case-insensitive.
        return "unknown"  # WHY: unknown keeps polling until timeout.

    @staticmethod
    def is_terminal(status: str) -> bool:
        """Return True when a status should stop the poll loop."""
        return status.lower() in TERMINAL_STATUSES  # WHY: one shared set defines terminal states.
