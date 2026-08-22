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
from __future__ import annotations

# WHY: bounded retry backoff and progress-time seams live in stdlib only per the
# no-new-dependency constraint from plan.md.
import json  # WHY: backup file writes and loads use only stdlib json.
import logging  # WHY: progress + destructive-run WARNING land on the module logger.
import time  # WHY: default sleeper for the bounded retry seam.
from datetime import UTC, datetime  # WHY: UTC-normalized backup timestamps.
from pathlib import Path  # WHY: portable filesystem joins for the backup file path.
from typing import Any

# WHY: importing the mistapi sub-modules at module load lets tests monkey-patch
# them via ``patch("mistapi.api.v1.sites.devices.updateSiteDevice", ...)``.
import mistapi  # noqa: F401  # WHY: kept for get_all() pagination in production paths.
from mistapi.api.v1.orgs import deviceprofiles as _mist_deviceprofiles  # WHY: profile picker + snapshot fetcher.
from mistapi.api.v1.orgs import sites as _mist_orgs_sites  # WHY: org-wide site enumeration.
from mistapi.api.v1.sites import devices as _mist_site_devices  # WHY: per-site AP listing + updateSiteDevice PUT.

# WHY: module logger uses the dotted module path so operators can filter by
# ``src.device.ap_profile_migration_manager`` in the shared MistHelper logs.
_LOGGER = logging.getLogger(__name__)

# WHY: retry cadence pinned by research.md Decision 2. Two retries -> three total
# attempts; a change here MUST be reflected in the T013 test assertion.
_RETRY_BACKOFF_SECONDS: tuple[float, ...] = (0.5, 1.0)

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
_BACKUP_SCHEMA_VERSION = 1

# WHY: progress cadence pinned by research.md Decision 3 -- print at N=1, every
# _PROGRESS_STRIDE, and at N=total. T015 locks the stride at 10.
_PROGRESS_STRIDE = 10

# WHY: default directory for backup files. The test fixture monkey-patches this
# to a tmp_path/data so a unit test never scribbles under the repo data/ dir.
_DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")

# WHY: confirmation keywords per research.md Decision 5 -- uppercase-exact
# strings so a typo cannot silently arm a destructive run.
_KEYWORD_LIVE = "MIGRATE"
_KEYWORD_DRY_RUN = "DRY-RUN"
_KEYWORD_REVERT = "REVERT"

# WHY: telemetry file name for the JSONL audit stream (data-model 2.1). Kept as
# a module constant so tests and production point at the same relative path.
_REVERT_TELEMETRY_FILENAME = "ap_profile_migration_revert.jsonl"

# WHY: migrate-side JSONL audit stream (addendum FR-A09, TR032). Distinct
# filename so operators can grep menu-207 runs separately from menu-208 runs.
_MIGRATE_TELEMETRY_FILENAME = "ap_profile_migration_migrate.jsonl"

# WHY: sentinel return value from ``_revert_one_ap`` when the AP has been
# deleted from Mist since the migration (data-model 2.2 -- ``missing_count``).
_REVERT_MISSING = "missing"

# WHY: the mistapi SDK returns an APIResponse for an error status. It does not
# raise. Any status at or above this floor means the PUT changed nothing.
_HTTP_ERROR_FLOOR = 400


class APProfileReassignmentError(RuntimeError):
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

    def __init__(self, response: Any, device_id: str) -> None:
        """Build the error from the SDK response and the AP that failed.

        Args:
            response: The object ``updateSiteDevice`` returned.
            device_id: The AP the PUT targeted, for the operator-facing text.
        """
        # WHY: _is_429 reads err.response.status_code. Keeping the original
        # object here lets the existing pacing path see a 429 answer.
        self.response = response
        # WHY: cached so a caller reads the status without a second getattr.
        self.status_code = getattr(response, "status_code", None)
        super().__init__(f"updateSiteDevice reported HTTP {self.status_code} for device {device_id}")


def _utc_iso_timestamp() -> str:
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
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


