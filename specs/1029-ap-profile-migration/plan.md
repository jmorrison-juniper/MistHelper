# Implementation Plan: Migrate APs Between Device Profiles (with Revert)

**Branch**: `1029-ap-profile-migration` | **Date**: 2026-07-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/1029-ap-profile-migration/spec.md`

## Summary

Add two new MistHelper menu operations that move Access Points between
org-level device profiles safely:

- **Menu 207 — Migrate APs from one device profile to another (DESTRUCTIVE)**:
  discover every AP whose `deviceprofile_id` equals a chosen source profile
  ID (by walking every site in the org via
  `mistapi.api.v1.sites.devices.listSiteDevices(..., type="ap")`), write a
  single pre-change JSON backup under `data/` (source-profile JSON,
  target-profile JSON, org ID, timestamp, ordered AP list), then PUT each
  AP with `deviceprofile_id` = target ID via
  `mistapi.api.v1.sites.devices.updateSiteDevice`. Progress prints every
  10 APs. On the first PUT failure, stop, record the exact list of APs
  actually reassigned into the backup file, and name the failing AP.
- **Menu 208 — Revert an AP profile migration from its backup file
  (DESTRUCTIVE)**: pick a backup file from `data/`, validate every field
  named in FR-013, verify the original source-profile ID still exists in
  the org, then PUT each listed AP back to that source profile ID.
  Missing APs are skipped with a warning; a JSONL audit line is appended
  via the existing `TelemetryEmitter` (matching feature 1020's shape).

Both operations are registered in `src/utils/operation_registry.py` with
`category = "destructive"` and a `skip_reason` string that names the
operation. Both require a typed uppercase confirmation keyword
(`MIGRATE` and `REVERT`) via the standard `safe_input()` helper before
any PUT is issued. A dry-run mode on menu 207 (chosen at the
confirmation prompt) prints the same plan the live run would print,
writes no backup, and issues no PUT.

The implementation adds one new class-based module
(`src/device/ap_profile_migration_manager.py`) that owns both menu
handlers as static methods, with the same static-method decomposition
pattern already used by `SiteConfigManager` (menu 174) — small, testable
helpers behind two public entry points. The device-side binding
mechanism (`PUT /sites/{site_id}/devices/{device_id}` with body
`{"deviceprofile_id": "<target>"}`) is preferred over the bulk
`assignOrgDeviceProfile` endpoint because per-AP transactional
granularity is required by FR-017 (stop on first failure, record the
exact partial-success set).

## Technical Context

**Language/Version**: Python 3.13+ (per constitution binding minimum
and `pyproject.toml` py313 target).

**Primary Dependencies**: `mistapi >= 0.63.1` (verified installed
surface `0.63.3`); standard library only for everything else
(`json`, `datetime`, `pathlib`, `logging`, `time`). No new third-party
dependency (FR-003).

**Storage**: Local files under `data/` only.

- One JSON snapshot per migration invocation:
  `data/ap-profile-migration_<UTC-timestamp>_<source-profile-id>_to_<target-profile-id>.json`
  (see `data-model.md`).
- One append-only JSONL audit line per revert invocation via the
  existing `TelemetryEmitter` (best-effort; matches feature 1020's
  pattern).

**Testing**: `pytest` with `pytest-mock` and `caplog`. New tests
co-locate under
`tests/unit/device/test_ap_profile_migration_manager.py`. Fixtures
capture mocked `mistapi` sessions and simulated site/device
inventories to cover: empty source set (FR-010), same-profile refusal
(FR-008), successful full migration (US1), mid-run PUT failure with
partial-success backup update (FR-017), dry-run (US3), revert against a
valid backup (US2), revert when source profile is missing (FR-021),
revert when a listed AP has since been removed (FR-023), and backup
malformed / missing fields (FR-020).

**Target Platform**: Cross-platform Python CLI (macOS, Linux, Windows).
`pathlib.Path` for all paths; UTF-8 explicit encoding on every open.

**Project Type**: Single-project CLI (`MistHelper.py` menu-driven).
Applies existing `src/` and `tests/` layout — no new top-level
directories.

**Performance Goals**: One migration handles up to 500 APs (SC-001).
Progress prints at least every 10 APs (SC-004) so no perceived freeze
longer than a few seconds under normal Mist API latency. Bounded retry
per AP (at most 2 retries with short backoff) prevents runaway loops.

**Constraints**:

- All operator-visible strings pass the ASD-STE100 lint (SC-007,
  FR-002) — no phrasal verbs, no Latin abbreviations, one term per
  concept, active voice, imperatives lead with the condition ("If X,
  do Y").
- Docstring coverage on changed files stays at or above 90 percent
  (FR-004); every added function, method, class, and module carries a
  Google-style docstring with a "Why" section per `DOCS.md`.
- No new destructive-registry lint failure and no new coverage
  regression (SC-006). Both menu entries added to
  `src/utils/operation_registry.py` with `category = "destructive"`.
- Backup file is written before the first PUT (FR-011). If the write
  fails, no PUT is issued.
- Never re-use `mistapi.api.v1.orgs.devices.assignOrgDeviceProfile`
  (the bulk `body={"macs":[...]}` path). Per-AP `updateSiteDevice` PUT
  is required for FR-017 per-AP failure granularity — see
  `research.md` for the trade-off analysis.

**Scale/Scope**: Two menu entries; one new module (~350 LOC estimated,
class + static methods); one new unit-test module (~30-40
assertions); no new top-level packages. Backup file typical size on a
500-AP org is a few hundred KB (two full device-profile JSONs + 500
AP records of about 100-200 bytes each).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.4.0 (seven Core
Principles).

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | Both menu handlers use a single class (`APProfileMigrationManager`) with static-method decomposition. Each helper stays under 5 items of local complexity by design — the top-level handler orchestrates, and each helper does one thing (discover, back-up, confirm, PUT-loop, summarize). |
| II. Class-Based Architecture | PASS | `APProfileMigrationManager` in `src/device/ap_profile_migration_manager.py` mirrors the pattern of `SiteConfigManager` (menu 174) and `OrgSyntheticProbesManager` (menu 206). Public entry points are `migrate_aps_between_device_profiles()` and `revert_ap_profile_migration()`, both class-level static methods. |
| III. Safety-First (Destructive Operations) | PASS | Both operations register as `destructive` in `operation_registry.py` (FR-001). Both require an uppercase typed keyword via `safe_input()` (`MIGRATE` / `REVERT`) that names the exact source and target profile IDs and the count of APs (FR-005). Menu 207 offers a dry-run at the confirmation prompt (FR-015). Backup is written before the first PUT (FR-011). On first failure, the backup file is updated with the actual reassigned set (FR-017). |
| IV. Full Deployment Pipeline | PASS | Feature ships behind existing CI (ruff, black, mypy, pytest, interrogate, pydoclint, ASD-STE100 lint, destructive-registry guardrail). No new gates required — SC-006 asserts the guardrail passes without modification. |
| V. Observability (Action Logging non-negotiable) | PASS | Every menu entry logs a `logger.warning("Menu #207 DESTRUCTIVE: ... started")` at start (matches existing pattern), `logger.info(...)` for each successful PUT ("reassigned AP <id> from <source> to <target>"), `logger.error(...)` on PUT failure with AP ID and error, and a final `logger.info(...)` summary line. Revert emits a JSONL audit line via `TelemetryEmitter` (FR-025). |
| VI. Inline Comments For Non-Obvious Blocks | PASS | The retry policy (bounded, then stop), the pre-PUT backup-write-must-succeed check, the target/source equality refusal, and the JSONL audit best-effort swallow are each annotated with a short `#` comment explaining the constraint. |
| VII. Documentation Coverage (>=90 percent) | PASS | Every added function, method, class, and module carries a Google-style docstring with a "Why" section per `DOCS.md`. `interrogate` >=90 percent gate holds; `pydoclint --style=google` passes. |

