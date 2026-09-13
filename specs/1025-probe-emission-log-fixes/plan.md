# Implementation Plan: Menu 206 Probe-Emission Log Quality & Correctness Fixes

**Branch**: `1025-probe-emission-log-fixes` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/1025-probe-emission-log-fixes/spec.md`

## Summary

Fix two log-noise / correctness defects in menu 206
(`manage_org_synthetic_probes`) that surfaced during a post-1024 log review:

1. **CENR warning storm (US1, P1)** — The per-emission
   `logger.warning("no observation for %s, using catalogue default %s", ...)`
   inside `_probe_target()` fires once per site per unobserved host. On a
   ~315-site org with ~4 unobserved SecB2B hosts this produces ~1,261 lines
   in `data/script.log`. Move the WARNING to a single load-time emission,
   deduplicated by hostname within a per-run set. Probe payloads stay
   byte-identical (INV-1 from 1024).
2. **LATAM/Caribbean mis-region (US2, P1)** — `_COUNTRY_CODE_TO_REGION`
   currently contains only 13 codes (US/CA/MX + 6 South American + 4 China).
   Central America and Caribbean codes (PA, BS, HT, DO, GT, CU, CR, HN, and
   the rest of ISO-3166 alpha-2) fall through to `_DEFAULT_REGION = "emea"`
   with a per-site WARNING. Extend the map to cover Central America and the
   Caribbean (mapped to `"americas"` — the value the Samsung-ELM roles use;
   see Research decision R1), introduce an explicit intentional-gap set for
   codes deliberately excluded, dedup the per-site warning to per-code, and
   guard both collections with an ISO-3166 alpha-2 coverage regression test.
3. **Regression coverage (US3, P2)** — Fixture-backed unit tests that count
   emitted WARNING records so a future refactor cannot silently reintroduce
   either log-noise pattern.

**Technical approach**: All changes are confined to
`src/org/org_synthetic_probes_manager.py` plus new/extended unit-test files
and one static ISO-3166 alpha-2 fixture. No new runtime dependency. No
schema-breaking telemetry change. No new class introduced — the target
module is entirely function-based today; per-run dedup state is threaded
through the existing `_probe_target()` / region-resolver call sites as an
explicit `dedup_state` parameter (see Research R2).

## Technical Context

**Language/Version**: Python 3.13+ (constitution binding minimum;
`pyproject.toml` `requires-python = ">=3.13"`).

**Primary Dependencies**: Standard library only (`logging`, `pathlib`,
`typing`). No new third-party dep. `pycountry` is explicitly rejected in
Research R3 in favour of a checked-in static ISO-3166 alpha-2 fixture.

**Storage**: No persistent state beyond the existing JSONL telemetry pattern
under `data/`. This feature adds no new telemetry sink; dedup state is
ephemeral (per-invocation set discarded at function return per FR-012).

**Testing**: `pytest` + `pytest-cov` (already in use). New fixtures live
under `tests/unit/org/fixtures/` following the pattern established by 1024
(`smoke_org.json`). One new fixture `iso_3166_alpha2.json` under
`tests/unit/org/fixtures/` provides the reference ISO code list for the
coverage regression test.

**Target Platform**: Linux container (production) + Windows 11 local dev
(operator workstation). No platform-specific code paths.

**Project Type**: Single-project Python CLI (menu-driven ops toolkit). No
web/mobile split. The touched module is a menu-206-scoped submodule under
`src/org/`.

**Performance Goals**: SC-007 caps the new regression tests at <5 seconds
wall-clock on the reference dev machine (fixture-driven, no network I/O).
Runtime cost of the dedup lookup is O(1) per emission (Python set
membership).

**Constraints**:
- **INV-1 (from spec 1024)**: All emitted probe payloads for non-VPN
  targets MUST remain byte-identical to the pre-change baseline. This is
  the hardest constraint — the WARNING move MUST NOT alter the target URL,
  the probe name, aggressiveness, or any other emitted field.
- **Ephemeral dedup state (FR-012)**: State MUST NOT persist across
  invocations. Two consecutive runs of menu 206 in the same Python session
  both re-emit their load-time WARNINGs.
- **ASCII-only log output (Constitution V)**: No Unicode / emoji in the new
  log messages.
- **Inline comments (Constitution VI, NON-NEGOTIABLE)**: Every new line
  needs a same-line `#` comment explaining *why*.
- **Action logging (Constitution VII, NON-NEGOTIABLE)**: Logging BEFORE
  and AFTER every meaningful action, `%s` formatting only.

**Scale/Scope**:
- Touched files: 1 production module + 2 test files + 1 test fixture
  (~250 total lines changed / added, well under a 5-file / 2-class limit).
