# Phase 0 Research: 1029-ap-profile-migration

**Date**: 2026-07-27
**Status**: Complete — all NEEDS CLARIFICATION resolved

Most research for this feature was completed during the `/speckit.specify`
phase (see `spec.md` Assumptions section). This document captures only the
decisions taken during planning that were not fully pinned by the spec.

---

## Decision 1: Per-AP PUT via `updateSiteDevice`, not bulk `assignOrgDeviceProfile`

**Decision**: Use
`mistapi.api.v1.sites.devices.updateSiteDevice(session, site_id, device_id, body={"deviceprofile_id": "<target>"})`
one call per AP.

**Rationale**: FR-017 requires that on the first PUT failure, the tool
stops immediately and records the exact list of APs already reassigned so
that a subsequent revert acts on the correct partial-success set. The bulk
`mistapi.api.v1.orgs.devices.assignOrgDeviceProfile` endpoint accepts
`body={"macs":[...]}` and returns an aggregate result — it does not
guarantee ordered per-AP status suitable for building a correct
partial-success list on abort. Per-AP PUT gives full transactional
granularity at a cost of N HTTP calls, which is acceptable for the SC-001
scale (up to 500 APs).

**Alternatives considered**:

- `assignOrgDeviceProfile` bulk POST — rejected: coarse failure reporting
  breaks FR-017. Also observed in existing menu 174
  (`SiteConfigManager.assign_aps_to_matching_device_profiles`), where a
  single failure aborts the whole batch without a precise "who moved / who
  did not" list.
- Two-phase (bulk POST then verify) — rejected: doubles the API call
  count and still cannot reconstruct partial-success ordering on a
  mid-batch abort.

---

## Decision 2: Retry policy on a single failed PUT

**Decision**: At most 2 retries per AP with a short exponential backoff
(0.5 s, then 1.0 s). After the second retry fails, mark that AP as failed,
update the backup file with the reassigned-so-far list, and stop the run
(no further PUTs). This matches FR-017 (stop on failure) and the spec
Assumption on retry policy.

**Rationale**: A single transient network hiccup should not abort a
500-AP migration, but a bounded retry keeps the failure blast radius
predictable. Total worst-case time cost per failing AP is 1.5 s of
backoff — negligible compared to Mist API latency variance. The bound of
2 retries matches the spec assumption and the pattern used by the
existing MistHelper CENR probe.

**Alternatives considered**:

- No retry (fail on first error) — rejected: too fragile for the
  documented 500-AP scale.
- Unbounded retry with jitter — rejected: hides Mist API outages from the
  operator and makes progress reporting misleading.

---

## Decision 3: Progress cadence

**Decision**: Print a `logger.info(...)` progress line at least every 10
APs (SC-004), formatted as
`"reassigning AP N of M: <ap-id> (<hostname>) at site <site-id>"`, and
always print the first and last AP regardless of the cadence.

**Rationale**: SC-004 sets the floor at every 10 APs. Printing at 1 and
M as well makes it obvious to the operator that the loop actually started
and finished. This is O(1) additional log volume per boundary — not a
performance concern.

**Alternatives considered**:

- Print every AP — rejected: 500 lines of log noise for a routine
  migration.
- Print by percentage buckets (10 percent, 20 percent, ...) — rejected:
  for small migrations (5 APs) the operator sees only one line.

---

## Decision 4: Backup file vs audit line — split

**Decision**: One JSON file per migration invocation (single logical
snapshot, matches spec Assumption). One JSONL audit line per revert
invocation via `TelemetryEmitter` (append-only stream, matches existing
telemetry pattern from feature 1020).

**Rationale**: A migration produces one snapshot that a revert reads
back verbatim — JSON is the correct shape. A revert produces one audit
event per invocation that never needs to be read back by the tool —
JSONL is the correct shape and reuses the already-tested
`TelemetryEmitter` code path without modification.

**Alternatives considered**:

- Single JSONL stream for both — rejected: makes the migration file hard
  to read back atomically and hard to browse by an operator scanning
  `data/` for the right backup to revert against.
- Full JSON blob for the audit too — rejected: revert may run many times
  across the org's lifetime; append-only NDJSON is what the existing
  pattern already handles.

---

## Decision 5: Confirmation keywords

**Decision**: Menu 207 uses uppercase typed keyword `MIGRATE`. Menu 208
uses uppercase typed keyword `REVERT`. Both are validated by the existing
`safe_input(...)` helper (NASA/JPL keyword-confirmation pattern already
used by other destructive menus).

**Rationale**: One typed keyword per operation prevents the operator from
confirming the wrong operation by muscle memory. `MIGRATE` and `REVERT`
are unambiguous single-word imperatives, satisfy the ASD-STE100 style
(active voice, imperative, dictionary word), and match the existing
uppercase-single-word convention.

**Alternatives considered**:

- Same keyword for both (`YES` or `CONFIRM`) — rejected: no protection
  against confirming the wrong menu.
- Long phrase — rejected: adds friction without adding safety beyond one
  unambiguous word.

---

## Decision 6: New module location and naming

**Decision**: New module at
`src/device/ap_profile_migration_manager.py` containing
`class APProfileMigrationManager` with two public static-method entry
points:

- `APProfileMigrationManager.migrate_aps_between_device_profiles()` — menu 207
- `APProfileMigrationManager.revert_ap_profile_migration()` — menu 208

**Rationale**: The operation acts on AP device objects, so
`src/device/` is the correct package. The static-method decomposition
pattern is the same one used by `SiteConfigManager` (menu 174) — small
private helpers, two public entry points. Naming follows the existing
`<Domain>Manager` convention (`SiteConfigManager`,
`OrgSyntheticProbesManager`, `DeviceRebootManager`, etc.).

**Alternatives considered**:

- Two modules (one per menu) — rejected: the two operations share the
  backup-file schema, the AP-discovery helper, and the profile-lookup
  helper. Splitting duplicates code without a clear boundary.
- Under `src/org/` (because device profiles are org-level objects) —
  rejected: the mutation target is a device (AP) object, and the AP
  discovery walks sites, so `src/device/` is more accurate.

---

## Decision 7: Backup file naming

**Decision**: Confirm the spec Assumption pattern verbatim:
`ap-profile-migration_<YYYYMMDDTHHMMSSZ>_<source-profile-id>_to_<target-profile-id>.json`.

**Rationale**: ISO 8601 basic format (`YYYYMMDDTHHMMSSZ`) sorts
chronologically as a plain string, which lets the revert menu list
backup files in newest-first order without parsing the filename.
Including both profile IDs in the filename lets an operator disambiguate
multiple backups from the same day.

**Alternatives considered**:

- Extended ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`) — rejected: `:` is
  problematic on Windows filesystems.
- Underscore-only separator — rejected: harder to grep for "from X to Y"
  patterns.

---

## Open questions

None. All FR-001 through FR-025 requirements have a mapped implementation
path; all spec Assumptions have been confirmed above.