**Gate result**: PASS (zero variances).

## Project Structure

### Documentation (this feature)

```text
specs/1029-ap-profile-migration/
|-- plan.md              # This file
|-- spec.md              # Feature spec (input)
|-- research.md          # Phase 0 output (short — most research done in specify)
|-- data-model.md        # Phase 1 output — backup file + audit-line schema
|-- quickstart.md        # Phase 1 output — runnable validation scenarios
|-- contracts/           # Phase 1 output (empty for this feature; see below)
`-- tasks.md             # Phase 2 output (created by /speckit.tasks — NOT this command)
```

`contracts/` is intentionally empty for this feature. MistHelper does
not expose external APIs; the only "interfaces" this feature adds are
(a) two interactive menu handlers whose contract lives in `spec.md`
FR-001 through FR-025, and (b) the backup JSON schema and revert-audit
JSONL line, both fully specified in `data-model.md`. Adding a separate
`contracts/` file would duplicate `data-model.md` without new
information.

### Source Code (repository root)

```text
src/
|-- device/
|   `-- ap_profile_migration_manager.py   # NEW — the class + two static
|                                         # menu handlers (menu 207 + 208)
|-- utils/
|   `-- operation_registry.py             # MODIFIED — two new entries
|                                         # (207, 208) with
|                                         # category = "destructive"
`-- analytics/
    `-- telemetry_emitter.py              # UNCHANGED — reused as-is
                                          # for the revert audit line

MistHelper.py                             # MODIFIED — wire menu options
                                          # 207 and 208 into the menu
                                          # dispatch (existing pattern)

tests/
`-- unit/
    `-- device/
        `-- test_ap_profile_migration_manager.py  # NEW — see Testing
                                                  # section under
                                                  # Technical Context

data/                                     # No new committed files.
                                          # At runtime:
                                          # - one JSON per migration
                                          # - JSONL audit line appended
                                          #   by existing telemetry file
```

**Structure Decision**: Existing single-project CLI layout under `src/`
and `tests/` is preserved. The new module goes under `src/device/`
because the operation acts on device (AP) objects. The static-method
decomposition pattern from `SiteConfigManager` (menu 174) is reused so
the class stays discoverable to the existing menu dispatch, and each
helper stays inside the Five-Item Rule limit. Menu numbers 207 and 208
are the next available slots after the current maximum destructive
menu number (206).

## Complexity Tracking

> No violations. This section is empty by design.

The feature introduces no exceptions to constitutional principles. The
class-based container matches Principle II directly; all helpers are
methods on that class, not free functions. No new dependency, no new
top-level package, no new CI gate. The backup-vs-audit split (single
JSON snapshot for the migration state; append-only JSONL for the revert
audit) follows the spec's explicit assumption and matches the existing
`TelemetryEmitter` pattern already used elsewhere in MistHelper.
