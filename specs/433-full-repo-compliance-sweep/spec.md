# Feature Specification: Full-Repo Compliance Sweep (#433)

**Branch**: `refactor/433-full-repo-compliance-sweep`
**Created**: 2026-06-23
**Issue**: https://github.com/jmorrison-juniper/MistHelper/issues/433
**Status**: In progress (Phase A starting)

## Problem / Goal

`MistHelper.py` was cleaned up by #429 + #431 but the rest of the repository carries the bulk of the compliance debt. Full-repo scan (2026-06-23) shows **3,800 violations across 395 files** -- a 7x multiplier over the per-`MistHelper.py` tracking we have been using.

### Goal

Drive 4 specific compliance debts to zero / passing scores:

1. **Target A** -- `src/` G-rule violations: **789 -> 0**, remove the `src/**` per-file-ignore from `pyproject.toml`.
2. **Target B** -- `src/firmware/site_auto_upgrade.py` score: **27/F -> >=70/C-**.
3. **Target C** -- `src/maps/maps_manager.py` score: **40/F -> >=70/C-**.
4. **Target D** -- 5 critical-severity STRUCT-COMPLEXITY violations across the repo: **5 -> 0**.

### Non-goals

- Touching `MistHelper.py` (already done by #429 + #431).
- Decomposing every F-grade file (this issue covers A + B + C + D only; ~15 other F-grade files remain for future issues).
- New features, API changes, behavior changes.

## User Scenarios & Testing

### User Story 1 -- Operator confidence in `src/` logging hygiene (Priority: P1)

As an operator running MistHelper at INFO/WARN/ERROR level in production, I need every `logging.*` call in `src/` to defer string formatting until the record is rendered. The 662 G004 + 126 G201 + 1 G003 sites currently cost CPU on every disabled log level and prevent adoption of structured-logging handlers.

**Independent Test**: `python -m ruff check --select G003,G004,G201 src/` exits 0.

### User Story 2 -- Maintainable worst-file decomposition (Priority: P1)

As a maintainer touching `src/firmware/site_auto_upgrade.py` (worst-scored file in the repo) or `src/maps/maps_manager.py` (largest file in the repo, 6,387 lines), I need the file decomposed into smaller, single-responsibility classes so changes are reviewable.

**Independent Test**: each file scores >= 70/C- under `python tools/check_compliance.py <path>`.

### User Story 3 -- Zero critical-severity hotspots (Priority: P1)

As a release engineer signing off on a quality gate, I need zero functions whose cyclomatic complexity is >=20 (the critical-severity threshold) anywhere in the codebase. Today there are 5: CC 92, 77, 30, 24, 23.

**Independent Test**: `python tools/check_compliance.py --recursive .` reports `"critical": 0`.

### Edge Cases

- **G201 inside non-except blocks**: ruff flags `logging.error(..., exc_info=True)` only inside `except` clauses; the codemod must handle both forms (rename inside except, leave alone outside).
- **maps_manager.py Dash callbacks**: many functions are decorated as Dash callbacks, which have their own signature constraints. Decomposition extracts the body into a service class while keeping the decorator + thin entry-point in maps_manager.
- **Logging through `getattr`-chained loggers** (`self.log.info(...)`, `self._logger.warning(...)`): #429's codemod already handles these patterns; reuse without modification.
- **External-protocol signatures** (Flask routes, Dash callbacks, requests adapters): use `# noqa: STRUCT-PARAMS` exemption added in #431 Tranche 5B.

## Requirements

### Functional Requirements

- **FR-001**: After Phase A, `python -m ruff check --select G003,G004,G201 src/` MUST report 0 violations.
- **FR-002**: After Phase A, `pyproject.toml` `[tool.ruff.lint] per-file-ignores` MUST NOT contain `"G"` for `src/**`, `web_portal/**`, `tools/**`, `starlink_dashboard.py`, `maps_manager.py`, or `wsgi.py`.
- **FR-003**: After Phase B, `tools/check_compliance.py src/firmware/site_auto_upgrade.py` score >= 70/C-.
- **FR-004**: After Phase C, `tools/check_compliance.py src/maps/maps_manager.py` score >= 70/C-.
- **FR-005**: After Phase D, `tools/check_compliance.py --recursive .` reports `"critical": 0`.
- **FR-006**: All existing pytest suites pass on every phase commit.
- **FR-007**: Coverage stays >= 70% on every phase commit.
- **FR-008**: No new wrappers, facades, aliases, `*_legacy`, `*_compat`, or `*_wrapper` symbols (per `agents.md`).
- **FR-009**: Every executable line touched gains an inline comment per the NON-NEGOTIABLE inline-comment rule.
- **FR-010**: Every action gains action-logging (info before, debug after) per the NON-NEGOTIABLE action-logging rule.
- **FR-011**: CHANGELOG.md entry with UTC `YY.MM.DD.HH.MM` timestamp on each phase commit.

## Success Criteria

- **SC-001**: src/ G-rule total: 789 -> 0.
- **SC-002**: site_auto_upgrade.py score: 27 -> >=70.
- **SC-003**: maps_manager.py score: 40 -> >=70.
- **SC-004**: Repo critical-severity count: 5 -> 0.
- **SC-005**: All CI quality gates pass (ruff, black, mypy, pytest+cov, bandit, pip-audit, CodeQL, Playwright).
- **SC-006**: Repo-level compliance score climbs from 86.1 to >= 90 (B -> A-).
- **SC-007**: CHANGELOG.md entry added.
- **SC-008**: No regression of #429/#431 fixes (MistHelper.py compliance score stays at or above 34).

## Interfaces & Behavior

- Zero public-API change.
- Zero CLI surface change.
- Zero log-content change (lazy `%s` formatting renders byte-identical strings to eager f-strings).

## Constraints / Performance

- AST-based codemod only (libcst) -- regex sweeps prohibited.
- Per-phase commits CI-green independently.
- Decomposition follows the established serial-cc pattern from #195/#196: extract into `src/<package>/services/` modules with constructor DI, keep entry-point as canonical class (no wrapper layer).

## Security & Secrets

- Manual audit of any logging site referencing variables matching `(?i)(token|password|secret|cred|key)` before each tranche commits.
- Decomposition must not widen access to credential-bearing values.

## Test Plan

- All existing pytest suites continue to pass.
- New regression tests per phase:
  - Phase A: `tests/test_issue_433_src_g_no_regress.py` shell-out to `ruff --select G src/` and assert exit 0.
  - Phase B / C: per-extracted-class unit tests on new public surfaces; coverage preserved.
  - Phase D: per-function cyclomatic-complexity assertion via the analyzer.

## Migration / Compatibility

- No data migration.
- No operator-facing changes.
- `pyproject.toml` `per-file-ignores` shrinks after Phase A.
- CHANGELOG.md gains one entry per phase commit.

## Acceptance Criteria

1. `ruff check --select G003,G004,G201 src/` reports 0.
2. `pyproject.toml` `per-file-ignores` no longer contains G-suppressions.
3. `tools/check_compliance.py src/firmware/site_auto_upgrade.py` score >= 70.
4. `tools/check_compliance.py src/maps/maps_manager.py` score >= 70.
5. `tools/check_compliance.py --recursive .` reports `"critical": 0`.
6. All CI quality gates pass.
7. Coverage >= 70%.
8. CHANGELOG.md entry per phase commit.

## Implementation Notes (AI hints)

### Phase A -- src/ G-rule sweep (highest leverage, mechanical)

- Tool: `tools/codemod_logging_lazy.py` (proven on `MistHelper.py` in #429, 1,099 sites).
- Scope: every `*.py` under `src/`.
- Procedure: run codemod, format with black, run ruff, run tests, commit.
- After completion: remove `"src/**"`, `"tools/**"`, `"web_portal/**"`, `"starlink_dashboard.py"`, `"maps_manager.py"`, `"wsgi.py"` entries from `pyproject.toml` `[tool.ruff.lint.per-file-ignores]` (these were added in #429's lock-in commit as scope-out shields).

### Phase B -- site_auto_upgrade.py decomposition

- Current: 1,285 lines, 64 violations, score 27/F.
- Pattern: split into orchestration vs. data-fetch vs. reporting service classes under `src/firmware/site_auto_upgrade/` (move file to a package with sibling modules).
- Reference: spec #195's serial-cc decomposition pattern (`src/refactors/serial_cc/*` extractions).

### Phase C -- maps_manager.py decomposition

- Current: 6,387 lines, 347 violations, score 40/F, contains CC 77 (`get_map_data`) and CC 92 (`_launch_flask_viewer` in sibling `viewer_callbacks.py`).
- Approach: split into 4-5 sub-packages: `src/maps/dash_app/` (UI), `src/maps/data/` (fetching/processing), `src/maps/import_export/` (file IO), `src/maps/server/` (Flask + viewer launching).
- Note: Dash callback decorators stay attached to thin entry points; bodies move into service classes.

### Phase D -- remaining critical hotspots

After Phase C the maps-related criticals (CC 92, 77, 24) should fall out. That leaves:

- `tools/compliance_analyzer/audit::audit` (CC 30) -- the audit-log analyzer itself.
- `src/firmware/<...>::_process_one_batch` (CC 23) -- may be in `site_auto_upgrade.py` itself and fall out of Phase B.

Each remaining hotspot gets standard guard-clause + helper-extraction treatment.

## UI Behavior & Automated Testing

**N/A** -- no web UI behavior changes. Playwright suite runs unchanged as regression guardrail.

## Assumptions

- Codemod at `tools/codemod_logging_lazy.py` works on `src/` without modification (proven on `MistHelper.py` which uses the same logger patterns).
- The `_get_<X>_impl()` global-config pattern (uncovered in #431) is concentrated in `MistHelper.py`-side facades; `src/` classes themselves use proper constructor DI and do not need restructuring for Phase A.
- Existing tests provide enough coverage to catch decomposition regressions; gaps will be filled per-phase as discovered.
- Repo-wide compliance score climbing to >= 90 is achievable within these 4 targets because Targets B + C alone remove ~400 violations and Target A removes ~789.
