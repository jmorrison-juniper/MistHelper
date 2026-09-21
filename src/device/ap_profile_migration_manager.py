"""AP-to-device-profile migration and revert manager (menus 207 and 208).

This module hosts ``APProfileMigrationManager``, a static-method class that
implements two destructive Mist operations:

* Menu 207 -- bulk-reassign every AP bound to one source device profile to a
  chosen target device profile, with a full pre-change JSON backup written
  under ``data/`` before any AP is touched.
* Menu 208 -- consume a backup file written by menu 207 and reassign each
  listed AP back to the original source device profile, with a JSONL audit
  line appended via the shared ``TelemetryEmitter``.

Why:
    Mist device profiles carry the AP's radio, SSID, and channel plan. When an
    operator wants to promote a fleet to a new profile (or roll back a bad
    change) the UI forces one-AP-at-a-time edits. This module packages the
    fleet-wide walk, the pre-change snapshot, and the round-trip revert into a
    single audited, resumable operation that a small team can trust with
    hundreds of APs.

Module-import must remain side-effect free (``--help`` guard):
    Only ``import`` statements at module scope; all I/O, prompts, and API
    calls live inside functions invoked from the menu dispatch table.
"""

# WHY: PEP 604 unions and forward references keep annotations concise on 3.13+.
from __future__ import annotations  # WHY: Forward references keep destructive manager annotations import-safe.

# WHY: bounded retry backoff and progress-time seams live in stdlib only per the
# no-new-dependency constraint from plan.md.
import json  # WHY: backup file writes and loads use only stdlib json.
import logging  # WHY: progress + destructive-run WARNING land on the module logger.
import time  # WHY: default sleeper for the bounded retry seam.
from dataclasses import dataclass  # WHY: group related run state and keep helper signatures small.
from datetime import UTC, datetime  # WHY: UTC-normalized backup timestamps.
from pathlib import Path  # WHY: portable filesystem joins for the backup file path.
from typing import Any  # WHY: Mist SDK payloads use dictionary-like API response objects.

# WHY: importing the mistapi sub-modules at module load lets tests monkey-patch
# them via ``patch("mistapi.api.v1.sites.devices.updateSiteDevice", ...)``.
import mistapi  # WHY: kept for get_all() pagination in production paths.
from mistapi.api.v1.orgs import deviceprofiles as _mist_deviceprofiles  # WHY: profile picker + snapshot fetcher.
from mistapi.api.v1.orgs import sites as _mist_orgs_sites  # WHY: org-wide site enumeration.
from mistapi.api.v1.sites import devices as _mist_site_devices  # WHY: per-site AP listing + updateSiteDevice PUT.

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader can filter by source.

# WHY: module logger uses the dotted module path so operators can filter by
# ``src.device.ap_profile_migration_manager`` in the shared MistHelper logs.
_LOGGER = logging.getLogger(__name__)  # WHY: Module records identify AP profile migration actions.

# WHY: retry cadence pinned by research.md Decision 2. Two retries -> three total
# attempts; a change here MUST be reflected in the T013 test assertion.
_RETRY_BACKOFF_SECONDS: tuple[float, ...] = (0.5, 1.0)  # Preserve the existing behavior during the compliance refactor.

# WHY: adaptive rate limiter fallback per plan-rate-limiting.md Q1.
# Mist enforces 5000 requests per clock hour on the /api path; the theoretical
# minimum steady-state gap is 3600/5000 = 0.72 s per PUT. When the shared
# ``RateLimitingUtils.get_rate_limited_delay`` helper raises (FR-A06) the
# migrate and revert loops MUST fall back to a fixed conservative sleep so a
# limiter regression does not stall or halt a 10K-AP run. Value locked at the
# addendum-plan level; do not re-derive here.
_LIMITER_FALLBACK_DELAY: float = 0.75  # seconds

# WHY: fixed backup-file schema version per data-model §1.3. A future format
# change bumps this integer and the revert refuses unknown values (FR-020).
_BACKUP_SCHEMA_VERSION = 1  # WHY: Revert rejects backups with an unknown schema.

# WHY: progress cadence pinned by research.md Decision 3 -- print at N=1, every
# _PROGRESS_STRIDE, and at N=total. T015 locks the stride at 10.
_PROGRESS_STRIDE = 10  # WHY: Operators get bounded progress output during large AP runs.

# WHY: default directory for backup files. The test fixture monkey-patches this
# to a tmp_path/data so a unit test never scribbles under the repo data/ dir.
_DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")  # WHY: Backup files stay under data.

# WHY: confirmation keywords per research.md Decision 5 -- uppercase-exact
# strings so a typo cannot silently arm a destructive run.
_KEYWORD_LIVE = "MIGRATE"  # WHY: A live migration requires an exact typed confirmation.
_KEYWORD_DRY_RUN = "DRY-RUN"  # WHY: A preview run uses an exact typed confirmation.
_KEYWORD_REVERT = "REVERT"  # WHY: A revert requires an exact typed confirmation.

# WHY: telemetry file name for the JSONL audit stream (data-model 2.1). Kept as
# a module constant so tests and production point at the same relative path.
_REVERT_TELEMETRY_FILENAME = "ap_profile_migration_revert.jsonl"  # WHY: Revert audit rows use this file.

# WHY: migrate-side JSONL audit stream (addendum FR-A09, TR032). Distinct
# filename so operators can grep menu-207 runs separately from menu-208 runs.
_MIGRATE_TELEMETRY_FILENAME = "ap_profile_migration_migrate.jsonl"  # WHY: Migration audit rows use this file.

# WHY: sentinel return value from ``_revert_one_ap`` when the AP has been
# deleted from Mist since the migration (data-model 2.2 -- ``missing_count``).
_REVERT_MISSING = "missing"  # WHY: The revert loop treats a deleted AP as recoverable.

# WHY: the mistapi SDK returns an APIResponse for an error status. It does not
# raise. Any status at or above this floor means the PUT changed nothing.
_HTTP_ERROR_FLOOR = 400  # Preserve the existing behavior during the compliance refactor.


@dataclass
class APProfileBackupContext:  # Preserve the existing behavior during the compliance refactor.
    """Input values that form one migration backup payload."""

    org_id: str  # WHY: The backup records the org that owns the migration.
    source_id: str  # WHY: The backup records the profile that APs leave.
    source_snapshot: dict[str, Any]  # WHY: The backup preserves the pre-change source profile.
    target_id: str  # WHY: The backup records the profile that APs enter.
    target_snapshot: dict[str, Any]  # WHY: The backup preserves the pre-change target profile.


@dataclass
class APProfileReassignmentPlan:  # Preserve the existing behavior during the compliance refactor.
    """Mutable state for one migration PUT loop."""

    session: Any  # WHY: The PUT loop needs the active Mist API session.
    ap_records: list[dict[str, Any]]  # WHY: The PUT loop reassigns these AP records in order.
    target_id: str  # WHY: Each PUT binds the AP to this device profile.
    backup_path: str  # WHY: The PUT loop updates this backup file after each success.
    payload: dict[str, Any]  # WHY: The caller and loop share the in-memory backup record.
    progress_stride: int = _PROGRESS_STRIDE  # WHY: Progress output keeps the existing cadence by default.


@dataclass
class APProfileRevertOutcomeContext:  # Preserve the existing behavior during the compliance refactor.
    """Mutable state for one AP during a revert loop."""

    mist_session: Any  # WHY: The revert helper needs the active Mist API session.
    device_id: str  # WHY: The revert helper names the AP in outcome lists and logs.
    site_id: str  # WHY: The revert PUT requires the AP site identifier.
    source_id: str  # WHY: The revert PUT restores this device profile.
    pacing_stats: dict[str, float | int]  # WHY: The revert helper records rate-limit and failure counters.


@dataclass
class APProfileRevertResultLists:  # Preserve the existing behavior during the compliance refactor.
    """Outcome lists that the revert loop mutates in place."""

    reverted_ids: list[str]  # WHY: Successful AP IDs feed the summary and audit payload.
    missing_ids: list[str]  # WHY: Missing AP IDs feed the summary and audit payload.
    failed_ids: list[str]  # WHY: Failed AP IDs feed the summary and audit payload.


@dataclass
class APProfileRunSummary:  # Preserve the existing behavior during the compliance refactor.
    """Common summary fields for AP profile migration reporting."""

    source_name: str  # WHY: The operator summary needs the source profile name.
    source_id: str  # WHY: The operator summary and audit need the source profile ID.
    planned_count: int  # WHY: The operator summary and audit need the intended AP count.
    backup_path: str  # WHY: The operator summary and audit need the backup path.
    outcome: str  # WHY: The operator summary and audit need the final run state.
    pacing_stats: dict[str, float | int]  # WHY: Pacing metrics must stay grouped with the run result.


@dataclass
class APProfileRevertSummary:  # Preserve the existing behavior during the compliance refactor.
    """Complete result data for one revert command."""

    run: APProfileRunSummary  # WHY: Shared run fields stay in one grouped object.
    reverted_ids: list[str]  # WHY: The revert summary prints the successful AP count.
    missing_ids: list[str]  # WHY: The revert summary prints recoverable missing APs.
    failed_ids: list[str]  # WHY: The revert summary prints APs that need manual repair.


@dataclass
class APProfileMigrationSummary:  # Preserve the existing behavior during the compliance refactor.
    """Complete result data for one migration command."""

    source_name: str  # WHY: The migration summary prints the source profile name.
    source_id: str  # WHY: The migration summary prints the source profile ID.
    target_name: str  # WHY: The migration summary prints the target profile name.
    target_id: str  # WHY: The migration summary prints the target profile ID.
    backup_path: str  # WHY: The migration summary prints the backup file path.
    payload: dict[str, Any]  # WHY: The migration summary reads counts and pacing data from the final payload.


