# Feature Specification: Test quality: repair remaining missing_fm_http_4xx findings

**Feature Branch**: `chore/2747-fm-http-4xx`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Orchestrator task for issue #2747. Repair the remaining `missing_fm_http_4xx` findings in the test-quality baseline. The issue title and body name the 5xx rule. See clarification C-1.

## Clarifications

### Session 2026-11-26

- Q: Which rule does this record repair? → A: `missing_fm_http_4xx` only. The orchestrator task names the 4xx rule. Issue #2747 names the 5xx rule. Issue #2746 holds the 4xx title. The 5xx rule stays out of scope (D-1 and D-10).
- Q: Where does a detector defect get repaired? → A: In misthelper-devtools, at a released commit that the devtools pin names. Local exclusions, opt-in markers, synthetic HTTP tests, and baseline edits do not repair a detector defect (D-2).
- Q: Which test file receives a new 4xx test? → A: The existing module that the finding names. A new module does not clear the baseline entry (D-3).
- Q: Does the pull request close an issue? → A: No. The pull request uses "Part of" references only (D-6).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classify each 4xx finding (Priority: P1)

A maintainer runs the pinned analyzer census. The maintainer assigns each `missing_fm_http_4xx` finding and each stale baseline entry to one family. Each family has one repair rule.

**Why this priority**: The 38 baseline entries do not share one cause. A repair without a family can add a false test or hide a real gap.

**Independent Test**: Run the census. Compare the triage table with the census report. The table holds one row for each baseline 4xx entry. Each census finding maps to one family.

**Acceptance Scenarios**:

1. **Given** the pinned analyzer, **When** the census runs, **Then** the report lists each 4xx finding and each stale baseline entry.
2. **Given** a 4xx finding, **When** the maintainer triages it, **Then** it has one family and cites its test and source lines.
3. **Given** the triage table, **When** the maintainer counts rows, **Then** the count equals the 4xx baseline entries plus unmatched census findings.

---

### User Story 2 - Add native 4xx tests for real gaps (Priority: P2)

For each F1 finding, the existing test module gains one native 4xx test. The test drives the source under test and asserts an observable failure signal. The test fails when the status guard that it covers is mutated in memory.

**Why this priority**: A real missing 4xx refusal path leaves the caller unprotected. The census decides whether any F1 finding exists.

**Independent Test**: Mutate the status guard in memory. The new test fails. Restore the guard. The test passes.

**Acceptance Scenarios**:

1. **Given** an F1 finding, **When** the native 4xx test runs on unmodified code, **Then** it passes and asserts the refusal, log, and SDK call count.
2. **Given** the status guard is mutated in memory, **When** the same test runs, **Then** the test fails at the refusal assertion.
3. **Given** the census holds no F1 finding, **When** this story closes, **Then** the record states zero test edits and cites the census evidence.

---

### User Story 3 - Repair detector noise and prune stale entries (Priority: P3)

F2 and F3 defects are repaired in misthelper-devtools. MistHelper pins the released commit, reruns the census, and writes the baseline with the documented command. The baseline diff removes only 4xx entries that the census marks stale or resolved.

**Why this priority**: Most findings come from detector behavior, not from missing tests. A test-only change would hide the detector defect.

**Independent Test**: After the pin change, the census reports zero new findings and zero parse errors. The baseline diff holds only removals of 4xx entries.

**Acceptance Scenarios**:

1. **Given** a nested-project test path, **When** the upstream fix runs, **Then** the census no longer reports a path-only applicability finding.
2. **Given** a real 4xx test that the slicer discards, **When** the upstream coverage fix runs, **Then** the census no longer reports that coverage finding.
3. **Given** the census lists a stale entry, **When** the baseline write runs, **Then** the diff removes that entry and adds no entry.

---

### Edge Cases

