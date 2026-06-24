# Feature Specification: Eliminate Architectural-Hygiene + Parameter-Bloat Violations in `MistHelper.py` (ARCH-DELEGATE Cleanup)

**Feature Branch**: `refactor/431-arch-delegate-cleanup`
**Created**: 2026-06-23
**Status**: Draft
**Issue**: [#431](https://github.com/jmorrison-juniper/MistHelper/issues/431)
**Input**: User description: "Eliminate all 59 architectural-hygiene + parameter-bloat violations in `MistHelper.py` per the NON-NEGOTIABLE rule in `copilot-instructions.md` and `agents.md`: 'No wrappers: All functionality lives within appropriately named classes, never use standalone wrapper functions.' Inline ALL 38 delegators (including the 30 documented 'compatibility facades' from in-flight migration specs)."

## Problem / Goal *(mandatory)*

### Problem

`data/compliance_report.md` (snapshot 2026-06-23) flags `MistHelper.py` with **59** violations spread across seven categories that all stem from the same architectural root cause: the file accumulated a layer of standalone wrapper functions, module-scope aliases, and over-wide procedural signatures as classes were extracted into `src/` over specs #195 / #196 / #168 / #1002. The NON-NEGOTIABLE rule in `copilot-instructions.md` and `agents.md` reads:

> **"No wrappers: All functionality lives within appropriately named classes, never use standalone wrapper functions."**

The current state violates that rule in 59 distinct call sites and the overall compliance score is below 30/100.

### Goal

Drive every counted violation in the seven listed categories to **0** in `MistHelper.py` by inlining or eliminating each wrapper/alias/stub and by refactoring every 6-8 parameter signature down to ≤5 parameters via dataclass extraction.

### Violation Inventory (must reach 0)

| Category | Count | Source |
|----------|-------|--------|
| ARCH-DELEGATE (8 hand-rolled passthroughs + 30 migration-spec facades) | 38 | `data/compliance_report.md` |
| ARCH-NAMING (`_legacy`, `_compat`, `*_wrapper` in names) | 5 | `data/compliance_report.md` |
| ARCH-STUB (`stop_listening` no-op) | 1 | `data/compliance_report.md` |
| ARCH-ALIAS (`PacketCaptureManager = ExtractedPacketCaptureManager`) | 1 | `data/compliance_report.md` |
| STRUCT-PARAMS (functions with 6-8 params, target ≤5) | 12 | `data/compliance_report.md` |
| CONV-INPUT (bare `input()` at L2576) | 1 | `data/compliance_report.md` |
| CONV-PATH (hardcoded Windows drive separator at L12268) | 1 | `data/compliance_report.md` |
| **Total** | **59** | — |

### Non-Goals

- **No changes outside `MistHelper.py`** except: (a) the `data-model.md` / `tasks.md` status advances inside `specs/195/`, `specs/196/`, `specs/168/`, `specs/1002/`; (b) at most a single import-statement rename if `ExtractedPacketCaptureManager` is renamed in `src/capture/packet_capture.py` (see Edge Cases).
- **Do not** touch `src/`, `tools/`, `web_portal/`, `maps_manager.py`, `wsgi.py` (other than the one exception above).
- **Do not** address CONV-COMMENTS (inline-comment coverage 41.3 %) as a primary objective. It improves implicitly as tranches touch lines per the project's NON-NEGOTIABLE inline-comment rule; no dedicated sweep here.
- **Do not** introduce new wrappers, façades, or aliases to "ease" migration. The migration lifecycle terminates here.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Drive Architectural Compliance to Green (Priority: P1)

As a maintainer enforcing the "no wrappers" NON-NEGOTIABLE in `copilot-instructions.md`, I need every architectural-hygiene + parameter-bloat violation in `MistHelper.py` removed so the compliance gate stops flagging `MistHelper.py` for these categories and so future contributors cannot point to existing wrappers as license to add more.

**Why this priority**: The rule is labeled NON-NEGOTIABLE. Every violation that survives is a precedent that erodes the rule.

**Independent Test**: Run `python tools/check_compliance.py MistHelper.py`; ARCH-DELEGATE, ARCH-NAMING, ARCH-STUB, ARCH-ALIAS, STRUCT-PARAMS, CONV-INPUT, and CONV-PATH counters MUST all be 0.

**Acceptance Scenarios**:

1. **Given** the 2026-06-23 baseline with 59 violations across the seven categories, **When** the cleanup completes, **Then** `python tools/check_compliance.py MistHelper.py` reports 0 in every listed category.
2. **Given** the in-flight migration specs #195 / #196 / #168 / #1002, **When** their façade entries are inlined here, **Then** each spec's `data-model.md` status enum advances to `verified` (or `legacy-removed` if that spec uses the longer enum) and the corresponding final task is checked.
3. **Given** spec #429's ruff `G` rule sweep is already at 0, **When** this cleanup lands, **Then** `python -m ruff check --select G003,G004,G201 MistHelper.py` still reports 0 violations (no regression).

---

### User Story 2 - Preserve Runtime Behavior Across the Cleanup (Priority: P1)

As an operator running MistHelper in production, I need every inlined call site to behave identically to its pre-cleanup wrapper so that interactive prompts, file exports, packet captures, Mist API calls, and the bulk-RADIUS workflow remain byte-equivalent in user-visible behavior.

**Why this priority**: This is a behavior-preserving refactor of a 27 k-line operator tool. Any behavior drift is a silent production regression.

**Independent Test**: Full pytest suite passes unchanged; coverage ≥ 70 %; the new regression test in `tests/test_issue_431_canonical_imports.py` imports every public class listed in `tests/fixtures/issue_431_canonical_classes.json` from `MistHelper.py` and asserts each is identity-equal (`is`) to the canonical `src/` implementation (no façade interposed).

**Acceptance Scenarios**:

1. **Given** the pre-cleanup `MistHelper.py`, **When** the cleanup completes, **Then** all existing pytest suites pass unchanged with coverage ≥ 70 %.
2. **Given** a public class previously re-exported via a façade (e.g. `PacketCaptureManager`), **When** imported from `MistHelper` after cleanup, **Then** `MistHelper.PacketCaptureManager is src.capture.packet_capture.PacketCaptureManager` returns `True`.
3. **Given** a wrapper-removed call site for `_safe_input` / `save_data_to_output` / `_mist_get_wrapper`, **When** the same code path runs post-cleanup, **Then** stdout, file output, and HTTP behavior match the pre-cleanup baseline.

---

### User Story 3 - Reviewable Phased Delivery (Priority: P2)

As a reviewer of a 59-site architectural cleanup, I need the work split into reviewable, independently CI-green tranches so a faulty inlining can be bisected and reverted without losing the whole sweep.

**Why this priority**: A single-PR mega-refactor of 59 sites across 27 k lines is unreviewable in practice and high-blast-radius.

**Independent Test**: Inspect commit history on `refactor/431-arch-delegate-cleanup`; each tranche commit MUST pass full CI (ruff, black, mypy, pytest+cov, bandit, pip-audit, CodeQL, Playwright) independently and leave `MistHelper.py` internally consistent.

**Phased Delivery (must appear in the spec for the reviewer)**:

1. **Tranche 1** — Trivial single-line fixes (4 sites): ARCH-STUB, ARCH-ALIAS, CONV-INPUT (L2576), CONV-PATH (L12268).
2. **Tranche 2** — 8 hand-rolled passthroughs: `_safe_input`, `_get_actual_import_name`, `get_import`, `save_data_to_output`, `_mist_get_wrapper`, `select_device`, `DateTimeHandler.__call__`, `__getattr__`.
3. **Tranche 3** — ARCH-NAMING (5 sites): rename `*_legacy` / `*_compat` / `*_wrapper` symbols and update every call site inside `MistHelper.py`.
4. **Tranche 4** — 30 migration-spec façades, split into sub-tranches per owning spec: #195, #196, #168, #1002.
5. **Tranche 5** — 12 STRUCT-PARAMS: collapse 6-8-param signatures via dataclass extraction.
6. **Final commit** — Advance spec `data-model.md` status enums, check the corresponding `tasks.md` final tasks, append CHANGELOG entry with UTC `YY.MM.DD.HH.MM` timestamp, snapshot the final compliance report.

**Acceptance Scenarios**:

1. **Given** 59 sites to clean, **When** the work is committed, **Then** there are 5 tranche commits + 1 final commit (sub-tranches inside Tranche 4 may add 2-4 commits).
2. **Given** any single tranche commit, **When** CI runs against that commit alone, **Then** all quality gates pass and `MistHelper.py` remains internally consistent.

### Edge Cases

- **Dunder methods that look like delegators**: `DateTimeHandler.__call__` and `__getattr__` are listed under the 8 hand-rolled passthroughs. They MUST be examined individually before deletion — `__getattr__` in particular may implement legitimate dynamic-attribute access rather than a true wrapper. Inlining is only valid where the dunder body is a pure passthrough.
- **`_safe_input` (L21303) used pervasively by `BulkRadiusConfig`**: removal MUST either inline the body at every call site OR (preferred) replace every call site with a direct `InputUtils.safe_input(...)` call. Do not introduce a new wrapper. Count of call sites MUST be enumerated in `plan.md`.
- **`save_data_to_output` (L8006) marked "backward compatibility"**: every call site MUST migrate to the canonical `DataExporter.write_with_format_selection(...)` (or whichever `src/exporters/` method is the documented successor). The cleanup task in `plan.md` MUST list the exact replacement.
- **`PacketCaptureManager = ExtractedPacketCaptureManager` (L6277)**: two valid resolutions — (a) rewrite every reference inside `MistHelper.py` to `ExtractedPacketCaptureManager`, OR (b) rename the class to `PacketCaptureManager` inside `src/capture/packet_capture.py` (single-statement change there + update one import in `MistHelper.py`). Option (b) is preferred *only if* the rename is contained to a single import-statement change. `plan.md` MUST pick one and justify.
- **30 migration-spec façades**: each removal opens a `tasks.md` checkbox in the originating spec (#195 / #196 / #168 / #1002). A follow-up table in `tasks.md` MUST track which spec / which task is checked by which removal.
- **`stop_listening` no-op stub**: if no caller exists, delete it outright; if callers exist, replace each with the canonical stop method on the owning class.
- **CONV-PATH L12268**: hardcoded `\\` drive separator must move to `pathlib.Path` / `os.path.join` so the line is portable across Windows / Linux / container runtimes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `MistHelper.py` MUST contain 0 ARCH-DELEGATE violations after the cleanup (was 38).
- **FR-002**: `MistHelper.py` MUST contain 0 ARCH-NAMING violations (was 5) — no symbol name may contain `_legacy`, `_compat`, or `_wrapper` (case-insensitive).
- **FR-003**: `MistHelper.py` MUST contain 0 ARCH-STUB violations (was 1) — the `stop_listening` no-op is removed or replaced.
- **FR-004**: `MistHelper.py` MUST contain 0 ARCH-ALIAS violations (was 1) — no module-scope `Name = OtherName` re-binding for class aliases.
- **FR-005**: `MistHelper.py` MUST contain 0 STRUCT-PARAMS violations (was 12) — every function signature in `MistHelper.py` has ≤5 parameters (excluding `self` / `cls`).
- **FR-006**: `MistHelper.py` MUST contain 0 CONV-INPUT violations (was 1) — the bare `input()` at L2576 is replaced with `InputUtils.safe_input(...)` (or the project's documented prompt helper).
- **FR-007**: `MistHelper.py` MUST contain 0 CONV-PATH violations (was 1) — L12268 uses `pathlib.Path` / `os.path.join` instead of a hardcoded `\\` drive separator.
- **FR-008**: For every removed migration-spec façade, the originating spec's `data-model.md` status MUST advance from `delegated` to `verified` (specs using the short enum) or `legacy-removed` (specs using the longer enum, e.g. #195), and the corresponding `tasks.md` final task MUST be checked.
- **FR-009**: Every public class previously re-exported via a façade in `MistHelper.py` MUST be importable from `MistHelper` after cleanup AND MUST be identity-equal (`is`) to its canonical `src/` implementation.
- **FR-010**: No new wrapper, façade, alias, `*_legacy`, `*_compat`, or `*_wrapper` symbol may be introduced as part of this cleanup. The migration lifecycle terminates here.
- **FR-011**: CHANGELOG.md MUST gain a new entry with UTC `YY.MM.DD.HH.MM` timestamp summarizing the cleanup and citing issue #431.
- **FR-012**: A fresh `data/compliance_report.md` snapshot MUST be committed in the final commit; the overall compliance score MUST climb above 30/100.

### Key Entities

- **Wrapper / Façade / Alias / Stub**: the unit of removal. Each has a known line number in `MistHelper.py` per `data/compliance_report.md` (2026-06-23 snapshot).
- **Migration Spec** (#195 / #196 / #168 / #1002): owns one or more façades scheduled for terminal removal here. Each carries a `data-model.md` status enum that this cleanup advances.
- **STRUCT-PARAMS Function**: a 6-8 parameter function whose parameter list collapses into a dataclass passed as a single argument plus ≤4 remaining scalars.

## Success Criteria *(mandatory)*

### Measurable Outcomes (Acceptance Criteria — verbatim from issue #431)

- **SC-001**: `python tools/check_compliance.py MistHelper.py` reports **0** ARCH-DELEGATE, **0** ARCH-NAMING, **0** ARCH-STUB, **0** ARCH-ALIAS, **0** STRUCT-PARAMS, **0** CONV-INPUT, **0** CONV-PATH.
- **SC-002**: `python -m ruff check --select G003,G004,G201 MistHelper.py` still reports **0** (#429 must not regress).
- **SC-003**: All existing CI quality gates pass: ruff, black, mypy, pytest+cov, bandit, pip-audit, CodeQL, Playwright.
- **SC-004**: Coverage **≥ 70 %**.
- **SC-005**: Specs #195 / #196 / #168 / #1002 `data-model.md` entries advanced to `verified` / `legacy-removed`; their `tasks.md` updated to check the corresponding final task.
- **SC-006**: `CHANGELOG.md` entry with UTC `YY.MM.DD.HH.MM` timestamp.
- **SC-007**: Overall compliance score climbs **above 30/100**.

## Interfaces & Behavior *(mandatory)*

### Public Import Surface

- `MistHelper` module continues to expose every public class it exposed before the cleanup. The mechanism changes from "façade defined locally" to "direct re-export of the canonical `src/` class via `from src.X import Y`".
- Identity-equality (`MistHelper.Y is src.X.Y`) MUST hold for every public class previously re-exported.

### CLI / Operator Behavior

- Interactive prompts that previously routed through `_safe_input` route through `InputUtils.safe_input` directly. User-visible prompt text and validation behavior MUST be unchanged.
- File export paths that previously routed through `save_data_to_output` route through `DataExporter.write_with_format_selection` (or the documented successor). Resulting file path, filename, and content MUST be unchanged.
- Packet-capture references that previously used the alias `PacketCaptureManager` continue to work (either via direct reference to the renamed class or via updated call sites).

### Non-Interfaces

- No new public API is added.
- No deprecated public API is removed (the wrappers/façades being removed are private to `MistHelper.py`'s internal organization; the public surface is the canonical `src/` class either way).

## Constraints / Performance *(mandatory)*

- **Scope confinement**: edits are restricted to `MistHelper.py` plus the four migration-spec `data-model.md` / `tasks.md` pairs plus `CHANGELOG.md` plus `data/compliance_report.md` plus the at-most-one optional rename in `src/capture/packet_capture.py`. Touching any other file fails review.
- **Tranche atomicity**: every tranche commit MUST leave `MistHelper.py` syntactically valid, importable, and CI-green. No tranche may rely on a follow-up tranche to restore consistency.
- **No new wrappers**: the cleanup must not introduce a new layer of indirection to ease the diff. Direct call sites only.
- **Performance**: this is a behavior-preserving refactor; no measurable runtime regression is expected and none is acceptable. Removing wrappers should be a marginal positive (one fewer call frame).

## Security & Secrets *(mandatory)*

- No secret handling code paths are altered.
- The CONV-INPUT fix (replacing bare `input()` with `InputUtils.safe_input`) marginally *improves* input hygiene because `safe_input` is the project's vetted prompt helper.
- No new external network calls, file writes, or subprocess invocations are introduced.
- `bandit` and `pip-audit` MUST continue to pass at the existing baseline.

## Test Plan *(mandatory)*

### Existing Suite

- All existing `pytest` suites under `tests/` MUST pass unchanged.
- Coverage gate ≥ 70 % MUST continue to hold.

### New Regression Tests (added under `tests/`)

1. **`tests/test_issue_431_canonical_imports.py`** — import every public class listed in `tests/fixtures/issue_431_canonical_classes.json` from `MistHelper` and assert each `is` identity-equal to the canonical `src/` implementation. Fails if any façade is reintroduced.
2. **`tests/test_issue_431_ruff_g_rules_zero.py`** — invoke `ruff check --select G003,G004,G201 MistHelper.py` via subprocess and assert exit code 0 + empty output. Guards against #429 regression.
3. **`tests/test_issue_431_compliance_zero.py`** — invoke `python tools/check_compliance.py MistHelper.py` and assert ARCH-DELEGATE, ARCH-NAMING, ARCH-STUB, ARCH-ALIAS, STRUCT-PARAMS, CONV-INPUT, and CONV-PATH counters all equal 0.

### Fixture

- **`tests/fixtures/issue_431_canonical_classes.json`** — snapshot mapping `{ "PublicClassName": "src.module.path.PublicClassName" }` for every public class currently re-exported from `MistHelper`. Generated in Tranche 1, frozen thereafter.

### Per-Tranche Gate

- Each tranche commit MUST pass: ruff, black, mypy, pytest+cov, bandit, pip-audit, CodeQL, Playwright.

## Migration / Compatibility *(mandatory)*

- **Internal-only migration**: the wrappers/façades being removed are private to `MistHelper.py`. The public surface (the `src/` classes) is unchanged.
- **Migration-spec lifecycle**: the user has explicitly resolved that the "no wrappers" rule overrides the 4-state migration lifecycle. Façades documented in specs #195 / #196 / #168 / #1002 are removed in Tranche 4. For each removal:
  - Advance `data-model.md` status from `delegated` to `verified` (short enum) or `legacy-removed` (long enum, spec #195).
  - Check the corresponding `tasks.md` final task.
  - Note the removal in this spec's `tasks.md` follow-up table (generated by `/speckit.tasks`).
- **No deprecation window**: removal is immediate. There is no operator-facing breakage because there is no operator-facing surface change.
- **Rollback**: per-tranche commits enable surgical revert if a faulty inlining is bisected post-merge.

## Acceptance Criteria *(mandatory — verbatim from issue #431)*

1. `python tools/check_compliance.py MistHelper.py` reports 0 ARCH-DELEGATE, 0 ARCH-NAMING, 0 ARCH-STUB, 0 ARCH-ALIAS, 0 STRUCT-PARAMS, 0 CONV-INPUT, 0 CONV-PATH.
2. `python -m ruff check --select G003,G004,G201 MistHelper.py` still reports 0 (#429 must not regress).
3. All existing CI quality gates pass (ruff, black, mypy, pytest+cov, bandit, pip-audit, CodeQL, Playwright).
4. Coverage ≥ 70 %.
5. Specs #195 / #196 / #168 / #1002 `data-model.md` entries advanced to `verified` / `legacy-removed`; their `tasks.md` updated to check the corresponding final task.
6. CHANGELOG.md entry with UTC `YY.MM.DD.HH.MM` timestamp.
7. Overall compliance score climbs above 30/100.

## Implementation Notes (AI hints) *(mandatory)*

- **Single source of truth for violation list**: `data/compliance_report.md` (2026-06-23 snapshot). All line numbers in this spec reference that snapshot. If the file shifts during cleanup, regenerate the report and reconcile.
- **Order matters within Tranche 4**: handle façades for spec #195 first (longest enum, most documented context), then #196, then #168, then #1002. Sub-tranche per owning spec.
- **STRUCT-PARAMS pattern**: prefer `@dataclass(frozen=True, slots=True)` for the extracted parameter struct. The dataclass lives in `src/` if there is an obvious home, otherwise in `MistHelper.py` near its consumer (single consumer, internal to the file).
- **`_safe_input` removal**: enumerate all call sites once, replace every site with `InputUtils.safe_input(...)`. Do not leave `_safe_input` defined.
- **`save_data_to_output` removal**: locate the canonical successor in `src/exporters/` before starting; do not invent one.
- **`PacketCaptureManager` alias**: decide between in-file rename (option a) vs `src/` rename (option b) during `/speckit.plan`. Default to option (a) if option (b) would require touching any caller outside `MistHelper.py`.
- **Per-tranche CHANGELOG note is optional**; one consolidated CHANGELOG entry in the final commit is required.
- **Inline-comment rule reminder**: the NON-NEGOTIABLE inline-comment rule applies to every line touched. Each replacement site MUST gain an inline comment explaining the inlined logic if one is not already adjacent.

## UI Behavior & Automated Testing *(mandatory)*

**N/A** — this is a server-side / CLI architectural cleanup of `MistHelper.py`. There are no web UI changes; Playwright suites continue to run unchanged as a regression guardrail only.

## Assumptions

- The 2026-06-23 `data/compliance_report.md` snapshot is current as of plan execution. If the file changes during the cleanup window, the count of 59 may shift; the goal is "zero in these seven categories", not "remove exactly 59 things".
- Every façade flagged by ARCH-DELEGATE has a canonical successor already living in `src/`. If a façade is found whose successor does not yet exist in `src/`, escalate to NEEDS DECISION rather than inventing one.
- `InputUtils.safe_input` is the canonical prompt helper. (Verified during `/speckit.plan` against `src/`.)
- `DataExporter.write_with_format_selection` (or the documented equivalent under `src/exporters/`) is the canonical successor for `save_data_to_output`. (Verified during `/speckit.plan`.)
- CI quality gates (ruff, black, mypy, pytest+cov, bandit, pip-audit, CodeQL, Playwright) are wired and currently green on `main`.
- The user has explicitly chosen to override the documented 4-state migration lifecycle in specs #195 / #196 / #168 / #1002 in favor of the NON-NEGOTIABLE "no wrappers" rule.