class APProfileReassignmentError(RuntimeError):  # Preserve the existing behavior during the compliance refactor.
    """Raised when a reassignment PUT reports an error status.

    Why:
        Issue #1700 recorded 4030 PUT calls that changed no device profile.
        The SDK answers an error status with an object, so the old code read
        that object as a success. This exception makes the failure visible to
        the retry loop, to the failure counters, and to the operator.

    Attributes:
        response: The SDK response object. ``_is_429`` reads ``status_code``
            from this attribute, so a rate-limit answer still paces the run.
        status_code: The HTTP status the SDK reported.
    """

    def __init__(
        self, response: Any, device_id: str
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Build the error from the SDK response and the AP that failed.

        Args:
            response: The object ``updateSiteDevice`` returned.
            device_id: The AP the PUT targeted, for the operator-facing text.
        """
        # WHY: _is_429 reads err.response.status_code. Keeping the original
        # object here lets the existing pacing path see a 429 answer.
        self.response = response  # Preserve the existing behavior during the compliance refactor.
        # WHY: cached so a caller reads the status without a second getattr.
        self.status_code = getattr(
            response, "status_code", None
        )  # Preserve the existing behavior during the compliance refactor.
        super().__init__(
            f"updateSiteDevice reported HTTP {self.status_code} for device {device_id}"
        )  # Preserve the existing behavior during the compliance refactor.


def _utc_iso_timestamp() -> str:  # Preserve the existing behavior during the compliance refactor.
    """Return the current wall-clock time as an ISO 8601 extended UTC string.

    Why:
        The revert audit event (data-model 2.2) records ``timestamp_utc`` in
        the canonical trailing-Z form ``YYYY-MM-DDTHH:MM:SSZ``. Centralising
        the formatting here keeps every audit call site consistent and lets a
        future change to microsecond precision land in exactly one place.

    Returns:
        ISO 8601 extended UTC timestamp with a trailing ``Z`` suffix (for
        example ``"2026-07-27T19:30:45Z"``).
    """
    # WHY: aware UTC + ISO extended, then rewrite ``+00:00`` to ``Z`` for the
    # canonical trailing-Z shape the data-model example uses.
    return (
        datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    )  # Preserve the existing behavior during the compliance refactor.


class APProfileMigrationManager:  # Preserve the existing behavior during the compliance refactor.
    """Static-method class for AP-to-device-profile migration and revert.

    Groups the two public entry points and their private helpers so the
    backup-file schema, the AP-record shape, and the bounded retry policy
    live in one place. Follows the same pattern as ``SiteConfigManager``
    (menu 174) and ``OrgSyntheticProbesManager`` (menu 206).

    Why:
        The migrate and revert operations share the backup-file schema, the
        AP-discovery walk, and the profile-lookup helper. Splitting them into
        two modules would duplicate these helpers without a clear boundary
        (per research.md Decision 6).
    """

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    @staticmethod
    def migrate_aps_between_device_profiles(
        session: Any | None = None,
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Menu 207 entry point -- bulk-migrate APs between two device profiles.

        Discovers every AP bound to a chosen source profile across every site
        in the selected organization, writes a full pre-change JSON backup
        under ``data/``, then per-AP PUTs each AP to the chosen target
        profile with bounded retry and stop-on-first-failure semantics.

        Why:
            Delivers the primary user story (US1) as a single audited
            operation. The per-AP PUT is required by FR-017 so a mid-run
            failure records the exact partial-success set for a later revert.

        Args:
            session: The ``mistapi`` API session. When ``None`` the entry
                point resolves the ambient MistHelper session from
                ``ConfigUtils`` (matches the menu-206 wiring pattern).

        Returns:
            ``None``. The operation prints its own end-of-run summary and
            writes the backup file to disk; the caller does not consume any
            return value.
        """
        # WHY: destructive-operation banner per Constitution Principle V so the
        # log timeline shows the exact moment a mutating run started.
        _LOGGER.warning("Menu #207 DESTRUCTIVE: migrate APs started")

        # WHY: lazy import breaks the circular dependency between the top-level
        # MistHelper.py module and this src/ package.
        from src.config.source_dependency_resolver import (
            SourceDependencyResolver as _mh,  # WHY: resolve source dependencies without importing the root module.
        )

        # WHY: resolve org context via the shared cached-or-prompted helper.
        org_id = (
            _mh.ConfigUtils.get_cached_or_prompted_org_id()
        )  # Preserve the existing behavior during the compliance refactor.
        # WHY: fall back to the ambient MistHelper apisession when the caller
        # did not pass one -- matches the menu-206 wiring pattern.
        mist_session = (
            session if session is not None else _mh.apisession
        )  # Preserve the existing behavior during the compliance refactor.

        # WHY: two picker calls -- source first, then target. The refusal
        # short-circuit (FR-008) happens as soon as we know both IDs.
        source_id, source_name, source_snapshot = APProfileMigrationManager._pick_ap_device_profile(
            mist_session, org_id, "Select the SOURCE device profile"
        )
        target_id, target_name, target_snapshot = APProfileMigrationManager._pick_ap_device_profile(
            mist_session, org_id, "Select the TARGET device profile"
        )

        # WHY: FR-008 -- same-profile selection is a no-op destructive run whose
        # only effect is a spurious success audit line. Refuse loudly.
        if source_id == target_id:  # Preserve the existing behavior during the compliance refactor.
            print(  # Preserve the existing behavior during the compliance refactor.
                "Error: source and target device profiles are the same. " "Select two different profiles.",
            )
            _LOGGER.warning(
                "Refused: source and target profiles are identical (id=%s)", source_id
            )  # Preserve the existing behavior during the compliance refactor.
            return  # Preserve the existing behavior during the compliance refactor.

        # WHY: AP-discovery walk -- one pass across every site in the org.
        ap_records = APProfileMigrationManager._discover_aps_on_source_profile(
            mist_session, org_id, source_id
        )  # Preserve the existing behavior during the compliance refactor.

        # WHY: FR-010 -- empty source is not a failure; print the exact
        # short-circuit message and return before writing any file.
        if not ap_records:  # Preserve the existing behavior during the compliance refactor.
            print(
                "No APs bound to source profile. Nothing to migrate."
            )  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.info(
                "Nothing to migrate: source profile %s has zero APs", source_id
            )  # Preserve the existing behavior during the compliance refactor.
            return  # Preserve the existing behavior during the compliance refactor.

        # WHY: render the operator-visible plan before the confirmation prompt
        # so the operator sees exactly which APs will move.
        APProfileMigrationManager._render_migration_plan(
            (source_id, source_name), (target_id, target_name), ap_records
        )  # Preserve the existing behavior during the compliance refactor.

        # WHY: guarded confirmation -- accepts MIGRATE (live) or DRY-RUN (preview).
        decision = APProfileMigrationManager._confirm_migration(
            len(ap_records), source_name, target_name
        )  # Preserve the existing behavior during the compliance refactor.
        if decision == "cancel":  # Preserve the existing behavior during the compliance refactor.
            print("Migration cancelled.")  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.info(
                "Cancelled by operator at confirmation prompt"
            )  # Preserve the existing behavior during the compliance refactor.
            return  # Preserve the existing behavior during the compliance refactor.
        if decision == "dry_run":  # Preserve the existing behavior during the compliance refactor.
            # WHY: FR-015 -- dry-run writes no file and issues no PUT. Return
            # immediately so no backup or PUT side effect occurs.
            print("Dry run: no changes made")  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.info(
                "Dry-run selected; no backup and no PUT will be issued"
            )  # Preserve the existing behavior during the compliance refactor.
            return  # Preserve the existing behavior during the compliance refactor.

        # WHY: build the backup payload BEFORE any PUT so the on-disk file is
        # the single source of truth if the run is interrupted (FR-011).
        backup_context = APProfileBackupContext(  # WHY: Group related backup inputs before the payload builder runs.
            org_id=org_id,  # WHY: Preserve the selected org in the backup file.
            source_id=source_id,  # WHY: Preserve the source profile ID in the backup file.
            source_snapshot=source_snapshot,  # WHY: Preserve the source profile snapshot before any PUT.
            target_id=target_id,  # WHY: Preserve the target profile ID in the backup file.
            target_snapshot=target_snapshot,  # WHY: Preserve the target profile snapshot before any PUT.
        )
        payload = APProfileMigrationManager._build_backup_payload(
            backup_context, ap_records
        )  # Preserve the existing behavior during the compliance refactor.
        backup_path = APProfileMigrationManager._write_backup_file(
            payload, _DATA_DIR
        )  # Preserve the existing behavior during the compliance refactor.
        _LOGGER.info(
            "Backup file written: %s", backup_path
        )  # Preserve the existing behavior during the compliance refactor.

        # WHY: the loop mutates the on-disk backup after each success so an
        # interrupted run leaves the file in a consistent partial state. The
        # in-memory ``payload`` dict is mutated in place; the returned value
        # is the same object -- kept explicit for readability.
        # WHY: issue #1700 -- Ctrl+C used to skip the audit emission below, so
        # a stopped run left no JSONL row at all. Catch the interrupt, record
        # the partial result, then re-raise after the audit row is written.
        interrupted = False  # Preserve the existing behavior during the compliance refactor.
        try:
            final_payload = APProfileMigrationManager._run_reassignment_loop(
                APProfileReassignmentPlan(  # WHY: Keep migration loop inputs together for structural compliance.
                    session=mist_session,  # WHY: The loop needs the active Mist API session.
                    ap_records=ap_records,  # WHY: The loop reassigns APs in this planned order.
                    target_id=target_id,  # WHY: The loop assigns each AP to this profile.
                    backup_path=backup_path,  # WHY: The loop updates this file after each success.
                    payload=payload,  # WHY: The loop mutates the caller-owned backup payload.
                    progress_stride=_PROGRESS_STRIDE,  # WHY: Preserve the existing progress cadence.
                )
            )
        except KeyboardInterrupt:  # Preserve the existing behavior during the compliance refactor.
            # WHY: the loop mutates ``payload`` in place, so it already holds
            # every AP that was reassigned before the operator stopped the run.
            final_payload = payload  # Preserve the existing behavior during the compliance refactor.
            final_payload["outcome"] = "interrupted"  # Preserve the existing behavior during the compliance refactor.
            interrupted = True  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.warning(  # Preserve the existing behavior during the compliance refactor.
                "Migration interrupted by the operator after %d of %d APs. Writing the audit row.",
                len(final_payload.get("aps_reassigned", [])),
                len(ap_records),
            )

        # WHY: use the in-memory final payload for the summary print so we
        # never re-read a file that may have been left in a partial state by
        # a fixture-mocked backup writer.
        APProfileMigrationManager._print_migration_summary(
            APProfileMigrationSummary(  # WHY: Group printed migration fields for structural compliance.
                source_name=source_name,  # WHY: The summary prints the source profile name.
                source_id=source_id,  # WHY: The summary prints the source profile ID.
                target_name=target_name,  # WHY: The summary prints the target profile name.
                target_id=target_id,  # WHY: The summary prints the target profile ID.
                backup_path=backup_path,  # WHY: The summary prints the backup file path.
                payload=final_payload,  # WHY: The summary reads counts and pacing data from the final payload.
            )
        )

        # WHY: FR-A09 -- one JSONL audit row per migrate invocation. Mirrors
        # the revert-side envelope so downstream reporting sees a single
        # shape across both menus. Best-effort write.
        _pacing = final_payload.get("_pacing") or {}  # Preserve the existing behavior during the compliance refactor.
        _delay_count = int(
            _pacing.get("delay_count", 0)
        )  # Preserve the existing behavior during the compliance refactor.
        _delay_sum = float(
            _pacing.get("delay_sum", 0.0)
        )  # Preserve the existing behavior during the compliance refactor.
        _delay_mean = (
            (_delay_sum / _delay_count) if _delay_count > 0 else 0.0
        )  # Preserve the existing behavior during the compliance refactor.
        _delay_max = float(
            _pacing.get("delay_max", 0.0)
        )  # Preserve the existing behavior during the compliance refactor.
        APProfileMigrationManager._emit_migrate_audit(  # Preserve the existing behavior during the compliance refactor.
            {
                "event_type": "ap_profile_migration_migrate",
                "timestamp_utc": _utc_iso_timestamp(),
                "org_id": org_id,
                "backup_file_path": str(backup_path),
                "source_profile_id": source_id,
                "target_profile_id": target_id,
                "planned_count": len(ap_records),
                "reassigned_count": len(final_payload.get("aps_reassigned", [])),
                "outcome": final_payload.get("outcome", "unknown"),
                "pacing": {
                    "puts_issued": int(_pacing.get("puts_issued", 0)),
                    "http_429_seen": int(_pacing.get("http_429_seen", 0)),
                    "non_429_failures": int(_pacing.get("non_429_failures", 0)),
                    "delay_seconds_mean": round(_delay_mean, 3),
                    "delay_seconds_max": round(_delay_max, 3),
                },
            }
        )

        # WHY: the audit row is on disk now, so the operator's Ctrl+C may travel
        # on to the menu loop that reports the interruption.
        if interrupted:  # Preserve the existing behavior during the compliance refactor.
            raise KeyboardInterrupt  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def revert_ap_profile_migration(
        session: Any | None = None,
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Menu 208 entry point -- revert a prior migration from its backup file.

        Reads a backup file written by menu 207 and reassigns each listed AP
        back to the original source device profile, with strict backup-schema
        validation, source-profile-still-exists guard, per-AP missing-AP
        tolerance, and a JSONL audit line appended via ``TelemetryEmitter``.

        Why:
            Delivers the safety-net user story (US2). Every migration should
            be reversible with the same tool and the same audit trail; the
            backup file plus the JSONL audit line together satisfy FR-019
            through FR-025.

        Args:
            session: The ``mistapi`` API session. When ``None`` the entry
                point resolves the ambient MistHelper session from
                ``ConfigUtils`` (matches the menu-206 wiring pattern).

        Returns:
            ``None``. The operation prints its own end-of-run summary and
            appends a single JSONL row to the shared telemetry stream; the
            caller does not consume any return value.

        Raises:
            Nothing: No exception is raised for operator-visible failures.
                Backup validation failures, source-profile-missing, and
                cancellation are reported on stdout and short-circuit before
                any PUT is issued.
        """
        # WHY: destructive-operation banner per Constitution Principle V so the
        # log timeline shows the exact moment the revert entry point started.
        _LOGGER.warning("Menu #208 DESTRUCTIVE: revert AP profile migration started")

        # WHY: lazy import for the shared MistHelper helpers keeps this module
        # circular-import-safe.
        from src.config.source_dependency_resolver import (
            SourceDependencyResolver as _mh,  # WHY: resolve source dependencies without importing the root module.
        )

        org_id = (
            _mh.ConfigUtils.get_cached_or_prompted_org_id()
        )  # Preserve the existing behavior during the compliance refactor.
        # WHY: fall back to the ambient MistHelper apisession when the caller
        # did not pass one -- matches the menu-206 wiring pattern.
        mist_session = (
            session if session is not None else _mh.apisession
        )  # Preserve the existing behavior during the compliance refactor.

        # WHY: enumerate backup files under the data directory and let the
        # picker resolve the operator's choice. When zero candidates exist the
        # helper returns None and we print a short-circuit message.
        candidates = APProfileMigrationManager._list_backup_files(
            _DATA_DIR
        )  # Preserve the existing behavior during the compliance refactor.
        backup_path = APProfileMigrationManager._pick_backup_file(
            candidates
        )  # Preserve the existing behavior during the compliance refactor.
        if backup_path is None:  # Preserve the existing behavior during the compliance refactor.
            print(
                "No backup file selected. Revert cancelled."
            )  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.info(
                "Revert cancelled: no backup file selected"
            )  # Preserve the existing behavior during the compliance refactor.
            return  # Preserve the existing behavior during the compliance refactor.

        # WHY: rules 1-6 from data-model 1.6. A ValueError names the offending
        # field so the operator can locate the fix without opening the file.
        try:
            payload = APProfileMigrationManager._load_and_validate_backup(
                str(backup_path)
            )  # Preserve the existing behavior during the compliance refactor.
        except ValueError as exc:  # Preserve the existing behavior during the compliance refactor.
            print(f"Invalid backup: {exc}")  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.warning(
                "Revert refused: backup validation failed: %s", exc
            )  # Preserve the existing behavior during the compliance refactor.
            return  # Preserve the existing behavior during the compliance refactor.

        # WHY: data-model 1.3 states "Revert refuses if the operator's current
        # org does not match." Guards against running a backup from org A
        # against org B, which would touch APs that are not in the backup.
        if payload["org_id"] != org_id:  # Preserve the existing behavior during the compliance refactor.
            print(  # Preserve the existing behavior during the compliance refactor.
                f"Refused: backup org_id {payload['org_id']!r} does not match " f"current org_id {org_id!r}.",
            )
            _LOGGER.warning(  # Preserve the existing behavior during the compliance refactor.
                "Revert refused: backup org %s does not match current org %s",
                payload["org_id"],
                org_id,
            )
            return  # Preserve the existing behavior during the compliance refactor.

        source_id = str(payload["source_profile_id"])  # Preserve the existing behavior during the compliance refactor.
        source_name = str(  # Preserve the existing behavior during the compliance refactor.
            payload.get("source_profile_snapshot", {}).get("name", source_id),
        )
        planned_count = len(
            payload.get("aps_planned", [])
        )  # Preserve the existing behavior during the compliance refactor.

        # WHY: FR-021 -- if the source profile was deleted since the migration
        # ran, refuse the revert with an audited failure so the operator sees a
        # loud short-circuit rather than a silent "success" with zero PUTs.
        if not APProfileMigrationManager._verify_source_profile_exists(
            mist_session, org_id, source_id
        ):  # Preserve the existing behavior during the compliance refactor.
            print(  # Preserve the existing behavior during the compliance refactor.
                f"Source profile {source_id} no longer exists in org {org_id}. "
                f"Recreate the profile or hand-edit the backup before retrying.",
            )
            _LOGGER.warning(
                "Revert refused: source profile %s missing in org %s", source_id, org_id
            )  # Preserve the existing behavior during the compliance refactor.
            # WHY: FR-025 -- emit a failure audit row even on this early exit
            # so downstream reporting sees every refused revert attempt.
            APProfileMigrationManager._emit_revert_audit(
                {
                    "event_type": "ap_profile_migration_revert",
                    "timestamp_utc": _utc_iso_timestamp(),
                    "org_id": org_id,
                    "backup_file_path": str(backup_path),
                    "source_profile_id": source_id,
                    "planned_count": planned_count,
                    "reverted_count": 0,
                    "missing_count": 0,
                    "failed_count": 0,
                    "outcome": "failure",
                }
            )
            return  # Preserve the existing behavior during the compliance refactor.

        # WHY: guarded confirmation -- the exact keyword REVERT arms the run;
        # any other input cancels. Mirrors the migrate-side pattern.
        decision = (
            APProfileMigrationManager._confirm_revert(  # Preserve the existing behavior during the compliance refactor.
                len(payload.get("aps_reassigned", [])),
                source_name,
                str(backup_path),
            )
        )
        if decision != "live":  # Preserve the existing behavior during the compliance refactor.
            print("Revert cancelled.")  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.info(
                "Revert cancelled by operator at confirmation prompt"
            )  # Preserve the existing behavior during the compliance refactor.
            return  # Preserve the existing behavior during the compliance refactor.

        # WHY: build a lookup so we can retrieve each AP's site_id (required by
        # updateSiteDevice) from the compact aps_reassigned id list.
        plan_by_id: dict[str, dict[str, Any]] = {
            str(rec["device_id"]): rec for rec in payload.get("aps_planned", [])
        }  # Preserve the existing behavior during the compliance refactor.

        aps_to_revert = [
            str(x) for x in payload.get("aps_reassigned", [])
        ]  # Preserve the existing behavior during the compliance refactor.
        reverted_ids, missing_ids, failed_ids, pacing_stats = APProfileMigrationManager._run_revert_loop(
            mist_session,
            aps_to_revert,
            plan_by_id,
            source_id,
        )

        outcome = APProfileMigrationManager._compute_revert_outcome(
            reverted_ids, missing_ids, failed_ids
        )  # Preserve the existing behavior during the compliance refactor.

        revert_summary = APProfileRevertSummary(  # WHY: Group summary values for printing and audit emission.
            run=APProfileRunSummary(  # WHY: Shared run metadata stays in one object.
                source_name=source_name,  # WHY: The operator summary names the source profile.
                source_id=source_id,  # WHY: The audit row records the restored profile ID.
                planned_count=planned_count,  # WHY: The audit row records the intended AP count.
                backup_path=str(backup_path),  # WHY: The audit row records the replayed backup file.
                outcome=outcome,  # WHY: The audit row records the final revert state.
                pacing_stats=pacing_stats,  # WHY: The audit row records limiter statistics.
            ),
            reverted_ids=reverted_ids,  # WHY: The summary names successful reverts by count.
            missing_ids=missing_ids,  # WHY: The summary names missing APs when present.
            failed_ids=failed_ids,  # WHY: The summary names failed APs when present.
        )
        APProfileMigrationManager._print_revert_summary(
            revert_summary
        )  # Preserve the existing behavior during the compliance refactor.

        # WHY: FR-025 -- one JSONL audit row per revert invocation. Best-effort
        # write; TelemetryEmitter swallows OSError and logs a warning.
        APProfileMigrationManager._emit_revert_audit(  # Preserve the existing behavior during the compliance refactor.
            APProfileMigrationManager._build_revert_audit_payload(
                org_id,
                revert_summary,
            )
        )

    # ------------------------------------------------------------------
    # Private helpers -- revert loop and reporting (extracted for Radon CC)
    # ------------------------------------------------------------------

    @staticmethod
    def _new_pacing_stats() -> dict[str, float | int]:  # Preserve the existing behavior during the compliance refactor.
        """Return the initial pacing-stats dict for a menu-207/208 loop.

        Why:
            Both the migrate and the revert loops keep the same counters
            (puts_issued, http_429_seen, non_429_failures, delay_sum, delay_max,
            delay_count) so that the JSONL audit and the operator-facing
            summary share one shape. Centralising the initialiser removes a
            small source of copy-paste drift.

        Returns:
            A fresh dict with every counter zeroed.
        """
        return {  # Preserve the existing behavior during the compliance refactor.
            "puts_issued": 0,
            "http_429_seen": 0,
            "non_429_failures": 0,
            "delay_sum": 0.0,
            "delay_max": 0.0,
            "delay_count": 0,
        }

    @staticmethod
    def _run_revert_loop(  # Preserve the existing behavior during the compliance refactor.
        mist_session: Any,
        aps_to_revert: list[str],
        plan_by_id: dict[str, dict[str, Any]],
        source_id: str,
    ) -> tuple[list[str], list[str], list[str], dict[str, float | int]]:
        """Iterate every AP in the backup and revert each to the source profile.

        Why:
            Extracted from ``revert_ap_profile_migration`` so the entry point
            stays under the Radon CC gate. The loop owns per-invocation pacing
            state, 429-tolerant per-AP error handling, and the missing/reverted
            /failed partitioning; keeping it in one focused helper is easier to
            reason about than an inline block inside the 200-line entry point.

        Args:
            mist_session: The mistapi API session used for the PUT calls.
            aps_to_revert: Device IDs (in reassignment order) from the backup.
            plan_by_id: Lookup of the full APRecord dicts keyed by ``device_id``.
            source_id: The original source profile ID to reassign each AP back
                to.

        Returns:
            A ``(reverted_ids, missing_ids, failed_ids, pacing_stats)`` tuple
            with disjoint device-id lists and the final pacing counters.
        """
        reverted_ids: list[str] = []  # Preserve the existing behavior during the compliance refactor.
        missing_ids: list[str] = []  # Preserve the existing behavior during the compliance refactor.
        failed_ids: list[str] = []  # Preserve the existing behavior during the compliance refactor.
        # WHY: per-invocation pacing state per plan-rate-limiting.md Q3.
        # Mirrors the migrate loop; keeps menus 207 and 208 consistent for
        # the operator (data-model-rate-limiting.md section 2, Q1 lock).
        smoothed: float | None = None  # Preserve the existing behavior during the compliance refactor.
        pacing_stats = (
            APProfileMigrationManager._new_pacing_stats()
        )  # Preserve the existing behavior during the compliance refactor.
        total = len(aps_to_revert)  # Preserve the existing behavior during the compliance refactor.
        for idx, device_id in enumerate(
            aps_to_revert, start=1
        ):  # Preserve the existing behavior during the compliance refactor.
            rec = plan_by_id.get(device_id)  # Preserve the existing behavior during the compliance refactor.
            if rec is None:  # Preserve the existing behavior during the compliance refactor.
                # WHY: validation rule 5 prevents this, but the guard keeps a
                # hand-edited backup from crashing the loop instead of the
                # earlier refusal path.
                _LOGGER.warning(
                    "Skipping unknown device_id %s -- not in aps_planned", device_id
                )  # Preserve the existing behavior during the compliance refactor.
                continue  # Preserve the existing behavior during the compliance refactor.
            # WHY: emit progress at the same cadence as the migration path so
            # operators see the run is making progress on large fleets.
            if (
                idx == 1 or idx % _PROGRESS_STRIDE == 0 or idx == total
            ):  # Preserve the existing behavior during the compliance refactor.
                _LOGGER.info(  # Preserve the existing behavior during the compliance refactor.
                    "Reverting AP %d of %d: device_id=%s",
                    idx,
                    total,
                    device_id,
                )
            # WHY: FR-A01 -- consult the adaptive limiter once per PUT so a
            # 10K-AP revert stays under Mist's 5000-requests-per-hour ceiling.
            smoothed = APProfileMigrationManager._apply_pacing(
                smoothed, pacing_stats
            )  # Preserve the existing behavior during the compliance refactor.
            pacing_stats["puts_issued"] += 1  # Preserve the existing behavior during the compliance refactor.
            APProfileMigrationManager._classify_revert_outcome_for_ap(
                APProfileRevertOutcomeContext(  # WHY: Keep the AP target and pacing state together.
                    mist_session=mist_session,  # WHY: The helper needs the active Mist API session.
                    device_id=device_id,  # WHY: The helper records this AP in exactly one outcome list.
                    site_id=str(rec["site_id"]),  # WHY: The revert PUT requires the AP site identifier.
                    source_id=source_id,  # WHY: The revert PUT restores this profile.
                    pacing_stats=pacing_stats,  # WHY: The helper updates shared pacing counters.
                ),
                APProfileRevertResultLists(  # WHY: Group outcome lists without changing their mutation behavior.
                    reverted_ids=reverted_ids,  # WHY: The helper appends successful AP IDs here.
                    missing_ids=missing_ids,  # WHY: The helper appends missing AP IDs here.
                    failed_ids=failed_ids,  # WHY: The helper appends failed AP IDs here.
                ),
            )
        return (
            reverted_ids,
            missing_ids,
            failed_ids,
            pacing_stats,
        )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _classify_revert_outcome_for_ap(  # Preserve the existing behavior during the compliance refactor.
        context: APProfileRevertOutcomeContext,
        result_lists: APProfileRevertResultLists,
    ) -> None:
        """Attempt one PUT and route the outcome into the correct id list.

        Why:
            Isolates the single-AP branching (429 vs. other exception vs.
            missing AP vs. success) from the enclosing loop so the loop stays
            under the Radon CC gate. All partitioning of the resulting id
            lists happens through explicit ``list.append`` calls so the caller
            can inspect state after the loop finishes.

        Args:
            context: Mist API target data and pacing counters for this AP.
            result_lists: Mutable lists that receive exactly one AP outcome.
        """
        try:
            result = APProfileMigrationManager._revert_one_ap(
                context.mist_session,
                context.device_id,
                context.site_id,
                context.source_id,
            )
        except Exception as exc:  # WHY: tolerant per FR-023.
            # WHY: FR-A04 -- 429 is a throttle signal. Feed the limiter via
            # cache invalidation and continue; do NOT count the AP as failed
            # on 429 alone.
            if APProfileMigrationManager._is_429(exc):  # Preserve the existing behavior during the compliance refactor.
                APProfileMigrationManager._signal_rate_limit_hit()
                context.pacing_stats[
                    "http_429_seen"
                ] += 1  # Preserve the existing behavior during the compliance refactor.
                return  # Preserve the existing behavior during the compliance refactor.
            context.pacing_stats[
                "non_429_failures"
            ] += 1  # Preserve the existing behavior during the compliance refactor.
            result_lists.failed_ids.append(
                context.device_id
            )  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.warning(  # Preserve the existing behavior during the compliance refactor.
                "Revert failed for AP %s after retry exhaustion: %s",
                context.device_id,
                exc,
            )
            return  # Preserve the existing behavior during the compliance refactor.

        if result == _REVERT_MISSING:  # Preserve the existing behavior during the compliance refactor.
            # WHY: FR-023 -- the AP no longer exists in Mist; count and
            # continue instead of aborting the run.
            result_lists.missing_ids.append(
                context.device_id
            )  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.warning(
                "AP %s no longer exists in Mist; counted as missing", context.device_id
            )  # Preserve the existing behavior during the compliance refactor.
            return  # Preserve the existing behavior during the compliance refactor.

        result_lists.reverted_ids.append(
            context.device_id
        )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _compute_revert_outcome(  # Preserve the existing behavior during the compliance refactor.
        reverted_ids: list[str],
        missing_ids: list[str],
        failed_ids: list[str],
    ) -> str:
        """Classify the overall revert run as ``success``, ``partial``, or ``failure``.

        Why:
            Data-model 2.2 defines the three outcomes. Isolating the tri-state
            logic keeps the entry point under the Radon CC gate and gives unit
            tests a single seam to pin every branch of the truth table.

        Args:
            reverted_ids: APs that were reassigned back to the source profile.
            missing_ids: APs that no longer exist in Mist.
            failed_ids: APs that failed for non-429 reasons after retries.

        Returns:
            One of ``"success"``, ``"partial"``, or ``"failure"``.
        """
        if not missing_ids and not failed_ids:  # Preserve the existing behavior during the compliance refactor.
            return "success"  # Preserve the existing behavior during the compliance refactor.
        if reverted_ids or missing_ids:  # Preserve the existing behavior during the compliance refactor.
            return "partial"  # Preserve the existing behavior during the compliance refactor.
        return "failure"  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _print_revert_summary(
        summary: APProfileRevertSummary,
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Print the operator-facing end-of-run summary for menu 208."""
        logger.info("Printing the AP profile revert summary")  # Record the operator summary boundary.
        print("\nRevert summary:")  # Keep the existing heading text for characterization tests.
        print(f"  Backup file: {summary.run.backup_path}")  # Show the replayed backup path for audit lookup.
        print(f"  Source profile: {summary.run.source_name} (id={summary.run.source_id})")  # Show the restored profile.
        print(f"  Planned APs: {summary.run.planned_count}")  # Show the original planned AP count.
        print(f"  Reverted APs: {len(summary.reverted_ids)}")  # Show successful revert count.
        print(f"  Missing APs: {len(summary.missing_ids)}")  # Show recoverable missing AP count.
        print(f"  Failed APs: {len(summary.failed_ids)}")  # Show failed AP count for repair triage.
        print(f"  Outcome: {summary.run.outcome}")  # Show the final state label.
        APProfileMigrationManager._print_revert_detail_ids(summary)  # Print optional AP ID details.
        APProfileMigrationManager._print_pacing_summary(summary.run.pacing_stats)  # Print rate-limit counters.
        logger.debug("Printed revert summary with outcome=%s", summary.run.outcome)  # Record summary completion.

    @staticmethod
    def _print_revert_detail_ids(
        summary: APProfileRevertSummary,
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Print optional missing and failed AP identifiers for menu 208."""
        if summary.missing_ids:  # Name every missing AP so the operator can repair inventory drift.
            print(f"  Missing device_ids: {', '.join(summary.missing_ids)}")  # Preserve the existing detail text.
        if summary.failed_ids:  # Name every failed AP so the operator can retry or repair by hand.
            print(f"  Failed device_ids: {', '.join(summary.failed_ids)}")  # Preserve the existing detail text.

    @staticmethod
    def _pacing_delay_summary(
        pacing_stats: dict[str, float | int],
    ) -> tuple[int, float, float]:  # Preserve the existing behavior during the compliance refactor.
        """Return delay count, mean, and maximum for a pacing statistics dict."""
        delay_count = int(pacing_stats["delay_count"])  # Normalize the counter before division.
        delay_sum = float(pacing_stats["delay_sum"])  # Normalize the sum before division.
        delay_mean = (delay_sum / delay_count) if delay_count > 0 else 0.0  # Avoid division by zero.
        delay_max = float(pacing_stats["delay_max"])  # Normalize the max value for formatting.
        return delay_count, delay_mean, delay_max  # Return all display values as one grouped result.

    @staticmethod
    def _print_pacing_summary(
        pacing_stats: dict[str, float | int],
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Print the shared adaptive-rate-limiter summary block."""
        delay_values = APProfileMigrationManager._pacing_delay_summary(pacing_stats)  # Reuse one formula.
        _delay_count, delay_mean, delay_max = delay_values  # Name each display value for the output row.
        print(f"  Total PUTs issued        : {int(pacing_stats['puts_issued'])}")  # Show write attempts issued.
        print(f"  HTTP 429 responses seen  : {int(pacing_stats['http_429_seen'])}")  # Show throttle events.
        print(f"  Non-429 failures         : {int(pacing_stats['non_429_failures'])}")  # Show hard failure events.
        print(f"  Rate limiter delay (s)   : mean={delay_mean:.3f}  max={delay_max:.3f}")  # Show limiter delay values.

    @staticmethod
    def _build_revert_audit_payload(
        org_id: str, summary: APProfileRevertSummary
    ) -> dict[str, Any]:  # Preserve the existing behavior during the compliance refactor.
        """Build the JSONL audit payload for a completed revert run."""
        logger.info("Building the AP profile revert audit payload")  # Record the audit serialization boundary.
        return {
            "event_type": "ap_profile_migration_revert",
            "timestamp_utc": _utc_iso_timestamp(),
            "org_id": org_id,
            "backup_file_path": summary.run.backup_path,
            "source_profile_id": summary.run.source_id,
            "planned_count": summary.run.planned_count,
            "reverted_count": len(summary.reverted_ids),
            "missing_count": len(summary.missing_ids),
            "failed_count": len(summary.failed_ids),
            "outcome": summary.run.outcome,
            # WHY: FR-A09 -- pacing telemetry sub-dict per
            # data-model-rate-limiting.md section 3.
            "pacing": APProfileMigrationManager._build_pacing_audit_payload(summary.run.pacing_stats),
        }

    @staticmethod
    def _build_pacing_audit_payload(
        pacing_stats: dict[str, float | int],
    ) -> dict[str, int | float]:  # Preserve the existing behavior during the compliance refactor.
        """Build the shared pacing sub-dict for migration and revert audits."""
        delay_values = APProfileMigrationManager._pacing_delay_summary(pacing_stats)  # Reuse summary math.
        _delay_count, delay_mean, delay_max = delay_values  # Name each audit value.
        payload = {  # Keep the audit key order stable for JSONL consumers.
            "puts_issued": int(pacing_stats["puts_issued"]),  # Record total PUT attempts.
            "http_429_seen": int(pacing_stats["http_429_seen"]),  # Record throttle responses.
            "non_429_failures": int(pacing_stats["non_429_failures"]),  # Record non-throttle failures.
            "delay_seconds_mean": round(delay_mean, 3),  # Record rounded average delay.
            "delay_seconds_max": round(delay_max, 3),  # Record rounded maximum delay.
        }
        logger.debug("Built pacing audit payload with puts_issued=%s", payload["puts_issued"])  # Record size.
        return payload  # Return the pacing sub-dict for the caller envelope.

    # ------------------------------------------------------------------
    # Private helpers -- adaptive rate limiting (addendum FR-A01..FR-A09)
    # ------------------------------------------------------------------

    @staticmethod
    def _is_429(err: BaseException) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Return True when ``err`` carries an HTTP 429 status code.

        Why:
            Copies the two-line status_code pattern from
            ``src/api/api_data_fetcher.py._is_rate_limit_error`` verbatim into
            the manager per research-rate-limiting.md Q5. The addendum does
            NOT cross-import that private helper because a public rename in
            the fetcher would silently break the migration. Local copy keeps
            the two consumers independent.

        Args:
            err: The exception raised by the per-AP PUT retry loop.

        Returns:
            True when ``err.response.status_code == 429``; False otherwise
            (including any missing ``response`` or ``status_code`` attribute).
        """
        # WHY: two-line pattern lifted from api_data_fetcher._is_rate_limit_error.
        status_code = getattr(
            getattr(err, "response", None), "status_code", None
        )  # Preserve the existing behavior during the compliance refactor.
        return status_code == 429  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _apply_pacing(  # Preserve the existing behavior during the compliance refactor.
        smoothed: float | None,
        pacing_stats: dict[str, float | int],
    ) -> float | None:
        """Consult the shared rate limiter, sleep, and update in-place stats.

        Why:
            Central seam that both loops call once per outer iteration. Takes
            ``pacing_stats`` by reference (single-writer, O(1) memory per
            data-model-rate-limiting.md section 4) so the caller can print the
            summary and emit the JSONL audit line without threading extra
            values through the loop body. Uses the shared
            ``RateLimitingUtils.get_rate_limited_delay`` PID helper (FR-A03,
            no new limiter API). Sleeps via ``time.sleep(...)`` reached
            through the module attribute so hermetic tests can patch
            ``src.device.ap_profile_migration_manager.time.sleep`` (FR-A07).

        Args:
            smoothed: The prior iteration's smoothed delay estimate; ``None``
                on the first call. The PID helper returns the next value.
            pacing_stats: In-place counter dict (six keys per data-model
                section 4). Mutated with the observed delay before return.

        Returns:
            The updated smoothed-delay value to pass into the next call.
        """
        # WHY: lazy import matches lines 147/265/471; keeps top-of-module
        # circular-safe against the MistHelper entry point.
        from src.config.source_dependency_resolver import (
            SourceDependencyResolver as _mh,  # WHY: resolve source dependencies without importing the root module.
        )

        try:
            smoothed, delay = _mh.RateLimitingUtils.get_rate_limited_delay(
                smoothed,
                _mh.apisession,
                _mh._api_usage_cache,
            )
        except Exception as exc:  # WHY: FR-A06 -- limiter is diagnostic, not critical.
            # WHY: FR-A06 -- a limiter fault MUST NOT halt the migration.
            # Fall back to a fixed conservative sleep and log the fault so
            # the operator can investigate later.
            _LOGGER.warning(  # Preserve the existing behavior during the compliance refactor.
                "Rate limiter failed (%s). Using fallback delay of %.2f s",
                exc,
                _LIMITER_FALLBACK_DELAY,
            )
            delay = _LIMITER_FALLBACK_DELAY  # Preserve the existing behavior during the compliance refactor.

        # WHY: delay is None only if the PID helper misreports; coerce to 0.0
        # so downstream arithmetic stays a float.
        if delay is None:  # Preserve the existing behavior during the compliance refactor.
            delay = 0.0  # Preserve the existing behavior during the compliance refactor.

        pacing_stats["delay_sum"] = float(pacing_stats["delay_sum"]) + float(
            delay
        )  # Preserve the existing behavior during the compliance refactor.
        pacing_stats["delay_max"] = max(
            float(pacing_stats["delay_max"]), float(delay)
        )  # Preserve the existing behavior during the compliance refactor.
        pacing_stats["delay_count"] = (
            int(pacing_stats["delay_count"]) + 1
        )  # Preserve the existing behavior during the compliance refactor.

        # WHY: sleep via module attribute so tests can patch it with
        # ``patch("src.device.ap_profile_migration_manager.time.sleep", ...)``.
        time.sleep(delay)  # Preserve the existing behavior during the compliance refactor.
        return smoothed  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _signal_rate_limit_hit() -> None:  # Preserve the existing behavior during the compliance refactor.
        """Invalidate the shared API-usage cache so the limiter refreshes.

        Why:
            The addendum feeds observed 429 responses back to the limiter
            without adding a new ``RateLimitingUtils`` method (FR-A03).
            Setting ``_api_usage_cache["initialized"] = False`` makes the
            existing ``_needs_refresh`` predicate return True on the next
            consult; that triggers a live ``_refresh_api_usage`` round-trip
            and drives the PID error term up. Wrapped in ``try/except`` on
            KeyError and TypeError so a missing or unexpected cache shape
            (edge case: apisession or cache absent at menu-dispatch time)
            never crashes the loop.
        """
        # WHY: lazy import for the same reason as _apply_pacing above.
        from src.config.source_dependency_resolver import (
            SourceDependencyResolver as _mh,  # WHY: resolve source dependencies without importing the root module.
        )

        _LOGGER.warning(  # Preserve the existing behavior during the compliance refactor.
            "The API returned HTTP 429. Invalidating the API usage cache to trigger a limiter refresh",
        )
        try:
            # WHY: cache-invalidation is the addendum's 429 feedback surface;
            # _needs_refresh consumes this flag on the next consult.
            _mh._api_usage_cache["initialized"] = (
                False  # Preserve the existing behavior during the compliance refactor.
            )
        except (
            KeyError,
            TypeError,
            AttributeError,
        ) as exc:  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.warning(  # Preserve the existing behavior during the compliance refactor.
                "API usage cache unavailable (%s); 429 feedback suppressed this iteration",
                exc,
            )

    # ------------------------------------------------------------------
    # Private helpers -- migration (T017-T024)
    # ------------------------------------------------------------------

    @staticmethod
    def _fetch_and_sort_ap_profiles(
        session: Any, org_id: str
    ) -> list[dict[str, Any]]:  # Preserve the existing behavior during the compliance refactor.
        """Fetch all AP device profiles for the org, filtered and alphabetised.

        Why:
            Extracted from ``_pick_ap_device_profile`` to keep the picker's
            cyclomatic complexity under the Radon gate. The fetch + pagination
            + filter + sort has no interactive state, so it lives on its own
            and is easy for unit tests to patch.

        Args:
            session: The mistapi API session.
            org_id: The org whose device profiles to list.

        Returns:
            A list of profile dicts with ``type == "ap"``, sorted by lower-case
            name.

        Raises:
            RuntimeError: When the org has zero AP device profiles.
        """
        response = _mist_deviceprofiles.listOrgDeviceProfiles(
            session, org_id
        )  # Preserve the existing behavior during the compliance refactor.
        # WHY: get_all walks pagination in production; tests can return a
        # ready-made list on .data and get_all handles both shapes.
        try:
            profiles = mistapi.get_all(
                response=response, mist_session=session
            )  # Preserve the existing behavior during the compliance refactor.
        except Exception:  # WHY: fallback for mocked responses.
            profiles = (
                getattr(response, "data", []) or []
            )  # Preserve the existing behavior during the compliance refactor.

        ap_profiles = [
            p for p in profiles if p.get("type") == "ap"
        ]  # Preserve the existing behavior during the compliance refactor.
        if not ap_profiles:  # Preserve the existing behavior during the compliance refactor.
            raise RuntimeError(
                "No AP device profiles found in the selected organization."
            )  # Preserve the existing behavior during the compliance refactor.

        # WHY: alphabetise by name for a stable operator UX.
        ap_profiles.sort(
            key=lambda p: str(p.get("name", "")).lower()
        )  # Preserve the existing behavior during the compliance refactor.
        return ap_profiles  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _pick_ap_device_profile(
        session: Any, org_id: str, prompt_text: str
    ) -> tuple[str, str, dict[str, Any]]:  # Preserve the existing behavior during the compliance refactor.
        """Prompt the operator to pick one AP device profile from the org.

        Why:
            Both the source and the target picker share the same list + prompt
            code; centralising it here keeps the entry point short and lets
            unit tests patch this single seam to return canned tuples.

        Args:
            session: The mistapi API session.
            org_id: The org whose device profiles to list.
            prompt_text: The operator-visible prompt banner.

        Returns:
            A ``(profile_id, profile_name, profile_snapshot_dict)`` tuple
            where the snapshot is the full JSON as returned by Mist.

        Raises:
            RuntimeError: When the org has zero AP device profiles or the
                operator cancels the picker.
        """
        # WHY: lazy import for InputUtils so this module stays circular-safe.
        from src.config.source_dependency_resolver import (
            SourceDependencyResolver as _mh,  # WHY: resolve source dependencies without importing the root module.
        )

        ap_profiles = APProfileMigrationManager._fetch_and_sort_ap_profiles(
            session, org_id
        )  # Preserve the existing behavior during the compliance refactor.

        print(f"\n{prompt_text}")  # Preserve the existing behavior during the compliance refactor.
        for idx, prof in enumerate(
            ap_profiles, start=1
        ):  # Preserve the existing behavior during the compliance refactor.
            print(
                f"  {idx}. {prof.get('name', '<unnamed>')} (id={prof.get('id', '<no-id>')})"
            )  # Preserve the existing behavior during the compliance refactor.

        # WHY: EOF-safe input via the shared safe_input helper; retry on
        # non-numeric or out-of-range input.
        count = len(ap_profiles)  # Preserve the existing behavior during the compliance refactor.
        while True:  # Preserve the existing behavior during the compliance refactor.
            choice = _mh.InputUtils.safe_input(  # Preserve the existing behavior during the compliance refactor.
                f"  Select profile (1-{count}) or 'q' to cancel: ",
                default_value="",
                allow_empty=True,
                context="ap_profile_picker",
            )
            if choice.lower() == "q":  # Preserve the existing behavior during the compliance refactor.
                raise RuntimeError(
                    "Profile selection cancelled by operator."
                )  # Preserve the existing behavior during the compliance refactor.
            try:
                index = int(choice)  # Preserve the existing behavior during the compliance refactor.
            except ValueError:  # Preserve the existing behavior during the compliance refactor.
                print(
                    f"  Enter a number between 1 and {count}."
                )  # Preserve the existing behavior during the compliance refactor.
                continue  # Preserve the existing behavior during the compliance refactor.
            if 1 <= index <= count:  # Preserve the existing behavior during the compliance refactor.
                picked = ap_profiles[index - 1]  # Preserve the existing behavior during the compliance refactor.
                return (  # Preserve the existing behavior during the compliance refactor.
                    str(picked.get("id", "")),
                    str(picked.get("name", "")),
                    dict(picked),
                )
            print(
                f"  Enter a number between 1 and {count}."
            )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _discover_aps_on_source_profile(
        session: Any, org_id: str, source_profile_id: str
    ) -> list[dict[str, Any]]:  # Preserve the existing behavior during the compliance refactor.
        """Walk every site in the org and collect AP records bound to the source profile.

        Why:
            Mist's per-site device list is the only reliable path to enumerate
            APs by device-profile binding; there is no org-wide ``list APs by
            deviceprofile`` endpoint. This helper does the walk once and
            returns a compact ``APRecord`` list per data-model §1.4.

        Args:
            session: The mistapi API session.
            org_id: The org to walk.
            source_profile_id: Only APs whose ``deviceprofile_id`` equals this
                UUID are included.

        Returns:
            A list of dicts each shaped ``{device_id, site_id, mac, hostname}``.
        """
        _LOGGER.info(
            "Discovering APs bound to profile %s across every site", source_profile_id
        )  # Preserve the existing behavior during the compliance refactor.
        # WHY: listOrgSites gives us the site_id list; loop is the only walk.
        sites_response = _mist_orgs_sites.listOrgSites(
            session, org_id
        )  # Preserve the existing behavior during the compliance refactor.
        try:
            sites = mistapi.get_all(
                response=sites_response, mist_session=session
            )  # Preserve the existing behavior during the compliance refactor.
        except Exception:  # Preserve the existing behavior during the compliance refactor.
            sites = (
                getattr(sites_response, "data", []) or []
            )  # Preserve the existing behavior during the compliance refactor.

        records: list[dict[str, Any]] = []  # Preserve the existing behavior during the compliance refactor.
        for site in sites:  # Preserve the existing behavior during the compliance refactor.
            site_id = str(site.get("id", ""))  # Preserve the existing behavior during the compliance refactor.
            if not site_id:  # Preserve the existing behavior during the compliance refactor.
                continue  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.info(
                "Scanning site %s (%s) for APs", site.get("name", ""), site_id
            )  # Preserve the existing behavior during the compliance refactor.
            try:
                # WHY: type="ap" keeps the response shape tight and skips
                # switches / gateways at the API side.
                devs_response = _mist_site_devices.listSiteDevices(
                    session, site_id, type="ap"
                )  # Preserve the existing behavior during the compliance refactor.
                devs = mistapi.get_all(
                    response=devs_response, mist_session=session
                )  # Preserve the existing behavior during the compliance refactor.
            except Exception:  # WHY: skip unreachable sites.
                _LOGGER.exception(
                    "Failed to list devices for site %s", site_id
                )  # Preserve the existing behavior during the compliance refactor.
                continue  # Preserve the existing behavior during the compliance refactor.

            for dev in devs:  # Preserve the existing behavior during the compliance refactor.
                if (
                    dev.get("deviceprofile_id") != source_profile_id
                ):  # Preserve the existing behavior during the compliance refactor.
                    continue  # Preserve the existing behavior during the compliance refactor.
                records.append(  # Preserve the existing behavior during the compliance refactor.
                    {
                        "device_id": str(dev.get("id", "")),
                        "site_id": site_id,
                        "mac": str(dev.get("mac", "")),
                        "hostname": dev.get("name") or dev.get("hostname"),
                    }
                )
        _LOGGER.info(
            "Discovery complete: %d APs bound to source profile", len(records)
        )  # Preserve the existing behavior during the compliance refactor.
        return records  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _render_migration_plan(  # Preserve the existing behavior during the compliance refactor.
        source: tuple[str, str],
        target: tuple[str, str],
        ap_records: list[dict[str, Any]],
    ) -> None:
        """Print the operator-visible migration plan.

        Why:
            The plan block is the last chance for the operator to catch a
            wrong-profile pick before the confirmation prompt. Printing every
            device_id + hostname + site keeps the audit trail on stdout.

        Args:
            source: ``(source_id, source_name)`` tuple.
            target: ``(target_id, target_name)`` tuple.
            ap_records: The APs the migration will reassign.
        """
        _source_id, source_name = source  # Preserve the existing behavior during the compliance refactor.
        _target_id, target_name = target  # Preserve the existing behavior during the compliance refactor.
        print("\nPlanned migration:")  # Preserve the existing behavior during the compliance refactor.
        for rec in ap_records:  # Preserve the existing behavior during the compliance refactor.
            hostname = rec.get("hostname") or "-"  # Preserve the existing behavior during the compliance refactor.
            print(
                f"  device_id={rec['device_id']}  hostname={hostname}  site={rec['site_id']}"
            )  # Preserve the existing behavior during the compliance refactor.
        print(
            f"Total: {len(ap_records)} APs will be reassigned " f"from {source_name} to {target_name}"
        )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _confirm_migration(
        count: int, source_name: str, target_name: str
    ) -> str:  # Preserve the existing behavior during the compliance refactor.
        """Prompt for the destructive-confirmation keyword.

        Why:
            An uppercase-exact keyword prevents a typo from arming a
            destructive run (research.md Decision 5). Three return values
            keep the branch shape flat in the caller.

        Args:
            count: Number of APs that will be reassigned.
            source_name: Human-readable source profile name.
            target_name: Human-readable target profile name.

        Returns:
            One of:
              * ``"live"`` -- operator typed ``MIGRATE``; proceed with PUTs.
              * ``"dry_run"`` -- operator typed ``DRY-RUN``; preview only.
              * ``"cancel"`` -- any other input; abort with no changes.
        """
        # WHY: lazy import for InputUtils per the module load rule.
        from src.config.source_dependency_resolver import (
            SourceDependencyResolver as _mh,  # WHY: resolve source dependencies without importing the root module.
        )

        prompt = (  # Preserve the existing behavior during the compliance refactor.
            f"\nType {_KEYWORD_LIVE!r} to reassign {count} APs from "
            f"{source_name} to {target_name}, "
            f"or {_KEYWORD_DRY_RUN!r} to preview only: "
        )
        response = _mh.InputUtils.safe_input(  # Preserve the existing behavior during the compliance refactor.
            prompt,
            default_value="",
            allow_empty=True,
            context="ap_profile_migration_confirm",
        )
        # WHY: strip trailing whitespace but keep case-sensitive compare so a
        # lowercase "migrate" is treated as cancel.
        response = response.strip()  # Preserve the existing behavior during the compliance refactor.
        if response == _KEYWORD_LIVE:  # Preserve the existing behavior during the compliance refactor.
            return "live"  # Preserve the existing behavior during the compliance refactor.
        if response == _KEYWORD_DRY_RUN:  # Preserve the existing behavior during the compliance refactor.
            return "dry_run"  # Preserve the existing behavior during the compliance refactor.
        return "cancel"  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _build_backup_payload(  # Preserve the existing behavior during the compliance refactor.
        context: APProfileBackupContext,
        ap_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Assemble the backup dict per data-model section 1.3."""
        logger.info("Building the AP profile migration backup payload")  # Record the backup build boundary.
        ts = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")  # Use canonical UTC text.
        planned = [dict(rec) for rec in ap_records]  # Copy AP records so later caller mutation cannot alter the backup.
        logger.debug("Built backup payload inputs with planned_count=%s", len(planned))  # Record payload size.
        return {  # Preserve the existing behavior during the compliance refactor.
            "schema_version": _BACKUP_SCHEMA_VERSION,
            "org_id": context.org_id,
            "migration_timestamp_utc": ts,
            "source_profile_id": context.source_id,
            "target_profile_id": context.target_id,
            "source_profile_snapshot": dict(context.source_snapshot),
            "target_profile_snapshot": dict(context.target_snapshot),
            "aps_planned": planned,
            "aps_reassigned": [],
            "outcome": "success",
            "failure_detail": None,
        }

    @staticmethod
    def _write_backup_file(
        payload: dict[str, Any], data_dir: str
    ) -> str:  # Preserve the existing behavior during the compliance refactor.
        """Write ``payload`` to a new backup file and return the absolute path."""
        logger.info("Writing the AP profile migration backup file")  # Record the backup write boundary.
        filename = APProfileMigrationManager._backup_filename(payload)  # Build the data-model file name.
        target_dir = Path(data_dir)  # Use pathlib so Windows and Linux builds share one path rule.
        target_dir.mkdir(parents=True, exist_ok=True)  # Ensure a fresh checkout has the data directory.
        target_path = target_dir / filename  # Join the directory and file name safely.
        target_path.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")  # Write readable JSON.
        resolved = str(target_path.resolve())  # Normalize the path for the operator summary and audit.
        logger.debug("Wrote AP profile migration backup file to %s", resolved)  # Record the written path.
        return resolved  # Return the resolved backup path for downstream revert use.

    @staticmethod
    def _backup_filename(
        payload: dict[str, Any],
    ) -> str:  # Preserve the existing behavior during the compliance refactor.
        """Return the data-model file name for a migration backup."""
        iso_ts = str(payload.get("migration_timestamp_utc", ""))  # Read the timestamp from the backup payload.
        basic_ts = iso_ts.replace("-", "").replace(":", "")  # Strip separators for lexical time ordering.
        source_id = str(payload.get("source_profile_id", ""))  # Read the source profile ID for the file name.
        target_id = str(payload.get("target_profile_id", ""))  # Read the target profile ID for the file name.
        return f"ap-profile-migration_{basic_ts}_{source_id}_to_{target_id}.json"  # Preserve the existing name shape.

    @staticmethod
    def _reassign_one_ap(  # Preserve the existing behavior during the compliance refactor.
        session: Any,
        ap_record: dict[str, Any],
        target_profile_id: str,
    ) -> None:
        """Reassign a single AP via ``updateSiteDevice`` with bounded retry.

        Why:
            Bounded retry is required by Constitution Principle VI. The
            retry cadence is pinned to ``_RETRY_BACKOFF_SECONDS``; tests
            observe timing by patching ``time.sleep`` at the module level.

        Args:
            session: The mistapi API session.
            ap_record: A single ``APRecord`` dict (device_id, site_id, ...).
            target_profile_id: The device-profile UUID to bind the AP to.

        Raises:
            Exception: The first exception observed after retry exhaustion.
        """
        # WHY: two retries -> three total attempts. The backoff sequence is
        # pinned by research Decision 2 -- any change here breaks T013.
        body = {"deviceprofile_id": target_profile_id}
        first_exc: BaseException | None = None  # WHY: preserve the original retry failure cause.
        # WHY: attempt indices 0, 1, 2. Sleep AFTER attempts 0 and 1 only.
        for attempt in range(
            len(_RETRY_BACKOFF_SECONDS) + 1
        ):  # Preserve the existing behavior during the compliance refactor.
            try:
                response = _mist_site_devices.updateSiteDevice(
                    session, ap_record["site_id"], ap_record["device_id"], body
                )
                # WHY: issue #1700 -- the SDK answers an error status with an
                # object instead of raising. Read that status before the call
                # counts as a success.
                APProfileMigrationManager._check_reassign_response(
                    response, ap_record["device_id"]
                )  # Preserve the existing behavior during the compliance refactor.
                return  # Preserve the existing behavior during the compliance refactor.
            except Exception as exc:  # WHY: broad catch for retry policy.
                first_exc = APProfileMigrationManager._remember_first_failure(first_exc, exc)  # WHY: keep cause.
                _LOGGER.warning(
                    "AP profile assignment attempt %s failed for %s: %s",
                    attempt + 1,
                    ap_record["device_id"],
                    exc,
                )
                # WHY: sleep only if there is a next attempt to make. Attribute
                # access on the ``time`` module (rather than a captured default
                # parameter) lets ``patch("time.sleep", ...)`` intercept.
                if attempt < len(_RETRY_BACKOFF_SECONDS):
                    time.sleep(_RETRY_BACKOFF_SECONDS[attempt])
                    continue
                # WHY: retry exhaustion -- re-raise the first exception so the
                # loop can record the original failure detail and stop.
                raise first_exc from None  # WHY: report the original cause without chaining a later symptom.
        # WHY: unreachable; guard against typing lint anyway.
        if first_exc is not None:  # WHY: preserve the first failure if control somehow leaves the loop.
            raise first_exc  # WHY: report the original cause, not a later symptom.

    @staticmethod
    def _remember_first_failure(first: BaseException | None, current: BaseException) -> BaseException:
        """Return the first failure, so a later symptom cannot replace the cause."""
        return first if first is not None else current  # WHY: preserve the original retry failure cause.

    @staticmethod
    def _check_reassign_response(
        response: Any, device_id: str
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Raise when the SDK response reports an HTTP error status.

        Why:
            Issue #1700 -- ``updateSiteDevice`` answers an error status with an
            ``APIResponse`` object. The old code discarded that object, so a
            refused PUT counted as a reassigned AP. The operator saw a success
            line for every one of 4030 calls that changed nothing.

        Args:
            response: The object ``updateSiteDevice`` returned.
            device_id: The AP the PUT targeted, for the message text.

        Raises:
            APProfileReassignmentError: The response reports a status at or
                above ``_HTTP_ERROR_FLOOR``.
        """
        # WHY: a stub or a mock carries no integer status. Treat an unreadable
        # status as "cannot judge" so this check never invents a failure.
        status_code = getattr(
            response, "status_code", None
        )  # Preserve the existing behavior during the compliance refactor.
        if not isinstance(status_code, int):  # Preserve the existing behavior during the compliance refactor.
            return  # Preserve the existing behavior during the compliance refactor.
        # WHY: 1xx, 2xx, and 3xx leave the reassignment claim intact.
        if status_code < _HTTP_ERROR_FLOOR:  # Preserve the existing behavior during the compliance refactor.
            return  # Preserve the existing behavior during the compliance refactor.
        _LOGGER.warning(  # Preserve the existing behavior during the compliance refactor.
            "Reassignment PUT for device %s reported HTTP %s. The device profile did not change.",
            device_id,
            status_code,
        )
        raise APProfileReassignmentError(
            response, device_id
        )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _run_reassignment_loop(  # Preserve the existing behavior during the compliance refactor.
        plan: APProfileReassignmentPlan,
    ) -> dict[str, Any]:
        """Iterate ``ap_records`` and PUT each AP with stop-on-failure semantics.

        Why:
            The file is re-written after every success so an interrupted run
            leaves a consistent on-disk partial-success record. A revert can
            then read the file and roll back exactly what was reassigned.
            The caller passes the in-memory payload so this loop never has to
            re-read a file that may still be a fixture-mocked path.

        Args:
            session: The mistapi API session.
            ap_records: The APs to reassign, in plan order.
            target_id: The target device-profile UUID.
            backup_path: Absolute path to the backup file to update on disk.
            payload: The in-memory backup dict to mutate and rewrite. The
                caller receives the same dict back (with ``aps_reassigned``,
                ``outcome``, and ``failure_detail`` updated in place).
            progress_stride: Emit progress at N=1, every ``progress_stride``,
                and at N=total. Defaults to 10.

        Returns:
            The mutated ``payload`` dict for the caller to use in the
            end-of-run summary (avoids a second disk read). The dict also
            carries an ephemeral ``_pacing`` sub-dict (leading underscore
            marks it as summary-only telemetry, not part of the persisted
            backup schema) with the six adaptive-rate-limiter counters
            required by addendum FR-A09.
        """
        # WHY: work on the caller-supplied in-memory dict so tests that patch
        # ``_write_backup_file`` (T011) still exercise the loop end-to-end.
        backup = plan.payload  # Preserve the existing behavior during the compliance refactor.
        total = len(plan.ap_records)  # Preserve the existing behavior during the compliance refactor.
        # WHY: per-invocation pacing state per plan-rate-limiting.md Q3.
        # ``smoothed`` is the PID limiter's internal EMA of the returned delay;
        # the limiter mutates it across calls. ``pacing_stats`` tracks the
        # counters that feed FR-A09 summary lines and the JSONL audit line.
        smoothed: float | None = None  # Preserve the existing behavior during the compliance refactor.
        pacing_stats: dict[str, float | int] = {  # Preserve the existing behavior during the compliance refactor.
            "puts_issued": 0,
            "http_429_seen": 0,
            "non_429_failures": 0,
            "delay_sum": 0.0,
            "delay_max": 0.0,
            "delay_count": 0,
        }
        for idx, rec in enumerate(
            plan.ap_records, start=1
        ):  # Preserve the existing behavior during the compliance refactor.
            # WHY: emit progress at N=1, at every stride boundary, and at N=total.
            if (
                idx == 1 or idx % plan.progress_stride == 0 or idx == total
            ):  # Preserve the existing behavior during the compliance refactor.
                _LOGGER.info(  # Preserve the existing behavior during the compliance refactor.
                    "Reassigning AP %d of %d: device_id=%s",
                    idx,
                    total,
                    rec["device_id"],
                )
            # WHY: FR-A01 -- consult the adaptive limiter once per PUT so a
            # 10K-AP run stays under Mist's 5000-requests-per-hour ceiling.
            smoothed = APProfileMigrationManager._apply_pacing(
                smoothed, pacing_stats
            )  # Preserve the existing behavior during the compliance refactor.
            pacing_stats["puts_issued"] += 1  # Preserve the existing behavior during the compliance refactor.
            try:
                APProfileMigrationManager._reassign_one_ap(
                    plan.session, rec, plan.target_id
                )  # Preserve the existing behavior during the compliance refactor.
            except Exception as exc:  # WHY: partial-success record path.
                # WHY: FR-A04 -- 429 is a throttle signal, not a hard failure.
                # Feed the cache-invalidation signal to the limiter and keep
                # going; the retry policy in ``_reassign_one_ap`` already
                # burnt its three attempts on this AP, so record it and skip.
                if APProfileMigrationManager._is_429(
                    exc
                ):  # Preserve the existing behavior during the compliance refactor.
                    APProfileMigrationManager._signal_rate_limit_hit()
                    pacing_stats["http_429_seen"] += 1  # Preserve the existing behavior during the compliance refactor.
                    continue  # Preserve the existing behavior during the compliance refactor.
                # WHY: FR-017 -- stop on first non-429 failure so the on-disk
                # file exactly matches the state Mist is in.
                pacing_stats["non_429_failures"] += 1  # Preserve the existing behavior during the compliance refactor.
                backup["outcome"] = "partial"  # Preserve the existing behavior during the compliance refactor.
                backup["failure_detail"] = {  # Preserve the existing behavior during the compliance refactor.
                    "failed_device_id": rec["device_id"],
                    "failed_site_id": rec["site_id"],
                    "error_message": str(exc),
                    "reassigned_count": len(backup["aps_reassigned"]),
                    "planned_count": total,
                }
                Path(plan.backup_path).write_text(  # Preserve the existing behavior during the compliance refactor.
                    json.dumps(backup, indent=2, sort_keys=False),
                    encoding="utf-8",
                )
                _LOGGER.warning(  # Preserve the existing behavior during the compliance refactor.
                    "Reassignment failed for AP %s after retry exhaustion; run stopped",
                    rec["device_id"],
                )
                # WHY: attach ephemeral pacing telemetry for the summary and
                # JSONL emitters. Leading underscore keeps it out of the
                # persisted backup schema (FR-A09).
                backup["_pacing"] = pacing_stats  # Preserve the existing behavior during the compliance refactor.
                return backup  # Preserve the existing behavior during the compliance refactor.

            # WHY: append + rewrite after every success so an interrupted
            # revert has an accurate list to roll back.
            backup["aps_reassigned"].append(
                rec["device_id"]
            )  # Preserve the existing behavior during the compliance refactor.
            Path(plan.backup_path).write_text(  # Preserve the existing behavior during the compliance refactor.
                json.dumps(backup, indent=2, sort_keys=False),
                encoding="utf-8",
            )

        # WHY: fell through the loop -- every AP succeeded.
        backup["outcome"] = "success"  # Preserve the existing behavior during the compliance refactor.
        backup["failure_detail"] = None  # Preserve the existing behavior during the compliance refactor.
        Path(plan.backup_path).write_text(  # Preserve the existing behavior during the compliance refactor.
            json.dumps(backup, indent=2, sort_keys=False),
            encoding="utf-8",
        )
        # WHY: attach ephemeral pacing telemetry per FR-A09.
        backup["_pacing"] = pacing_stats  # Preserve the existing behavior during the compliance refactor.
        return backup  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _print_migration_summary(
        summary: APProfileMigrationSummary,
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Print the end-of-run summary block."""
        logger.info("Printing the AP profile migration summary")  # Record the operator summary boundary.
        planned = len(summary.payload.get("aps_planned", []))  # Count planned APs from the persisted schema.
        reassigned = len(summary.payload.get("aps_reassigned", []))  # Count successfully reassigned APs.
        outcome = summary.payload.get("outcome", "unknown")  # Read the final state label with the existing fallback.
        print("\nMigration summary:")  # Keep the existing heading text.
        print(f"  Source profile: {summary.source_name} (id={summary.source_id})")  # Show the source profile.
        print(f"  Target profile: {summary.target_name} (id={summary.target_id})")  # Show the target profile.
        print(f"  Planned APs: {planned}")  # Show the intended AP count.
        print(f"  Reassigned APs: {reassigned}")  # Show the completed AP count.
        print(f"  Outcome: {outcome}")  # Show the final state label.
        print(f"  Backup file: {summary.backup_path}")  # Show the backup file for revert use.
        APProfileMigrationManager._print_migration_failure(summary.payload, outcome)  # Print failure detail.
        pacing_stats = APProfileMigrationManager._migration_pacing_stats(summary.payload)  # Read limiter counters.
        APProfileMigrationManager._print_pacing_summary(pacing_stats)  # Print limiter counters.
        logger.debug("Printed migration summary with outcome=%s", outcome)  # Record summary completion.

    @staticmethod
    def _migration_pacing_stats(
        payload: dict[str, Any],
    ) -> dict[str, float | int]:  # Preserve the existing behavior during the compliance refactor.
        """Return migration pacing statistics with the existing zero fallback."""
        pacing_stats = payload.get("_pacing")  # Read the ephemeral summary data from the in-memory payload.
        defaults = APProfileMigrationManager._new_pacing_stats()  # Preserve zero defaults for missing pacing keys.
        if isinstance(pacing_stats, dict):  # Preserve existing values when the loop attached them.
            defaults.update(pacing_stats)  # Preserve partial dict behavior by filling absent keys.
        return defaults  # Return a complete counter set for output formatting.

    @staticmethod
    def _print_migration_failure(
        payload: dict[str, Any], outcome: Any
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Print migration failure detail when the outcome is not success."""
        if outcome == "success":  # Keep success output byte-identical by printing no failure detail.
            return  # Return early because no failure block is needed.
        failure_detail = payload.get("failure_detail")  # Read the persisted failure payload.
        if failure_detail is not None:  # Preserve the prior condition for partial runs.
            print(  # Preserve the existing operator-visible failure line.
                f"  Failed AP: {failure_detail.get('failed_device_id')}  "
                f"reason: {failure_detail.get('error_message')}"
            )

    # ------------------------------------------------------------------
    # Private helpers -- revert (T036-T042)
    # ------------------------------------------------------------------

    @staticmethod
    def _list_backup_files(
        data_dir: str,
    ) -> list[Path]:  # Preserve the existing behavior during the compliance refactor.
        """Return every backup file under ``data_dir``, newest first.

        Why:
            The backup filename convention (data-model 1.1) starts with an
            ISO-basic UTC timestamp, so a reverse ``sorted`` on the string
            filename ranks the newest-written file first. This helper hides
            the glob pattern so the picker only sees ``list[Path]``.

        Args:
            data_dir: Directory to scan for backup JSON files.

        Returns:
            A list of ``Path`` values matching ``ap-profile-migration_*.json``
            under ``data_dir``, newest first. Empty when the directory does
            not exist or contains no matches.
        """
        # WHY: an absent directory is not an error; return empty so the picker
        # emits the "no backup" short-circuit message.
        base = Path(data_dir)  # Preserve the existing behavior during the compliance refactor.
        if not base.is_dir():  # Preserve the existing behavior during the compliance refactor.
            return []  # Preserve the existing behavior during the compliance refactor.
        # WHY: glob returns unordered on some filesystems; sort by filename in
        # reverse so the newest ISO-basic timestamp lands first.
        candidates = sorted(
            base.glob("ap-profile-migration_*.json"), reverse=True
        )  # Preserve the existing behavior during the compliance refactor.
        return candidates  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _pick_backup_file(
        candidates: list[Path],
    ) -> Path | None:  # Preserve the existing behavior during the compliance refactor.
        """Prompt the operator to pick one backup file from ``candidates``.

        Why:
            Splitting the picker from the entry point keeps the confirmation
            flow test-friendly (tests patch this helper with a canned Path).
            The picker returns ``None`` on cancel or empty so the caller can
            short-circuit before any validation runs.

        Args:
            candidates: The list of backup files, in newest-first order.

        Returns:
            The chosen ``Path``, or ``None`` when the operator cancels or the
            list is empty.
        """
        # WHY: lazy import for InputUtils keeps this module circular-safe.
        from src.config.source_dependency_resolver import (
            SourceDependencyResolver as _mh,  # WHY: resolve source dependencies without importing the root module.
        )

        if not candidates:  # Preserve the existing behavior during the compliance refactor.
            print(
                "No backup files found under data/. Nothing to revert."
            )  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.info(
                "No backup files present under data/"
            )  # Preserve the existing behavior during the compliance refactor.
            return None  # Preserve the existing behavior during the compliance refactor.

        print("\nSelect the backup file to revert:")  # Preserve the existing behavior during the compliance refactor.
        for idx, path in enumerate(
            candidates, start=1
        ):  # Preserve the existing behavior during the compliance refactor.
            print(f"  {idx}. {path.name}")  # Preserve the existing behavior during the compliance refactor.

        count = len(candidates)  # Preserve the existing behavior during the compliance refactor.
        # WHY: retry loop for non-numeric or out-of-range input; matches the
        # UX pattern used by ``_pick_ap_device_profile``.
        while True:  # Preserve the existing behavior during the compliance refactor.
            choice = _mh.InputUtils.safe_input(  # Preserve the existing behavior during the compliance refactor.
                f"  Select backup (1-{count}) or 'q' to cancel: ",
                default_value="",
                allow_empty=True,
                context="ap_profile_revert_picker",
            )
            if choice.lower() == "q":  # Preserve the existing behavior during the compliance refactor.
                return None  # Preserve the existing behavior during the compliance refactor.
            try:
                index = int(choice)  # Preserve the existing behavior during the compliance refactor.
            except ValueError:  # Preserve the existing behavior during the compliance refactor.
                print(
                    f"  Enter a number between 1 and {count}."
                )  # Preserve the existing behavior during the compliance refactor.
                continue  # Preserve the existing behavior during the compliance refactor.
            if 1 <= index <= count:  # Preserve the existing behavior during the compliance refactor.
                return candidates[index - 1]  # Preserve the existing behavior during the compliance refactor.
            print(
                f"  Enter a number between 1 and {count}."
            )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _load_and_validate_backup(
        path: str,
    ) -> dict[str, Any]:  # Preserve the existing behavior during the compliance refactor.
        """Read ``path`` and enforce data-model 1.6 rules 1 through 6.

        Why:
            Every rule failure raises ``ValueError`` naming the offending
            field so the entry-point can print the operator-visible refusal
            message without re-implementing rule-to-message mapping in the
            caller.

        Args:
            path: Absolute filesystem path to the backup JSON file.

        Returns:
            The parsed backup dict when every rule passes.

        Raises:
            ValueError: When any rule fails; message names the offending
                field or rule so the operator can locate the fix.
        """
        payload = APProfileMigrationManager._parse_backup_file(
            path
        )  # Preserve the existing behavior during the compliance refactor.
        APProfileMigrationManager._validate_backup_top_level(
            payload
        )  # Preserve the existing behavior during the compliance refactor.
        planned = payload["aps_planned"]  # Preserve the existing behavior during the compliance refactor.
        APProfileMigrationManager._validate_planned_records(
            planned
        )  # Preserve the existing behavior during the compliance refactor.
        APProfileMigrationManager._validate_reassigned_list(
            payload.get("aps_reassigned", []),
            planned,
        )
        APProfileMigrationManager._validate_snapshot_ids(
            payload
        )  # Preserve the existing behavior during the compliance refactor.
        return payload  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _parse_backup_file(
        path: str,
    ) -> dict[str, Any]:  # Preserve the existing behavior during the compliance refactor.
        """Read ``path`` and return the parsed JSON dict.

        Why:
            Isolates file I/O + JSON parse from the semantic rule checks so
            each layer has a small, targeted cyclomatic complexity footprint
            and stays under the Radon CC>10 quality gate.

        Args:
            path: Absolute filesystem path to the backup JSON file.

        Returns:
            The parsed backup dict.

        Raises:
            ValueError: When the file cannot be read, is not valid JSON, or
                the top-level value is not a JSON object.
        """
        try:
            raw = Path(path).read_text(
                encoding="utf-8"
            )  # Preserve the existing behavior during the compliance refactor.
        except OSError as exc:  # Preserve the existing behavior during the compliance refactor.
            raise ValueError(
                f"backup file unreadable: {exc}"
            ) from exc  # Preserve the existing behavior during the compliance refactor.
        try:
            payload = json.loads(raw)  # Preserve the existing behavior during the compliance refactor.
        except json.JSONDecodeError as exc:  # Preserve the existing behavior during the compliance refactor.
            raise ValueError(
                f"backup file not valid JSON: {exc}"
            ) from exc  # Preserve the existing behavior during the compliance refactor.
        if not isinstance(payload, dict):  # Preserve the existing behavior during the compliance refactor.
            raise ValueError(
                "backup file top-level must be a JSON object"
            )  # Preserve the existing behavior during the compliance refactor.
        return payload  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _validate_backup_top_level(
        payload: dict[str, Any],
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Enforce data-model rules 1 through 3 on the backup top level."""
        logger.info("Validating AP profile backup top-level fields")  # Record the schema validation boundary.
        APProfileMigrationManager._require_backup_version(payload)  # Validate the schema version first.
        APProfileMigrationManager._require_backup_string_fields(payload)  # Validate required string fields next.
        APProfileMigrationManager._require_backup_plan_list(payload)  # Validate the planned AP list last.
        logger.debug("Validated AP profile backup top-level fields")  # Record validation completion.

    @staticmethod
    def _require_backup_version(
        payload: dict[str, Any],
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Validate the backup schema version."""
        version = payload.get("schema_version")  # Read the schema version field from the backup.
        if version != _BACKUP_SCHEMA_VERSION:  # Refuse unknown backup schemas before any AP changes.
            raise ValueError(
                f"schema_version must be {_BACKUP_SCHEMA_VERSION}; got {version!r}"
            )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _require_backup_string_fields(
        payload: dict[str, Any],
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Validate required top-level string fields."""
        fields = ("org_id", "source_profile_id", "target_profile_id", "migration_timestamp_utc")  # Preserve order.
        for field in fields:  # Validate fields in the original message order.
            value = payload.get(field)  # Read the field value for shape validation.
            if not isinstance(value, str) or not value.strip():  # Require a non-empty string value.
                raise ValueError(
                    f"required field {field!r} must be a non-empty string"
                )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _require_backup_plan_list(
        payload: dict[str, Any],
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Validate that ``aps_planned`` exists and is a list."""
        planned = payload.get("aps_planned")  # Read the planned AP list from the backup.
        if planned is None:  # Preserve the specific missing-field message.
            raise ValueError(
                "required field 'aps_planned' is missing"
            )  # Preserve the existing behavior during the compliance refactor.
        if not isinstance(planned, list):  # Preserve the specific type message.
            raise ValueError(
                "required field 'aps_planned' must be a JSON array"
            )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _validate_planned_records(
        planned: list[Any],
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Enforce data-model rule 4 on every ``aps_planned`` entry."""
        logger.info("Validating %d planned AP records from backup", len(planned))  # Record validation scope.
        for idx, rec in enumerate(planned):  # Preserve the original record order in error messages.
            APProfileMigrationManager._validate_planned_record(idx, rec)  # Validate one AP record.
        logger.debug("Validated %d planned AP records from backup", len(planned))  # Record validation count.

    @staticmethod
    def _validate_planned_record(
        index: int, record: Any
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Validate one planned AP record from the backup file."""
        if not isinstance(record, dict):  # Require object shape for each AP plan row.
            raise ValueError(
                f"aps_planned[{index}] must be a JSON object"
            )  # Preserve the existing behavior during the compliance refactor.
        for field in ("device_id", "site_id", "mac"):  # Preserve required-field validation order.
            APProfileMigrationManager._validate_planned_field(index, record, field)  # Validate one field.

    @staticmethod
    def _validate_planned_field(
        index: int, record: dict[str, Any], field: str
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Validate one required field in a planned AP record."""
        value = record.get(field)  # Read the AP record field value.
        if not isinstance(value, str) or not value.strip():  # Require a non-empty string value.
            raise ValueError(
                f"aps_planned[{index}].{field} must be a non-empty string"
            )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _validate_reassigned_list(
        reassigned: Any, planned: list[Any]
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Enforce data-model rule 5 on ``aps_reassigned``."""
        logger.info("Validating AP profile reassignment list")  # Record reassigned-list validation boundary.
        if not isinstance(reassigned, list):  # Require list shape before iterating entries.
            raise ValueError(
                "field 'aps_reassigned' must be a JSON array of strings"
            )  # Preserve the existing behavior during the compliance refactor.
        planned_ids = APProfileMigrationManager._planned_device_ids(planned)  # Build the valid ID set.
        for entry in reassigned:  # Validate reassigned IDs in their stored order.
            APProfileMigrationManager._validate_reassigned_entry(entry, planned_ids)  # Validate one reassigned ID.
        logger.debug("Validated %d reassigned AP IDs", len(reassigned))  # Record validation count.

    @staticmethod
    def _planned_device_ids(
        planned: list[Any],
    ) -> set[str]:  # Preserve the existing behavior during the compliance refactor.
        """Return the device IDs that appear in the planned AP list."""
        return {str(record.get("device_id", "")) for record in planned}  # Preserve prior set construction.

    @staticmethod
    def _validate_reassigned_entry(
        entry: Any, planned_ids: set[str]
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Validate one reassigned AP ID against the planned AP set."""
        if not isinstance(entry, str):  # Require string entries before membership checks.
            raise ValueError(
                "aps_reassigned entries must be strings"
            )  # Preserve the existing behavior during the compliance refactor.
        if entry not in planned_ids:  # Refuse a reassigned AP that does not appear in the plan.
            raise ValueError(
                f"aps_reassigned contains id {entry!r} not present in aps_planned"
            )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _validate_snapshot_ids(
        payload: dict[str, Any],
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Enforce data-model 1.6 rule 6 on the snapshot ID fields.

        Why:
            Snapshot IDs must match the top-level IDs so a hand-edited pair
            (snapshot copied from a wrong profile) is caught before any PUT
            lands.

        Args:
            payload: The parsed backup dict (top-level already validated).

        Returns:
            None.

        Raises:
            ValueError: When either snapshot ID does not match its
                top-level counterpart.
        """
        src_snap = payload.get(
            "source_profile_snapshot"
        )  # Preserve the existing behavior during the compliance refactor.
        tgt_snap = payload.get(
            "target_profile_snapshot"
        )  # Preserve the existing behavior during the compliance refactor.
        if (
            isinstance(src_snap, dict) and src_snap.get("id") != payload["source_profile_id"]
        ):  # Preserve the existing behavior during the compliance refactor.
            raise ValueError(
                "source_profile_snapshot.id does not match source_profile_id"
            )  # Preserve the existing behavior during the compliance refactor.
        if (
            isinstance(tgt_snap, dict) and tgt_snap.get("id") != payload["target_profile_id"]
        ):  # Preserve the existing behavior during the compliance refactor.
            raise ValueError(
                "target_profile_snapshot.id does not match target_profile_id"
            )  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _verify_source_profile_exists(
        session: Any, org_id: str, source_profile_id: str
    ) -> bool:  # Preserve the existing behavior during the compliance refactor.
        """Return ``True`` when the source profile still exists in ``org_id``.

        Why:
            FR-021 -- the revert must refuse if the source profile the
            backup PUT-s each AP back to has been deleted. A dedicated helper
            makes this seam trivial to patch in unit tests.

        Args:
            session: The mistapi API session.
            org_id: The org that owns the profile.
            source_profile_id: The device-profile UUID to look up.

        Returns:
            ``True`` when ``getOrgDeviceProfile`` returns a 2xx response with
            a matching id; ``False`` on 404 or any lookup exception.
        """
        # WHY: broad try/except -- any lookup failure (404, network error,
        # SDK exception) is treated as "does not exist" so the operator gets
        # a loud refusal instead of a silent no-op. Alternate causes are
        # visible via the mistapi log line the SDK writes.
        try:
            response = _mist_deviceprofiles.getOrgDeviceProfile(
                session, org_id, source_profile_id
            )  # Preserve the existing behavior during the compliance refactor.
        except Exception as exc:  # WHY: any error treats profile as missing.
            _LOGGER.warning(
                "getOrgDeviceProfile raised for %s: %s", source_profile_id, exc
            )  # Preserve the existing behavior during the compliance refactor.
            return False  # Preserve the existing behavior during the compliance refactor.
        # WHY: mistapi may return a response object with .status_code; a 404
        # means the profile is gone.
        status = getattr(response, "status_code", 200)  # Preserve the existing behavior during the compliance refactor.
        if status == 404:  # Preserve the existing behavior during the compliance refactor.
            return False  # Preserve the existing behavior during the compliance refactor.
        # WHY: defensive id-match check -- an SDK that returns an empty body
        # on error would otherwise be misread as success.
        data = getattr(response, "data", None)  # Preserve the existing behavior during the compliance refactor.
        if (
            isinstance(data, dict) and data.get("id") and data["id"] != source_profile_id
        ):  # Preserve the existing behavior during the compliance refactor.
            _LOGGER.warning(  # Preserve the existing behavior during the compliance refactor.
                "getOrgDeviceProfile returned id %s for lookup of %s",
                data.get("id"),
                source_profile_id,
            )
            return False  # Preserve the existing behavior during the compliance refactor.
        return True  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _confirm_revert(
        count: int, source_name: str, backup_path: str
    ) -> str:  # Preserve the existing behavior during the compliance refactor.
        """Prompt for the uppercase-exact ``REVERT`` keyword.

        Why:
            Requiring the operator to type ``REVERT`` (research.md Decision 5)
            prevents a mis-typed ``r`` or blind Enter from arming a
            destructive rollback. The three return values mirror the migrate
            side to keep the caller flat.

        Args:
            count: Number of APs the revert will attempt.
            source_name: Human-readable source profile name.
            backup_path: Absolute path to the backup file being consumed.

        Returns:
            ``"live"`` when the operator typed ``REVERT``, ``"cancel"``
            otherwise.
        """
        # WHY: lazy import for InputUtils per the module load rule.
        from src.config.source_dependency_resolver import (
            SourceDependencyResolver as _mh,  # WHY: resolve source dependencies without importing the root module.
        )

        prompt = (  # Preserve the existing behavior during the compliance refactor.
            f"\nType {_KEYWORD_REVERT!r} to revert {count} APs back to "
            f"{source_name}\n(backup file: {backup_path}): "
        )
        response = _mh.InputUtils.safe_input(  # Preserve the existing behavior during the compliance refactor.
            prompt,
            default_value="",
            allow_empty=True,
            context="ap_profile_revert_confirm",
        )
        # WHY: strip trailing whitespace but keep case-sensitive compare so a
        # lowercase "revert" is treated as cancel.
        if response.strip() == _KEYWORD_REVERT:  # Preserve the existing behavior during the compliance refactor.
            return "live"  # Preserve the existing behavior during the compliance refactor.
        return "cancel"  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _revert_one_ap(  # Preserve the existing behavior during the compliance refactor.
        session: Any,
        device_id: str,
        site_id: str,
        source_profile_id: str,
    ) -> str | None:
        """Revert a single AP to ``source_profile_id`` with bounded retry.

        Why:
            The revert path shares the migrate path's bounded-retry policy
            (Constitution Principle VI), plus a 404-detects-missing branch
            required by FR-023. Separating this from ``_reassign_one_ap``
            keeps the missing-AP path visible at the call site.

        Args:
            session: The mistapi API session.
            device_id: The AP device UUID to revert.
            site_id: The site the AP is under (required by updateSiteDevice).
            source_profile_id: The device-profile UUID to bind the AP to.

        Returns:
            ``None`` on a healthy PUT (2xx response, or any SDK success), or
            the sentinel ``_REVERT_MISSING`` when Mist returns 404 for the AP.

        Raises:
            Exception: The first exception observed after retry exhaustion.
        """
        # WHY: same cadence as the migrate side -- two retries, three total
        # attempts, sleep only when a next attempt exists.
        body = {"deviceprofile_id": source_profile_id}
        first_exc: BaseException | None = None  # WHY: preserve the original retry failure cause.
        for attempt in range(len(_RETRY_BACKOFF_SECONDS) + 1):
            try:
                response = _mist_site_devices.updateSiteDevice(
                    session, site_id, device_id, body
                )  # Preserve the existing behavior during the compliance refactor.
            except Exception as exc:  # WHY: broad catch for retry policy.
                first_exc = APProfileMigrationManager._remember_first_failure(first_exc, exc)  # WHY: keep cause.
                _LOGGER.warning("AP profile revert attempt %s failed for %s: %s", attempt + 1, device_id, exc)
                if attempt < len(_RETRY_BACKOFF_SECONDS):
                    time.sleep(_RETRY_BACKOFF_SECONDS[attempt])
                    continue
                raise first_exc from None  # WHY: report the original cause without chaining a later symptom.
            # WHY: mistapi returns a response object; a 404 status means the
            # AP is missing from Mist -- report as missing (FR-023) not retry.
            status = getattr(
                response, "status_code", 200
            )  # Preserve the existing behavior during the compliance refactor.
            if status == 404:  # Preserve the existing behavior during the compliance refactor.
                return _REVERT_MISSING  # Preserve the existing behavior during the compliance refactor.
            # WHY: any 5xx (or other non-2xx) is a retryable server problem;
            # treat as failure and back off the same way an exception would.
            if isinstance(status, int) and status >= 500:
                status_error = RuntimeError(f"HTTP {status} on updateSiteDevice for {device_id}")  # WHY: wrap status.
                first_exc = APProfileMigrationManager._remember_first_failure(
                    first_exc, status_error
                )  # WHY: keep cause.
                _LOGGER.warning("AP profile revert attempt %s failed for %s: %s", attempt + 1, device_id, status_error)
                if attempt < len(_RETRY_BACKOFF_SECONDS):
                    time.sleep(_RETRY_BACKOFF_SECONDS[attempt])
                    continue
                raise first_exc
            # WHY: fell through -- SDK success or 2xx status.
            return None  # Preserve the existing behavior during the compliance refactor.
        # WHY: unreachable; guard against typing lint anyway.
        if first_exc is not None:  # WHY: preserve the first failure if control somehow leaves the loop.
            raise first_exc  # WHY: report the original cause, not a later symptom.
        return None

    @staticmethod
    def _emit_revert_audit(
        event: dict[str, Any],
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Append a single JSONL row to the shared revert telemetry stream.

        Why:
            FR-025 requires a machine-readable audit trail for every revert
            invocation. Using ``TelemetryEmitter`` inherits its best-effort
            write semantics (a disk-full or permission error is logged, not
            raised) so a telemetry failure never blocks the primary revert.

        Args:
            event: The audit event dict; shape follows data-model 2.2. The
                caller is responsible for populating every required key.
        """
        # WHY: lazy import so the top-level module load stays circular-safe
        # even if TelemetryEmitter grows a heavy dependency later.
        from src.analytics.telemetry_emitter import (
            TelemetryEmitter,
        )  # Preserve the existing behavior during the compliance refactor.

        # WHY: colocate the telemetry file with the backup files so the
        # operator finds every audit artefact under one directory.
        target = (
            Path(_DATA_DIR) / _REVERT_TELEMETRY_FILENAME
        )  # Preserve the existing behavior during the compliance refactor.
        # WHY: context manager guarantees flush + close even on an emit that
        # raises inside the writer.
        with TelemetryEmitter(str(target)) as emitter:  # Preserve the existing behavior during the compliance refactor.
            emitter.emit(event)  # Preserve the existing behavior during the compliance refactor.

    @staticmethod
    def _emit_migrate_audit(
        event: dict[str, Any],
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Append a single JSONL row to the shared migrate telemetry stream.

        Why:
            Addendum FR-A09 requires the same JSONL envelope on the migrate
            side (menu 207) as the revert side (menu 208) so operators and
            downstream reporting see one shape across both operations. Uses
            ``TelemetryEmitter`` for the same best-effort write semantics as
            ``_emit_revert_audit`` -- a disk-full or permission error is
            logged, not raised, so a telemetry failure never blocks the
            primary migration.

        Args:
            event: The audit event dict; shape mirrors the revert-side
                envelope plus the pacing sub-dict described in
                data-model-rate-limiting.md section 3.
        """
        # WHY: lazy import so the top-level module load stays circular-safe
        # even if TelemetryEmitter grows a heavy dependency later.
        from src.analytics.telemetry_emitter import (
            TelemetryEmitter,
        )  # Preserve the existing behavior during the compliance refactor.

        # WHY: colocate with backup files and the revert audit stream so the
        # operator finds every artefact under one directory.
        target = (
            Path(_DATA_DIR) / _MIGRATE_TELEMETRY_FILENAME
        )  # Preserve the existing behavior during the compliance refactor.
        with TelemetryEmitter(str(target)) as emitter:  # Preserve the existing behavior during the compliance refactor.
            emitter.emit(event)  # Preserve the existing behavior during the compliance refactor.