class APProfileMigrationManager:
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
    def migrate_aps_between_device_profiles(session: Any | None = None) -> None:
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
        import MistHelper as _mh  # noqa: PLC0415  # WHY: call-time only.

        # WHY: resolve org context via the shared cached-or-prompted helper.
        org_id = _mh.ConfigUtils.get_cached_or_prompted_org_id()
        # WHY: fall back to the ambient MistHelper apisession when the caller
        # did not pass one -- matches the menu-206 wiring pattern.
        mist_session = session if session is not None else _mh.apisession

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
        if source_id == target_id:
            print(  # noqa: T201
                "Error: source and target device profiles are the same. " "Select two different profiles.",
            )
            _LOGGER.warning("Refused: source and target profiles are identical (id=%s)", source_id)
            return

        # WHY: AP-discovery walk -- one pass across every site in the org.
        ap_records = APProfileMigrationManager._discover_aps_on_source_profile(mist_session, org_id, source_id)

        # WHY: FR-010 -- empty source is not a failure; print the exact
        # short-circuit message and return before writing any file.
        if not ap_records:
            print("No APs bound to source profile. Nothing to migrate.")  # noqa: T201
            _LOGGER.info("Nothing to migrate: source profile %s has zero APs", source_id)
            return

        # WHY: render the operator-visible plan before the confirmation prompt
        # so the operator sees exactly which APs will move.
        APProfileMigrationManager._render_migration_plan((source_id, source_name), (target_id, target_name), ap_records)

        # WHY: guarded confirmation -- accepts MIGRATE (live) or DRY-RUN (preview).
        decision = APProfileMigrationManager._confirm_migration(len(ap_records), source_name, target_name)
        if decision == "cancel":
            print("Migration cancelled.")  # noqa: T201
            _LOGGER.info("Cancelled by operator at confirmation prompt")
            return
        if decision == "dry_run":
            # WHY: FR-015 -- dry-run writes no file and issues no PUT. Return
            # immediately so no backup or PUT side effect occurs.
            print("Dry run: no changes made")  # noqa: T201
            _LOGGER.info("Dry-run selected; no backup and no PUT will be issued")
            return

        # WHY: build the backup payload BEFORE any PUT so the on-disk file is
        # the single source of truth if the run is interrupted (FR-011).
        payload = APProfileMigrationManager._build_backup_payload(
            org_id, source_id, source_snapshot, target_id, target_snapshot, ap_records
        )
        backup_path = APProfileMigrationManager._write_backup_file(payload, _DATA_DIR)
        _LOGGER.info("Backup file written: %s", backup_path)

        # WHY: the loop mutates the on-disk backup after each success so an
        # interrupted run leaves the file in a consistent partial state. The
        # in-memory ``payload`` dict is mutated in place; the returned value
        # is the same object -- kept explicit for readability.
        final_payload = APProfileMigrationManager._run_reassignment_loop(
            mist_session,
            ap_records,
            target_id,
            backup_path,
            payload,
            progress_stride=_PROGRESS_STRIDE,
        )

        # WHY: use the in-memory final payload for the summary print so we
        # never re-read a file that may have been left in a partial state by
        # a fixture-mocked backup writer.
        APProfileMigrationManager._print_migration_summary(
            source_name, source_id, target_name, target_id, backup_path, final_payload
        )

        # WHY: FR-A09 -- one JSONL audit row per migrate invocation. Mirrors
        # the revert-side envelope so downstream reporting sees a single
        # shape across both menus. Best-effort write.
        _pacing = final_payload.get("_pacing") or {}
        _delay_count = int(_pacing.get("delay_count", 0))
        _delay_sum = float(_pacing.get("delay_sum", 0.0))
        _delay_mean = (_delay_sum / _delay_count) if _delay_count > 0 else 0.0
        _delay_max = float(_pacing.get("delay_max", 0.0))
        APProfileMigrationManager._emit_migrate_audit(
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

    @staticmethod
    def revert_ap_profile_migration(session: Any | None = None) -> None:
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
        import MistHelper as _mh  # noqa: PLC0415

        org_id = _mh.ConfigUtils.get_cached_or_prompted_org_id()
        # WHY: fall back to the ambient MistHelper apisession when the caller
        # did not pass one -- matches the menu-206 wiring pattern.
        mist_session = session if session is not None else _mh.apisession

        # WHY: enumerate backup files under the data directory and let the
        # picker resolve the operator's choice. When zero candidates exist the
        # helper returns None and we print a short-circuit message.
        candidates = APProfileMigrationManager._list_backup_files(_DATA_DIR)
        backup_path = APProfileMigrationManager._pick_backup_file(candidates)
        if backup_path is None:
            print("No backup file selected. Revert cancelled.")  # noqa: T201
            _LOGGER.info("Revert cancelled: no backup file selected")
            return

        # WHY: rules 1-6 from data-model 1.6. A ValueError names the offending
        # field so the operator can locate the fix without opening the file.
        try:
            payload = APProfileMigrationManager._load_and_validate_backup(str(backup_path))
        except ValueError as exc:
            print(f"Invalid backup: {exc}")  # noqa: T201
            _LOGGER.warning("Revert refused: backup validation failed: %s", exc)
            return

        # WHY: data-model 1.3 states "Revert refuses if the operator's current
        # org does not match." Guards against running a backup from org A
        # against org B, which would touch APs that are not in the backup.
        if payload["org_id"] != org_id:
            print(  # noqa: T201
                f"Refused: backup org_id {payload['org_id']!r} does not match " f"current org_id {org_id!r}.",
            )
            _LOGGER.warning(
                "Revert refused: backup org %s does not match current org %s",
                payload["org_id"],
                org_id,
            )
            return

        source_id = str(payload["source_profile_id"])
        source_name = str(
            payload.get("source_profile_snapshot", {}).get("name", source_id),
        )
        planned_count = len(payload.get("aps_planned", []))

        # WHY: FR-021 -- if the source profile was deleted since the migration
        # ran, refuse the revert with an audited failure so the operator sees a
        # loud short-circuit rather than a silent "success" with zero PUTs.
        if not APProfileMigrationManager._verify_source_profile_exists(mist_session, org_id, source_id):
            print(  # noqa: T201
                f"Source profile {source_id} no longer exists in org {org_id}. "
                f"Recreate the profile or hand-edit the backup before retrying.",
            )
            _LOGGER.warning("Revert refused: source profile %s missing in org %s", source_id, org_id)
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
            return

        # WHY: guarded confirmation -- the exact keyword REVERT arms the run;
        # any other input cancels. Mirrors the migrate-side pattern.
        decision = APProfileMigrationManager._confirm_revert(
            len(payload.get("aps_reassigned", [])),
            source_name,
            str(backup_path),
        )
        if decision != "live":
            print("Revert cancelled.")  # noqa: T201
            _LOGGER.info("Revert cancelled by operator at confirmation prompt")
            return

        # WHY: build a lookup so we can retrieve each AP's site_id (required by
        # updateSiteDevice) from the compact aps_reassigned id list.
        plan_by_id: dict[str, dict[str, Any]] = {str(rec["device_id"]): rec for rec in payload.get("aps_planned", [])}

        aps_to_revert = [str(x) for x in payload.get("aps_reassigned", [])]
        reverted_ids, missing_ids, failed_ids, pacing_stats = APProfileMigrationManager._run_revert_loop(
            mist_session,
            aps_to_revert,
            plan_by_id,
            source_id,
        )

        outcome = APProfileMigrationManager._compute_revert_outcome(reverted_ids, missing_ids, failed_ids)

        APProfileMigrationManager._print_revert_summary(
            backup_path=str(backup_path),
            source_name=source_name,
            source_id=source_id,
            planned_count=planned_count,
            reverted_ids=reverted_ids,
            missing_ids=missing_ids,
            failed_ids=failed_ids,
            outcome=outcome,
            pacing_stats=pacing_stats,
        )

        # WHY: FR-025 -- one JSONL audit row per revert invocation. Best-effort
        # write; TelemetryEmitter swallows OSError and logs a warning.
        APProfileMigrationManager._emit_revert_audit(
            APProfileMigrationManager._build_revert_audit_payload(
                org_id=org_id,
                backup_path=str(backup_path),
                source_id=source_id,
                planned_count=planned_count,
                reverted_ids=reverted_ids,
                missing_ids=missing_ids,
                failed_ids=failed_ids,
                outcome=outcome,
                pacing_stats=pacing_stats,
            )
        )

    # ------------------------------------------------------------------
    # Private helpers -- revert loop and reporting (extracted for Radon CC)
    # ------------------------------------------------------------------

    @staticmethod
    def _new_pacing_stats() -> dict[str, float | int]:
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
        return {
            "puts_issued": 0,
            "http_429_seen": 0,
            "non_429_failures": 0,
            "delay_sum": 0.0,
            "delay_max": 0.0,
            "delay_count": 0,
        }

    @staticmethod
    def _run_revert_loop(
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
        reverted_ids: list[str] = []
        missing_ids: list[str] = []
        failed_ids: list[str] = []
        # WHY: per-invocation pacing state per plan-rate-limiting.md Q3.
        # Mirrors the migrate loop; keeps menus 207 and 208 consistent for
        # the operator (data-model-rate-limiting.md section 2, Q1 lock).
        smoothed: float | None = None
        pacing_stats = APProfileMigrationManager._new_pacing_stats()
        total = len(aps_to_revert)
        for idx, device_id in enumerate(aps_to_revert, start=1):
            rec = plan_by_id.get(device_id)
            if rec is None:
                # WHY: validation rule 5 prevents this, but the guard keeps a
                # hand-edited backup from crashing the loop instead of the
                # earlier refusal path.
                _LOGGER.warning("Skipping unknown device_id %s -- not in aps_planned", device_id)
                continue
            # WHY: emit progress at the same cadence as the migration path so
            # operators see the run is making progress on large fleets.
            if idx == 1 or idx % _PROGRESS_STRIDE == 0 or idx == total:
                _LOGGER.info(
                    "Reverting AP %d of %d: device_id=%s",
                    idx,
                    total,
                    device_id,
                )
            # WHY: FR-A01 -- consult the adaptive limiter once per PUT so a
            # 10K-AP revert stays under Mist's 5000-requests-per-hour ceiling.
            smoothed = APProfileMigrationManager._apply_pacing(smoothed, pacing_stats)
            pacing_stats["puts_issued"] += 1
            APProfileMigrationManager._classify_revert_outcome_for_ap(
                mist_session=mist_session,
                device_id=device_id,
                site_id=str(rec["site_id"]),
                source_id=source_id,
                pacing_stats=pacing_stats,
                reverted_ids=reverted_ids,
                missing_ids=missing_ids,
                failed_ids=failed_ids,
            )
        return reverted_ids, missing_ids, failed_ids, pacing_stats

    @staticmethod
    def _classify_revert_outcome_for_ap(
        *,
        mist_session: Any,
        device_id: str,
        site_id: str,
        source_id: str,
        pacing_stats: dict[str, float | int],
        reverted_ids: list[str],
        missing_ids: list[str],
        failed_ids: list[str],
    ) -> None:
        """Attempt one PUT and route the outcome into the correct id list.

        Why:
            Isolates the single-AP branching (429 vs. other exception vs.
            missing AP vs. success) from the enclosing loop so the loop stays
            under the Radon CC gate. All partitioning of the resulting id
            lists happens through explicit ``list.append`` calls so the caller
            can inspect state after the loop finishes.

        Args:
            mist_session: The mistapi API session used for the PUT call.
            device_id: The AP the caller is attempting to revert.
            site_id: The site the AP is bound to (needed by
                ``updateSiteDevice``).
            source_id: The original source profile ID we are reverting to.
            pacing_stats: Mutable pacing counters that this helper increments
                on 429 or on non-429 failure.
            reverted_ids: Mutable list that receives ``device_id`` on success.
            missing_ids: Mutable list that receives ``device_id`` when Mist
                returns the sentinel "AP no longer exists" result.
            failed_ids: Mutable list that receives ``device_id`` on non-429
                exceptions.
        """
        try:
            result = APProfileMigrationManager._revert_one_ap(
                mist_session,
                device_id,
                site_id,
                source_id,
            )
        except Exception as exc:  # noqa: BLE001  # WHY: tolerant per FR-023.
            # WHY: FR-A04 -- 429 is a throttle signal. Feed the limiter via
            # cache invalidation and continue; do NOT count the AP as failed
            # on 429 alone.
            if APProfileMigrationManager._is_429(exc):
                APProfileMigrationManager._signal_rate_limit_hit()
                pacing_stats["http_429_seen"] += 1
                return
            pacing_stats["non_429_failures"] += 1
            failed_ids.append(device_id)
            _LOGGER.warning(
                "Revert failed for AP %s after retry exhaustion: %s",
                device_id,
                exc,
            )
            return

        if result == _REVERT_MISSING:
            # WHY: FR-023 -- the AP no longer exists in Mist; count and
            # continue instead of aborting the run.
            missing_ids.append(device_id)
            _LOGGER.warning("AP %s no longer exists in Mist; counted as missing", device_id)
            return

        reverted_ids.append(device_id)

    @staticmethod
    def _compute_revert_outcome(
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
        if not missing_ids and not failed_ids:
            return "success"
        if reverted_ids or missing_ids:
            return "partial"
        return "failure"

    @staticmethod
    def _print_revert_summary(
        *,
        backup_path: str,
        source_name: str,
        source_id: str,
        planned_count: int,
        reverted_ids: list[str],
        missing_ids: list[str],
        failed_ids: list[str],
        outcome: str,
        pacing_stats: dict[str, float | int],
    ) -> None:
        """Print the operator-facing end-of-run summary for menu 208.

        Why:
            The summary block is deterministic text with two conditional
            "missing" / "failed" lines and one adaptive-limiter telemetry
            block. Extracting it drops several branches out of the entry point
            and gives a single call site to freeze in golden-output tests.

        Args:
            backup_path: Absolute path of the backup file the operator picked.
            source_name: Human-readable original source profile name.
            source_id: Original source profile ID.
            planned_count: Total AP count from the backup's ``aps_planned``.
            reverted_ids: Successfully reverted device IDs.
            missing_ids: Device IDs Mist reported as no-longer-existing.
            failed_ids: Device IDs that failed for non-429 reasons.
            outcome: The final ``success``/``partial``/``failure`` label from
                ``_compute_revert_outcome``.
            pacing_stats: Final pacing counters from the revert loop.
        """
        print("\nRevert summary:")  # noqa: T201
        print(f"  Backup file: {backup_path}")  # noqa: T201
        print(f"  Source profile: {source_name} (id={source_id})")  # noqa: T201
        print(f"  Planned APs: {planned_count}")  # noqa: T201
        print(f"  Reverted APs: {len(reverted_ids)}")  # noqa: T201
        print(f"  Missing APs: {len(missing_ids)}")  # noqa: T201
        print(f"  Failed APs: {len(failed_ids)}")  # noqa: T201
        print(f"  Outcome: {outcome}")  # noqa: T201
        if missing_ids:
            # WHY: name every missing AP so the operator can hand-fix.
            print(f"  Missing device_ids: {', '.join(missing_ids)}")  # noqa: T201
        if failed_ids:
            print(f"  Failed device_ids: {', '.join(failed_ids)}")  # noqa: T201

        # WHY: FR-A09 -- adaptive-rate-limiter telemetry lines. Same text,
        # same order as the migrate-side summary so operators reading both
        # menus see one consistent block.
        delay_count = int(pacing_stats["delay_count"])
        delay_mean = (pacing_stats["delay_sum"] / delay_count) if delay_count > 0 else 0.0
        delay_max = float(pacing_stats["delay_max"])
        print(f"  Total PUTs issued        : {int(pacing_stats['puts_issued'])}")  # noqa: T201
        print(f"  HTTP 429 responses seen  : {int(pacing_stats['http_429_seen'])}")  # noqa: T201
        print(f"  Non-429 failures         : {int(pacing_stats['non_429_failures'])}")  # noqa: T201
        print(f"  Rate limiter delay (s)   : mean={delay_mean:.3f}  max={delay_max:.3f}")  # noqa: T201

    @staticmethod
    def _build_revert_audit_payload(
        *,
        org_id: str,
        backup_path: str,
        source_id: str,
        planned_count: int,
        reverted_ids: list[str],
        missing_ids: list[str],
        failed_ids: list[str],
        outcome: str,
        pacing_stats: dict[str, float | int],
    ) -> dict[str, Any]:
        """Build the JSONL audit payload for a completed revert run.

        Why:
            Split from the entry point so the payload shape can be exercised
            in unit tests without invoking the whole menu. The shape matches
            data-model-rate-limiting.md section 3 for the pacing sub-dict.

        Args:
            org_id: The operator's current org.
            backup_path: Absolute path of the backup file that was replayed.
            source_id: Original source profile ID reverted to.
            planned_count: Total AP count from the backup's ``aps_planned``.
            reverted_ids: Successfully reverted device IDs.
            missing_ids: Device IDs Mist reported as no-longer-existing.
            failed_ids: Device IDs that failed for non-429 reasons.
            outcome: ``success`` / ``partial`` / ``failure`` label.
            pacing_stats: Final pacing counters from the revert loop.

        Returns:
            The dict that ``_emit_revert_audit`` will write as one JSONL row.
        """
        delay_count = int(pacing_stats["delay_count"])
        delay_mean = (pacing_stats["delay_sum"] / delay_count) if delay_count > 0 else 0.0
        delay_max = float(pacing_stats["delay_max"])
        return {
            "event_type": "ap_profile_migration_revert",
            "timestamp_utc": _utc_iso_timestamp(),
            "org_id": org_id,
            "backup_file_path": backup_path,
            "source_profile_id": source_id,
            "planned_count": planned_count,
            "reverted_count": len(reverted_ids),
            "missing_count": len(missing_ids),
            "failed_count": len(failed_ids),
            "outcome": outcome,
            # WHY: FR-A09 -- pacing telemetry sub-dict per
            # data-model-rate-limiting.md section 3.
            "pacing": {
                "puts_issued": int(pacing_stats["puts_issued"]),
                "http_429_seen": int(pacing_stats["http_429_seen"]),
                "non_429_failures": int(pacing_stats["non_429_failures"]),
                "delay_seconds_mean": round(delay_mean, 3),
                "delay_seconds_max": round(delay_max, 3),
            },
        }

    # ------------------------------------------------------------------
    # Private helpers -- adaptive rate limiting (addendum FR-A01..FR-A09)
    # ------------------------------------------------------------------

    @staticmethod
    def _is_429(err: BaseException) -> bool:
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
        status_code = getattr(getattr(err, "response", None), "status_code", None)
        return status_code == 429

    @staticmethod
    def _apply_pacing(
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
        import MistHelper as _mh  # noqa: PLC0415

        try:
            smoothed, delay = _mh.RateLimitingUtils.get_rate_limited_delay(
                smoothed,
                _mh.apisession,
                _mh._api_usage_cache,
            )
        except Exception as exc:  # noqa: BLE001  # WHY: FR-A06 -- limiter is diagnostic, not critical.
            # WHY: FR-A06 -- a limiter fault MUST NOT halt the migration.
            # Fall back to a fixed conservative sleep and log the fault so
            # the operator can investigate later.
            _LOGGER.warning(
                "Rate limiter failed (%s). Using fallback delay of %.2f s",
                exc,
                _LIMITER_FALLBACK_DELAY,
            )
            delay = _LIMITER_FALLBACK_DELAY

        # WHY: delay is None only if the PID helper misreports; coerce to 0.0
        # so downstream arithmetic stays a float.
        if delay is None:
            delay = 0.0

        pacing_stats["delay_sum"] = float(pacing_stats["delay_sum"]) + float(delay)
        pacing_stats["delay_max"] = max(float(pacing_stats["delay_max"]), float(delay))
        pacing_stats["delay_count"] = int(pacing_stats["delay_count"]) + 1

        # WHY: sleep via module attribute so tests can patch it with
        # ``patch("src.device.ap_profile_migration_manager.time.sleep", ...)``.
        time.sleep(delay)
        return smoothed

    @staticmethod
    def _signal_rate_limit_hit() -> None:
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
        import MistHelper as _mh  # noqa: PLC0415

        _LOGGER.warning(
            "The API returned HTTP 429. Invalidating the API usage cache to trigger a limiter refresh",
        )
        try:
            # WHY: cache-invalidation is the addendum's 429 feedback surface;
            # _needs_refresh consumes this flag on the next consult.
            _mh._api_usage_cache["initialized"] = False
        except (KeyError, TypeError, AttributeError) as exc:
            _LOGGER.warning(
                "API usage cache unavailable (%s); 429 feedback suppressed this iteration",
                exc,
            )

    # ------------------------------------------------------------------
    # Private helpers -- migration (T017-T024)
    # ------------------------------------------------------------------

    @staticmethod
    def _fetch_and_sort_ap_profiles(session: Any, org_id: str) -> list[dict[str, Any]]:
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
        response = _mist_deviceprofiles.listOrgDeviceProfiles(session, org_id)
        # WHY: get_all walks pagination in production; tests can return a
        # ready-made list on .data and get_all handles both shapes.
        try:
            profiles = mistapi.get_all(response=response, mist_session=session)
        except Exception:  # noqa: BLE001  # WHY: fallback for mocked responses.
            profiles = getattr(response, "data", []) or []

        ap_profiles = [p for p in profiles if p.get("type") == "ap"]
        if not ap_profiles:
            raise RuntimeError("No AP device profiles found in the selected organization.")

        # WHY: alphabetise by name for a stable operator UX.
        ap_profiles.sort(key=lambda p: str(p.get("name", "")).lower())
        return ap_profiles

    @staticmethod
    def _pick_ap_device_profile(session: Any, org_id: str, prompt_text: str) -> tuple[str, str, dict[str, Any]]:
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
        import MistHelper as _mh  # noqa: PLC0415

        ap_profiles = APProfileMigrationManager._fetch_and_sort_ap_profiles(session, org_id)

        print(f"\n{prompt_text}")  # noqa: T201
        for idx, prof in enumerate(ap_profiles, start=1):
            print(f"  {idx}. {prof.get('name', '<unnamed>')} (id={prof.get('id', '<no-id>')})")  # noqa: T201

        # WHY: EOF-safe input via the shared safe_input helper; retry on
        # non-numeric or out-of-range input.
        count = len(ap_profiles)
        while True:
            choice = _mh.InputUtils.safe_input(
                f"  Select profile (1-{count}) or 'q' to cancel: ",
                default_value="",
                allow_empty=True,
                context="ap_profile_picker",
            )
            if choice.lower() == "q":
                raise RuntimeError("Profile selection cancelled by operator.")
            try:
                index = int(choice)
            except ValueError:
                print(f"  Enter a number between 1 and {count}.")  # noqa: T201
                continue
            if 1 <= index <= count:
                picked = ap_profiles[index - 1]
                return (
                    str(picked.get("id", "")),
                    str(picked.get("name", "")),
                    dict(picked),
                )
            print(f"  Enter a number between 1 and {count}.")  # noqa: T201

    @staticmethod
    def _discover_aps_on_source_profile(session: Any, org_id: str, source_profile_id: str) -> list[dict[str, Any]]:
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
        _LOGGER.info("Discovering APs bound to profile %s across every site", source_profile_id)
        # WHY: listOrgSites gives us the site_id list; loop is the only walk.
        sites_response = _mist_orgs_sites.listOrgSites(session, org_id)
        try:
            sites = mistapi.get_all(response=sites_response, mist_session=session)
        except Exception:  # noqa: BLE001
            sites = getattr(sites_response, "data", []) or []

        records: list[dict[str, Any]] = []
        for site in sites:
            site_id = str(site.get("id", ""))
            if not site_id:
                continue
            _LOGGER.info("Scanning site %s (%s) for APs", site.get("name", ""), site_id)
            try:
                # WHY: type="ap" keeps the response shape tight and skips
                # switches / gateways at the API side.
                devs_response = _mist_site_devices.listSiteDevices(session, site_id, type="ap")
                devs = mistapi.get_all(response=devs_response, mist_session=session)
            except Exception:  # noqa: BLE001  # WHY: skip unreachable sites.
                _LOGGER.exception("Failed to list devices for site %s", site_id)
                continue

            for dev in devs:
                if dev.get("deviceprofile_id") != source_profile_id:
                    continue
                records.append(
                    {
                        "device_id": str(dev.get("id", "")),
                        "site_id": site_id,
                        "mac": str(dev.get("mac", "")),
                        "hostname": dev.get("name") or dev.get("hostname"),
                    }
                )
        _LOGGER.info("Discovery complete: %d APs bound to source profile", len(records))
        return records

    @staticmethod
    def _render_migration_plan(
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
        _source_id, source_name = source
        _target_id, target_name = target
        print("\nPlanned migration:")  # noqa: T201
        for rec in ap_records:
            hostname = rec.get("hostname") or "-"
            print(f"  device_id={rec['device_id']}  hostname={hostname}  site={rec['site_id']}")  # noqa: T201
        print(f"Total: {len(ap_records)} APs will be reassigned " f"from {source_name} to {target_name}")  # noqa: T201

    @staticmethod
    def _confirm_migration(count: int, source_name: str, target_name: str) -> str:
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
        import MistHelper as _mh  # noqa: PLC0415

        prompt = (
            f"\nType {_KEYWORD_LIVE!r} to reassign {count} APs from "
            f"{source_name} to {target_name}, "
            f"or {_KEYWORD_DRY_RUN!r} to preview only: "
        )
        response = _mh.InputUtils.safe_input(
            prompt,
            default_value="",
            allow_empty=True,
            context="ap_profile_migration_confirm",
        )
        # WHY: strip trailing whitespace but keep case-sensitive compare so a
        # lowercase "migrate" is treated as cancel.
        response = response.strip()
        if response == _KEYWORD_LIVE:
            return "live"
        if response == _KEYWORD_DRY_RUN:
            return "dry_run"
        return "cancel"

    @staticmethod
    def _build_backup_payload(
        org_id: str,
        source_id: str,
        source_snapshot: dict[str, Any],
        target_id: str,
        target_snapshot: dict[str, Any],
        ap_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Assemble the backup dict per data-model §1.3.

        Why:
            Centralises the schema so a future field addition edits one
            place. Timestamp is normalized to trailing ``Z`` for human
            readability (data-model §1.3).

        Args:
            org_id: The Mist org UUID.
            source_id: The source profile UUID.
            source_snapshot: Full source-profile JSON.
            target_id: The target profile UUID.
            target_snapshot: Full target-profile JSON.
            ap_records: The APs the migration plans to reassign.

        Returns:
            The pre-run backup payload dict.
        """
        # WHY: aware UTC + ISO extended, then replace "+00:00" with "Z" for the
        # canonical trailing-Z form the data-model example uses.
        ts = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        return {
            "schema_version": _BACKUP_SCHEMA_VERSION,
            "org_id": org_id,
            "migration_timestamp_utc": ts,
            "source_profile_id": source_id,
            "target_profile_id": target_id,
            "source_profile_snapshot": dict(source_snapshot),
            "target_profile_snapshot": dict(target_snapshot),
            "aps_planned": [dict(rec) for rec in ap_records],
            "aps_reassigned": [],
            "outcome": "success",
            "failure_detail": None,
        }

    @staticmethod
    def _write_backup_file(payload: dict[str, Any], data_dir: str) -> str:
        """Write ``payload`` to a new backup file and return the absolute path.

        Why:
            The filename convention (data-model §1.1) sorts chronologically
            as a plain string, so ``ls | sort`` gives newest-last without a
            special comparator.

        Args:
            payload: The backup dict returned by ``_build_backup_payload``.
            data_dir: Directory under which the file is written.

        Returns:
            The absolute path (as a string) of the file just written.

        Raises:
            OSError: When the write fails for any reason (disk full, denied,
                path missing). The caller MUST NOT issue any PUT if this
                raises (FR-011).
        """
        # WHY: parse ISO timestamp back into the basic YYYYMMDDTHHMMSSZ form
        # used in the filename per data-model §1.1.
        iso_ts = str(payload.get("migration_timestamp_utc", ""))
        basic_ts = iso_ts.replace("-", "").replace(":", "")  # WHY: strip separators.
        source_id = str(payload.get("source_profile_id", ""))
        target_id = str(payload.get("target_profile_id", ""))
        filename = f"ap-profile-migration_{basic_ts}_{source_id}_to_{target_id}.json"

        # WHY: ensure the directory exists so a fresh checkout without data/
        # still writes cleanly (a common CI-runner situation).
        target_dir = Path(data_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        # WHY: sort_keys=False preserves the field order the data-model
        # example shows -- readable for humans skimming the file.
        target_path.write_text(
            json.dumps(payload, indent=2, sort_keys=False),
            encoding="utf-8",
        )
        return str(target_path.resolve())

    @staticmethod
    def _reassign_one_ap(
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
            Exception: The last exception observed after retry exhaustion.
        """
        # WHY: two retries -> three total attempts. The backoff sequence is
        # pinned by research Decision 2 -- any change here breaks T013.
        body = {"deviceprofile_id": target_profile_id}
        last_exc: BaseException | None = None
        # WHY: attempt indices 0, 1, 2. Sleep AFTER attempts 0 and 1 only.
        for attempt in range(len(_RETRY_BACKOFF_SECONDS) + 1):
            try:
                response = _mist_site_devices.updateSiteDevice(
                    session, ap_record["site_id"], ap_record["device_id"], body
                )
                # WHY: issue #1700 -- the SDK answers an error status with an
                # object instead of raising. Read that status before the call
                # counts as a success.
                APProfileMigrationManager._check_reassign_response(response, ap_record["device_id"])
                return
            except Exception as exc:  # noqa: BLE001  # WHY: broad catch for retry policy.
                last_exc = exc
                # WHY: sleep only if there is a next attempt to make. Attribute
                # access on the ``time`` module (rather than a captured default
                # parameter) lets ``patch("time.sleep", ...)`` intercept.
                if attempt < len(_RETRY_BACKOFF_SECONDS):
                    time.sleep(_RETRY_BACKOFF_SECONDS[attempt])
                    continue
                # WHY: retry exhaustion -- re-raise the last exception so the
                # loop can record the failure detail and stop.
                raise
        # WHY: unreachable; guard against typing lint anyway.
        if last_exc is not None:
            raise last_exc

    @staticmethod
    def _check_reassign_response(response: Any, device_id: str) -> None:
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
        status_code = getattr(response, "status_code", None)
        if not isinstance(status_code, int):
            return
        # WHY: 1xx, 2xx, and 3xx leave the reassignment claim intact.
        if status_code < _HTTP_ERROR_FLOOR:
            return
        _LOGGER.warning(
            "Reassignment PUT for device %s reported HTTP %s. The device profile did not change.",
            device_id,
            status_code,
        )
        raise APProfileReassignmentError(response, device_id)

    @staticmethod
    def _run_reassignment_loop(
        session: Any,
        ap_records: list[dict[str, Any]],
        target_id: str,
        backup_path: str,
        payload: dict[str, Any],
        *,
        progress_stride: int = _PROGRESS_STRIDE,
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
        backup = payload
        total = len(ap_records)
        # WHY: per-invocation pacing state per plan-rate-limiting.md Q3.
        # ``smoothed`` is the PID limiter's internal EMA of the returned delay;
        # the limiter mutates it across calls. ``pacing_stats`` tracks the
        # counters that feed FR-A09 summary lines and the JSONL audit line.
        smoothed: float | None = None
        pacing_stats: dict[str, float | int] = {
            "puts_issued": 0,
            "http_429_seen": 0,
            "non_429_failures": 0,
            "delay_sum": 0.0,
            "delay_max": 0.0,
            "delay_count": 0,
        }
        for idx, rec in enumerate(ap_records, start=1):
            # WHY: emit progress at N=1, at every stride boundary, and at N=total.
            if idx == 1 or idx % progress_stride == 0 or idx == total:
                _LOGGER.info(
                    "Reassigning AP %d of %d: device_id=%s",
                    idx,
                    total,
                    rec["device_id"],
                )
            # WHY: FR-A01 -- consult the adaptive limiter once per PUT so a
            # 10K-AP run stays under Mist's 5000-requests-per-hour ceiling.
            smoothed = APProfileMigrationManager._apply_pacing(smoothed, pacing_stats)
            pacing_stats["puts_issued"] += 1
            try:
                APProfileMigrationManager._reassign_one_ap(session, rec, target_id)
            except Exception as exc:  # noqa: BLE001  # WHY: partial-success record path.
                # WHY: FR-A04 -- 429 is a throttle signal, not a hard failure.
                # Feed the cache-invalidation signal to the limiter and keep
                # going; the retry policy in ``_reassign_one_ap`` already
                # burnt its three attempts on this AP, so record it and skip.
                if APProfileMigrationManager._is_429(exc):
                    APProfileMigrationManager._signal_rate_limit_hit()
                    pacing_stats["http_429_seen"] += 1
                    continue
                # WHY: FR-017 -- stop on first non-429 failure so the on-disk
                # file exactly matches the state Mist is in.
                pacing_stats["non_429_failures"] += 1
                backup["outcome"] = "partial"
                backup["failure_detail"] = {
                    "failed_device_id": rec["device_id"],
                    "failed_site_id": rec["site_id"],
                    "error_message": str(exc),
                    "reassigned_count": len(backup["aps_reassigned"]),
                    "planned_count": total,
                }
                Path(backup_path).write_text(
                    json.dumps(backup, indent=2, sort_keys=False),
                    encoding="utf-8",
                )
                _LOGGER.warning(
                    "Reassignment failed for AP %s after retry exhaustion; run stopped",
                    rec["device_id"],
                )
                # WHY: attach ephemeral pacing telemetry for the summary and
                # JSONL emitters. Leading underscore keeps it out of the
                # persisted backup schema (FR-A09).
                backup["_pacing"] = pacing_stats
                return backup

            # WHY: append + rewrite after every success so an interrupted
            # revert has an accurate list to roll back.
            backup["aps_reassigned"].append(rec["device_id"])
            Path(backup_path).write_text(
                json.dumps(backup, indent=2, sort_keys=False),
                encoding="utf-8",
            )

        # WHY: fell through the loop -- every AP succeeded.
        backup["outcome"] = "success"
        backup["failure_detail"] = None
        Path(backup_path).write_text(
            json.dumps(backup, indent=2, sort_keys=False),
            encoding="utf-8",
        )
        # WHY: attach ephemeral pacing telemetry per FR-A09.
        backup["_pacing"] = pacing_stats
        return backup

    @staticmethod
    def _print_migration_summary(
        source_name: str,
        source_id: str,
        target_name: str,
        target_id: str,
        backup_path: str,
        payload: dict[str, Any],
    ) -> None:
        """Print the end-of-run summary block.

        Why:
            The summary names the source, target, backup file path, and the
            planned/reassigned counts so the operator sees the outcome at a
            glance without opening the JSON file.

        Args:
            source_name: Human-readable source profile name.
            source_id: Source profile UUID.
            target_name: Human-readable target profile name.
            target_id: Target profile UUID.
            backup_path: Absolute path to the backup file just written.
            payload: The final backup dict (post-loop).
        """
        planned = len(payload.get("aps_planned", []))
        reassigned = len(payload.get("aps_reassigned", []))
        outcome = payload.get("outcome", "unknown")
        print("\nMigration summary:")  # noqa: T201
        print(f"  Source profile: {source_name} (id={source_id})")  # noqa: T201
        print(f"  Target profile: {target_name} (id={target_id})")  # noqa: T201
        print(f"  Planned APs: {planned}")  # noqa: T201
        print(f"  Reassigned APs: {reassigned}")  # noqa: T201
        print(f"  Outcome: {outcome}")  # noqa: T201
        print(f"  Backup file: {backup_path}")  # noqa: T201
        if outcome != "success":
            fd = payload.get("failure_detail")
            if fd is not None:
                print(f"  Failed AP: {fd.get('failed_device_id')}  " f"reason: {fd.get('error_message')}")  # noqa: T201
        # WHY: FR-A09 -- adaptive-rate-limiter telemetry lines. Text and
        # order pinned by data-model-rate-limiting.md section 2 so menus
        # 207 and 208 present one consistent block to the operator.
        pacing_stats = payload.get("_pacing") or {
            "puts_issued": 0,
            "http_429_seen": 0,
            "non_429_failures": 0,
            "delay_sum": 0.0,
            "delay_max": 0.0,
            "delay_count": 0,
        }
        _delay_count = int(pacing_stats.get("delay_count", 0))
        _delay_sum = float(pacing_stats.get("delay_sum", 0.0))
        _delay_mean = (_delay_sum / _delay_count) if _delay_count > 0 else 0.0
        _delay_max = float(pacing_stats.get("delay_max", 0.0))
        print(f"  Total PUTs issued        : {int(pacing_stats.get('puts_issued', 0))}")  # noqa: T201
        print(f"  HTTP 429 responses seen  : {int(pacing_stats.get('http_429_seen', 0))}")  # noqa: T201
        print(f"  Non-429 failures         : {int(pacing_stats.get('non_429_failures', 0))}")  # noqa: T201
        print(f"  Rate limiter delay (s)   : mean={_delay_mean:.3f}  max={_delay_max:.3f}")  # noqa: T201

    # ------------------------------------------------------------------
    # Private helpers -- revert (T036-T042)
    # ------------------------------------------------------------------

    @staticmethod
    def _list_backup_files(data_dir: str) -> list[Path]:
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
        base = Path(data_dir)
        if not base.is_dir():
            return []
        # WHY: glob returns unordered on some filesystems; sort by filename in
        # reverse so the newest ISO-basic timestamp lands first.
        candidates = sorted(base.glob("ap-profile-migration_*.json"), reverse=True)
        return candidates

    @staticmethod
    def _pick_backup_file(candidates: list[Path]) -> Path | None:
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
        import MistHelper as _mh  # noqa: PLC0415

        if not candidates:
            print("No backup files found under data/. Nothing to revert.")  # noqa: T201
            _LOGGER.info("No backup files present under data/")
            return None

        print("\nSelect the backup file to revert:")  # noqa: T201
        for idx, path in enumerate(candidates, start=1):
            print(f"  {idx}. {path.name}")  # noqa: T201

        count = len(candidates)
        # WHY: retry loop for non-numeric or out-of-range input; matches the
        # UX pattern used by ``_pick_ap_device_profile``.
        while True:
            choice = _mh.InputUtils.safe_input(
                f"  Select backup (1-{count}) or 'q' to cancel: ",
                default_value="",
                allow_empty=True,
                context="ap_profile_revert_picker",
            )
            if choice.lower() == "q":
                return None
            try:
                index = int(choice)
            except ValueError:
                print(f"  Enter a number between 1 and {count}.")  # noqa: T201
                continue
            if 1 <= index <= count:
                return candidates[index - 1]
            print(f"  Enter a number between 1 and {count}.")  # noqa: T201

    @staticmethod
    def _load_and_validate_backup(path: str) -> dict[str, Any]:
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
        payload = APProfileMigrationManager._parse_backup_file(path)
        APProfileMigrationManager._validate_backup_top_level(payload)
        planned = payload["aps_planned"]
        APProfileMigrationManager._validate_planned_records(planned)
        APProfileMigrationManager._validate_reassigned_list(
            payload.get("aps_reassigned", []),
            planned,
        )
        APProfileMigrationManager._validate_snapshot_ids(payload)
        return payload

    @staticmethod
    def _parse_backup_file(path: str) -> dict[str, Any]:
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
            raw = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"backup file unreadable: {exc}") from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"backup file not valid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("backup file top-level must be a JSON object")
        return payload

    @staticmethod
    def _validate_backup_top_level(payload: dict[str, Any]) -> None:
        """Enforce data-model 1.6 rules 1 through 3 on the backup top level.

        Why:
            Isolates the schema-version + required-string-field + planned-list
            checks so ``_load_and_validate_backup`` stays under the Radon
            complexity gate.

        Args:
            payload: The parsed backup dict.

        Returns:
            None.

        Raises:
            ValueError: When schema_version is wrong, a required string
                field is missing or empty, or ``aps_planned`` is missing or
                not a JSON array.
        """
        version = payload.get("schema_version")
        if version != _BACKUP_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {_BACKUP_SCHEMA_VERSION}; got {version!r}")
        for field in ("org_id", "source_profile_id", "target_profile_id", "migration_timestamp_utc"):
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"required field {field!r} must be a non-empty string")
        planned = payload.get("aps_planned")
        if planned is None:
            raise ValueError("required field 'aps_planned' is missing")
        if not isinstance(planned, list):
            raise ValueError("required field 'aps_planned' must be a JSON array")

    @staticmethod
    def _validate_planned_records(planned: list[Any]) -> None:
        """Enforce data-model 1.6 rule 4 on every ``aps_planned`` entry.

        Why:
            Each APRecord must have non-empty ``device_id``, ``site_id``,
            and ``mac``. Extracting the loop keeps the caller's CC low.

        Args:
            planned: The list of AP records from the backup file.

        Returns:
            None.

        Raises:
            ValueError: When any entry is not a dict or any required
                sub-field is missing or empty.
        """
        for idx, rec in enumerate(planned):
            if not isinstance(rec, dict):
                raise ValueError(f"aps_planned[{idx}] must be a JSON object")
            for sub in ("device_id", "site_id", "mac"):
                v = rec.get(sub)
                if not isinstance(v, str) or not v.strip():
                    raise ValueError(f"aps_planned[{idx}].{sub} must be a non-empty string")

    @staticmethod
    def _validate_reassigned_list(reassigned: Any, planned: list[Any]) -> None:
        """Enforce data-model 1.6 rule 5 on ``aps_reassigned``.

        Why:
            Every entry of ``aps_reassigned`` must be a string and must
            appear as a ``device_id`` in ``aps_planned``. Guards against
            hand-edited backups that reference APs not in the plan.

        Args:
            reassigned: The value of the ``aps_reassigned`` field.
            planned: The list of AP records (already validated).

        Returns:
            None.

        Raises:
            ValueError: When the field is not a list, an entry is not a
                string, or an entry is not present in ``aps_planned``.
        """
        if not isinstance(reassigned, list):
            raise ValueError("field 'aps_reassigned' must be a JSON array of strings")
        planned_ids = {str(rec.get("device_id", "")) for rec in planned}
        for entry in reassigned:
            if not isinstance(entry, str):
                raise ValueError("aps_reassigned entries must be strings")
            if entry not in planned_ids:
                raise ValueError(f"aps_reassigned contains id {entry!r} not present in aps_planned")

    @staticmethod
    def _validate_snapshot_ids(payload: dict[str, Any]) -> None:
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
        src_snap = payload.get("source_profile_snapshot")
        tgt_snap = payload.get("target_profile_snapshot")
        if isinstance(src_snap, dict) and src_snap.get("id") != payload["source_profile_id"]:
            raise ValueError("source_profile_snapshot.id does not match source_profile_id")
        if isinstance(tgt_snap, dict) and tgt_snap.get("id") != payload["target_profile_id"]:
            raise ValueError("target_profile_snapshot.id does not match target_profile_id")

    @staticmethod
    def _verify_source_profile_exists(session: Any, org_id: str, source_profile_id: str) -> bool:
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
            response = _mist_deviceprofiles.getOrgDeviceProfile(session, org_id, source_profile_id)
        except Exception as exc:  # noqa: BLE001  # WHY: any error treats profile as missing.
            _LOGGER.warning("getOrgDeviceProfile raised for %s: %s", source_profile_id, exc)
            return False
        # WHY: mistapi may return a response object with .status_code; a 404
        # means the profile is gone.
        status = getattr(response, "status_code", 200)
        if status == 404:
            return False
        # WHY: defensive id-match check -- an SDK that returns an empty body
        # on error would otherwise be misread as success.
        data = getattr(response, "data", None)
        if isinstance(data, dict) and data.get("id") and data["id"] != source_profile_id:
            _LOGGER.warning(
                "getOrgDeviceProfile returned id %s for lookup of %s",
                data.get("id"),
                source_profile_id,
            )
            return False
        return True

    @staticmethod
    def _confirm_revert(count: int, source_name: str, backup_path: str) -> str:
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
        import MistHelper as _mh  # noqa: PLC0415

        prompt = (
            f"\nType {_KEYWORD_REVERT!r} to revert {count} APs back to "
            f"{source_name}\n(backup file: {backup_path}): "
        )
        response = _mh.InputUtils.safe_input(
            prompt,
            default_value="",
            allow_empty=True,
            context="ap_profile_revert_confirm",
        )
        # WHY: strip trailing whitespace but keep case-sensitive compare so a
        # lowercase "revert" is treated as cancel.
        if response.strip() == _KEYWORD_REVERT:
            return "live"
        return "cancel"

    @staticmethod
    def _revert_one_ap(
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
            Exception: The last exception observed after retry exhaustion.
        """
        # WHY: same cadence as the migrate side -- two retries, three total
        # attempts, sleep only when a next attempt exists.
        body = {"deviceprofile_id": source_profile_id}
        last_exc: BaseException | None = None
        for attempt in range(len(_RETRY_BACKOFF_SECONDS) + 1):
            try:
                response = _mist_site_devices.updateSiteDevice(session, site_id, device_id, body)
            except Exception as exc:  # noqa: BLE001  # WHY: broad catch for retry policy.
                last_exc = exc
                if attempt < len(_RETRY_BACKOFF_SECONDS):
                    time.sleep(_RETRY_BACKOFF_SECONDS[attempt])
                    continue
                raise
            # WHY: mistapi returns a response object; a 404 status means the
            # AP is missing from Mist -- report as missing (FR-023) not retry.
            status = getattr(response, "status_code", 200)
            if status == 404:
                return _REVERT_MISSING
            # WHY: any 5xx (or other non-2xx) is a retryable server problem;
            # treat as failure and back off the same way an exception would.
            if isinstance(status, int) and status >= 500:
                last_exc = RuntimeError(f"HTTP {status} on updateSiteDevice for {device_id}")
                if attempt < len(_RETRY_BACKOFF_SECONDS):
                    time.sleep(_RETRY_BACKOFF_SECONDS[attempt])
                    continue
                raise last_exc
            # WHY: fell through -- SDK success or 2xx status.
            return None
        # WHY: unreachable; guard against typing lint anyway.
        if last_exc is not None:
            raise last_exc
        return None

    @staticmethod
    def _emit_revert_audit(event: dict[str, Any]) -> None:
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
        from src.analytics.telemetry_emitter import TelemetryEmitter  # noqa: PLC0415

        # WHY: colocate the telemetry file with the backup files so the
        # operator finds every audit artefact under one directory.
        target = Path(_DATA_DIR) / _REVERT_TELEMETRY_FILENAME
        # WHY: context manager guarantees flush + close even on an emit that
        # raises inside the writer.
        with TelemetryEmitter(str(target)) as emitter:
            emitter.emit(event)

    @staticmethod
    def _emit_migrate_audit(event: dict[str, Any]) -> None:
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
        from src.analytics.telemetry_emitter import TelemetryEmitter  # noqa: PLC0415

        # WHY: colocate with backup files and the revert audit stream so the
        # operator finds every artefact under one directory.
        target = Path(_DATA_DIR) / _MIGRATE_TELEMETRY_FILENAME
        with TelemetryEmitter(str(target)) as emitter:
            emitter.emit(event)