- Affected menu: 206 only.
- Affected org sizes: any (fix is O(unique-missing-hosts), independent of
  site count — actually helps larger orgs more).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance | Notes |
|-----------|-----------|-------|
| I. Five-Item Rule | PASS | 1 module edited + 2 test files + 1 fixture = 4 files. No new function exceeds 25 lines or 5 blocks (dedup is a 3-line set membership check + guarded WARNING). |
| II. Class-Based Architecture | PASS with note | Target module `org_synthetic_probes_manager.py` is entirely function-based today (all `_`-prefixed helpers). Introducing a class solely for the dedup state would be inconsistent with the module's established pattern and would fail the "no wrappers" clause — the class would trivially wrap a dict/set. Dedup state is passed as an explicit parameter (Research R2). This is the *simpler* alternative and matches Principle II's spirit (semantically named ownership); see Complexity Tracking. |
| III. Safety-First | PASS | No new `input()` call. No destructive operation. No new secret/credential handling. |
| IV. Full Deployment Pipeline | DEFERRED | Applies at implement/merge time, not plan time. |
| V. Observability & Logging | PASS + INTENT | ASCII-only strings; `%s` formatting; the whole feature IS about logging quality. New WARNING wording preserves the diagnostic tokens operators grep for (host name, country code) per FR-013. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS BY DESIGN | Every new line will carry a `#` comment. Enforced during implementation. |
| VII. Action Logging (NON-NEGOTIABLE) | PASS BY DESIGN | The dedup path itself IS logging code, so `logging.info()` bookends the load-time summary block and `logging.debug()` records the deduped set size. Existing action logging in `_probe_target()` is preserved. |

**Result**: PASS. One point requires a Complexity Tracking entry
(Principle II — dedup state as parameter rather than class attribute); see
final section.

## Project Structure

### Documentation (this feature)

```text
specs/1025-probe-emission-log-fixes/
├── plan.md              # This file
├── research.md          # Phase 0 output — 5 design decisions with rationale
├── data-model.md        # Phase 1 output — dedup state, gap set, region map entities
├── quickstart.md        # Phase 1 output — validation guide for operators + CI
├── contracts/
│   ├── log_record_shape.md          # WARNING message shape + FR-013 grep-token guarantees
│   ├── iso_coverage_invariant.md    # ISO alpha-2 coverage regression test contract
│   └── byte_stability_invariant.md  # INV-1 restatement scoped to this feature
├── checklists/          # Already exists from /speckit.specify
└── tasks.md             # Phase 2 output (created by /speckit.tasks — NOT here)
```

### Source Code (repository root)

```text
src/
├── org/
│   ├── org_synthetic_probes_manager.py     # EDIT — dedup CENR WARNING (US1), extend region map + gap set (US2)
│   └── __init__.py                          # unchanged
└── utils/
    ├── zscaler_catalogue.py                 # unchanged (INV-1 boundary)
    └── zscaler_probe.py                     # unchanged

tests/
└── unit/
    └── org/
        ├── test_org_synthetic_probes_manager.py   # EXTEND — add US1/US2/US3 tests
        ├── test_country_region_coverage.py        # NEW — ISO alpha-2 coverage regression (US2/US3)
        └── fixtures/
            ├── smoke_org.json                     # reuse from 1024 (byte-stability baseline)
            ├── latam_caribbean_org.json           # NEW — synthetic org with PA/BS/HT/DO/GT/CU/CR/HN sites
            └── iso_3166_alpha2.json               # NEW — 249-code reference list for coverage test
```

**Structure Decision**: Single-project layout, already established.
No new package or module is introduced — all runtime changes live in the
existing `src/org/org_synthetic_probes_manager.py` module. Test coverage is
split across the existing feature-scoped test file and one new
coverage-invariant test file (kept separate so the ISO regression test can
be found by name from CI failure output).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Principle II — dedup state passed as function parameter rather than owned by a class attribute | The target module `org_synthetic_probes_manager.py` is entirely function-based today (`_load_probe_sources`, `_build_probe_set`, `_probe_target`, `_prompt_mode`, etc.). Introducing a `_ProbeEmissionRun` class solely to hold two sets would (a) be inconsistent with the surrounding pattern, (b) trivially wrap a dict and thereby violate Principle II's own "no wrappers" clause, and (c) require refactoring 5+ existing helpers to receive `self` rather than positional args, expanding blast radius well beyond the two documented touch sites. | A wrapper class was rejected because it would delegate zero behavior — it would be pure state. The dedup set is a private, ephemeral, per-invocation collection with lifetime bounded by `manage_org_synthetic_probes()`; a parameter thread models this lifetime exactly. If the module grows a class in a future refactor (e.g. issue 878-t8 tranche), dedup state can migrate to an attribute at that time with no external API change. |
