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
            NotImplementedError: This is the T005 skeleton placeholder; the
                real implementation lands in T036-T043.
        """
        # WHY: skeleton placeholder -- real body lands in T043 (US2
        # implementation phase). See the sibling migrate entry-point comment
        # for the interrogate-coverage rationale.
        raise NotImplementedError(
            "APProfileMigrationManager.revert_ap_profile_migration is a"
            " T005 skeleton; implementation lands in T036-T043.",
        )

    # ------------------------------------------------------------------
    # Private helpers -- migration (T017-T024)
    # ------------------------------------------------------------------

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

        # WHY: fetch every profile, filter to type=="ap" locally so a test that
        # returns a mixed list still gets the correct filter behaviour.
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
                _mist_site_devices.updateSiteDevice(session, ap_record["site_id"], ap_record["device_id"], body)
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
            end-of-run summary (avoids a second disk read).
        """
        # WHY: work on the caller-supplied in-memory dict so tests that patch
        # ``_write_backup_file`` (T011) still exercise the loop end-to-end.
        backup = payload
        total = len(ap_records)
        for idx, rec in enumerate(ap_records, start=1):
            # WHY: emit progress at N=1, at every stride boundary, and at N=total.
            if idx == 1 or idx % progress_stride == 0 or idx == total:
                _LOGGER.info(
                    "Reassigning AP %d of %d: device_id=%s",
                    idx,
                    total,
                    rec["device_id"],
                )
            try:
                APProfileMigrationManager._reassign_one_ap(session, rec, target_id)
            except Exception as exc:  # noqa: BLE001  # WHY: partial-success record path.
                # WHY: FR-017 -- stop on first failure so the on-disk file
                # exactly matches the state Mist is in.
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