- A test drives the source only through an instance method. The coverage defect (F3) applies. Add no duplicate test.
- The imported source has no HTTP status guard. The finding cannot be a real gap (F1). Reclassify the finding as F2 or F4.
- A new F1 test passes under the mutation. The test does not prove the guard. Repair the test until it fails under the mutation.
- The upstream release is delayed. The pin stays at the current commit. The baseline stays unchanged. The record stays blocked on the release.
- A 4xx finding appears in a module that has no baseline entry. Triage the finding as a new row before merge. The gate reports it as new.
- A file is held by an open pull request. The file stays unchanged until that pull request closes. The current hold is `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` (PR #4208).
- A baseline entry names a deleted file. Use `--prune-baseline`, which removes entries for files that no longer exist.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST treat the pinned analyzer census as the authority for current 4xx findings before any repair.
- **FR-002**: Each baseline 4xx entry and each census 4xx finding MUST map to one family: F1, F2, F3, or F4.
- **FR-003**: Each F1 finding MUST receive one native 4xx test in its existing test module. The test MUST drive the source under test.
- **FR-004**: Each new F1 test MUST fail when the status guard that it covers is mutated in memory.
- **FR-005**: F2 findings MUST be repaired in the misthelper-devtools applicability inference. Exclusions, markers, and synthetic HTTP tests MUST NOT repair an F2 finding.
- **FR-006**: F3 findings MUST be repaired in the misthelper-devtools coverage inference. A duplicate test MUST NOT repair an F3 finding.
- **FR-007**: No hand-written opt-in marker, comment, or decorator MUST suppress a 4xx finding.
- **FR-008**: The baseline MUST change only by the documented write command, without `--roots` and without `--changed-from`. Each removed 4xx entry MUST match a stale or resolved finding.
- **FR-009**: The devtools pin MUST change only to a released commit. The census after the change MUST report zero new findings and zero parse errors.
- **FR-010**: New tests MUST use mocked boundaries and native response objects. No test MUST send a live Mist request or read a production credential.
- **FR-011**: New test code MUST carry an inline comment on each executable line. New test code MUST add no log statement (D-5).
- **FR-012**: Findings for the 5xx rule and for other rules MUST stay out of scope. Baseline entries for those rules MUST stay unchanged.
- **FR-013**: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` MUST NOT change while PR #4208 is open.
- **FR-014**: Each remote claim in `design/research.md` MUST have one remote verification row. Each claim without evidence MUST appear under Unverified.
- **FR-015**: The pull request body MUST use "Part of" references to #2747 and #2746. The body MUST NOT use a closing keyword.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The feature adds no REST request. Each test uses a native `requests.Response` or `mistapi.APIResponse` object with a mocked SDK boundary.
- The feature adds no owned WebSocket transport.
- Contract evidence for SDK status handling comes from `mistapi.APIResponse` (`.venv\Lib\site-packages\mistapi\__api_response.py`, line 48, research R-71).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The triage table has one row for each baseline 4xx entry. Each row names one family and one repair rule.
- **SC-002**: After the upstream fix and the pin change, the census reports zero new findings and zero parse errors.
- **SC-003**: Each new F1 test fails under its mutation and passes without it. The number of such tests equals the number of F1 rows.
- **SC-004**: Each local gate in `tasks.md` exits with the expected result for each changed file.
- **SC-005**: Remote CI reports each required check as passed on the pull request head before auto-merge.
- **SC-006**: The pull request changes only the files that `plan.md` lists.

## Out of Scope

- The 5xx rule, the weak-assertion rule, and the other test-quality rules.
- Product code under `src/`, `mist-ops-platform/src/`, and `web_portal/`.
- Live Mist calls and production credentials.
- `README.md`, `CHANGELOG.md` (the release coordinator owns it), and operator documentation. The one fragment under `changelog.d/` is in scope (D-8).
- Repositories other than MistHelper and misthelper-devtools.

## Assumptions

- The implementing environment can install `requirements-dev.txt` and run `test-quality-analyzer`.
- The baseline blob on `main` (512da22b0769e8343a4b5b734c507d6aa3969ac6) is the baseline that the triage uses.
- The upstream misthelper-devtools repository publishes a commit that the MistHelper pin can name.
- Test-quality findings stay file-level. The baseline line number for each 4xx entry is 1.

## Key Entities

See `design/data-model.md`.
