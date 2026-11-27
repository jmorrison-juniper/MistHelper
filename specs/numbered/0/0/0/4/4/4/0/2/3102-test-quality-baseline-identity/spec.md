# Feature Specification: Test-quality baseline identity by content

**Feature Branch**: `fix/3102-test-quality-baseline-identity`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue 3102, "The test-quality ratchet baseline drifts on any line move, failing unrelated pull requests", in `jmorrison-juniper/MistHelper`.

**Spec record**: `specs\numbered\0\0\0\4\4\4\0\2\3102-test-quality-baseline-identity`

## Problem

The baseline file records each accepted finding with its line number. The gate compares that line number. An edit above an accepted finding moves its line. The gate then reports the finding as new and fails an unrelated pull request.

The pinned comparator keys each finding on `line_number` (`baseline.py` line 55). Its diff uses dictionaries and sets (lines 96 to 101). After the line number leaves the key, a set-based diff would hide a second identical finding. The comparison must count occurrences.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A line move does not fail the gate (Priority: P1)

A contributor adds lines above an accepted finding. The gate stays green. Unrelated pull requests then pass.

**Why this priority**: The defect blocks pull requests that do not touch the flagged code. Operators then stop trusting the gate.

**Independent Test**: Insert one blank line above a live finding. Run the gate. Read the exit code and the output.

**Acceptance Scenarios**:

1. **Given** a live finding, **When** one blank line is inserted above it, **Then** the gate prints `gate: 0 new findings vs baseline` and exits 0.
2. **Given** a file-level finding at line 1, **When** a header line is inserted above line 1, **Then** the gate exits 0.

---

### User Story 2 - A real new finding fails the gate (Priority: P1)

A contributor adds a weak assertion or a second identical finding. The gate must fail. A reviewer then sees the real regression.

**Why this priority**: A ratchet that passes real regressions has no value.

**Independent Test**: Add one weak assertion to a test that already has an accepted finding. Run the gate.

**Acceptance Scenarios**:

1. **Given** a live finding in a test, **When** a weak assertion is added there, **Then** the gate prints one `gate_new:` line and exits 1.
2. **Given** two identical baseline occurrences, **When** a third identical finding appears, **Then** the gate exits 1.
3. **Given** a flagged statement whose text changes, **When** the gate runs, **Then** the changed finding is new and the gate exits 1.

---

### User Story 3 - Removed findings tighten the baseline (Priority: P2)

A finding disappears after a fix. The gate must not fail on that removal. The next prune must remove the stale entry, so that the stale entry cannot hide a later identical finding.

**Why this priority**: A stale entry lets one identical later finding pass without review.

**Independent Test**: Remove one flagged statement from a matched test. Run the gate. Then run the prune command.

**Acceptance Scenarios**:

1. **Given** a matched finding that no longer exists, **When** the gate runs, **Then** the gate exits 0 and prints `gate_removed: 1`.
2. **Given** a removed finding in an analyzed file, **When** the prune command runs, **Then** the baseline file no longer holds that entry.
3. **Given** a baseline entry for a file with a parse error, **When** the prune command runs, **Then** the entry remains in the baseline file.

---

### User Story 4 - The gate shows its evidence and fails closed (Priority: P2)

An operator reads the gate output and sees what the run measured. A broken input stops the run before any comparison.

**Why this priority**: The issue acceptance requires counts. The guard rule from issue 2689 requires that a guard fail when it cannot read its input.

**Independent Test**: Run the full-suite gate. Then remove the baseline file in a temporary copy and run the gate again.

**Acceptance Scenarios**:

1. **Given** a full-suite run, **When** the gate runs, **Then** the output contains a `gate_scope` line with a file count above 0.
2. **Given** a baseline entry without `content_anchor`, **When** the gate runs, **Then** the gate exits 2 and names the baseline error.

---

### User Story 5 - The baseline migrates without changing live acceptance (Priority: P2)

A maintainer regenerates the baseline with the new analyzer. Every live finding stays accepted. The pull request lists each dropped entry.

**Why this priority**: The baseline on main holds 733 entries, and some entries are stale. The migration must keep the accepted findings and show what it removes.

**Independent Test**: Write the baseline with the new analyzer. Compare the new entries with the entries on main.

**Acceptance Scenarios**:

1. **Given** the old gate exits 0 on main, **When** the migration writes anchors, **Then** the new gate exits 0 and line numbers stay unchanged.
2. **Given** the migration drops entries, **When** the pull request opens, **Then** the body lists each dropped entry and the total count.

---

### Edge Cases

- A flagged statement changes only its whitespace. The normalized anchor stays the same, so the gate exits 0.
- A test function renames or changes its signature. Its flagged line changes. The gate reports a new finding, by design.
- Two identical flagged statements exist in one file. The comparison counts two occurrences.
- An identical statement replaces a removed statement in the same file. The net count is zero, so the change is not detected. This residual risk is recorded in `research.md` decision D-4.
- A test file moves to another path. The file path is part of the key, so the gate reports the moved findings as new and the old entries as removed. Issue 4142 may cause such moves.
- A source module named by an untested-function finding cannot be read. The gate exits 2 and names the path.
- A pull request changes no test file. The gate exits 0 and prints `gate_scope: 0 files checked`.
- The baseline file is missing or malformed. The gate exits 2.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The gate MUST NOT report a finding as new when only its line number changes and its flagged line text stays the same.
- **FR-002**: The gate MUST report each occurrence of an identity key beyond the baseline count as a new finding.
- **FR-003**: The gate MUST report a finding as new when its flagged line text changes.
- **FR-004**: The gate MUST NOT fail when a baseline occurrence has no matching finding.
- **FR-005**: The prune command MUST remove each unmatched occurrence in a file that the run analyzed without a parse error.
- **FR-006**: The prune command MUST keep every baseline entry of a file that has a parse error or that the run did not analyze.
- **FR-007**: The gate MUST exit 2 when a baseline entry lacks a valid content anchor.
- **FR-008**: Each gate run MUST print the `gate_scope` line with the count of files and the count of findings.
- **FR-009**: Each gate run MUST print the `gate_removed` count for analyzed files.
- **FR-010**: A file-level finding MUST carry the sentinel anchor `file-level`, so that a header insertion does not change its identity.
- **FR-011**: The migration MUST write a content anchor for every retained entry and MUST keep each retained line number unchanged.
- **FR-012**: The migration MUST drop only entries that no current finding matches. The pull request MUST list each dropped entry.
- **FR-013**: The MistHelper test suite MUST prove the line-move and new-finding behaviors through the installed analyzer.
- **FR-014**: The MistHelper pin MUST name a misthelper-devtools release that contains FR-001 to FR-010 before the migration merges.
- **FR-015**: The change MUST add one changelog fragment and MUST update the test-quality documentation.
- **FR-016**: The change MUST leave the `test_quality_gate` job, its command, and its required check name unchanged.

### Key Entities *(include if feature involves data)*

- **Baseline entry**: A stored record of one accepted finding. Its identity key is `(category, rule_id, file_path, explanation, content_anchor)`.
- **Finding**: A result of one analyzer run. It carries a content anchor after the pipeline assigns one.
- **Content anchor**: The SHA-256 digest of the normalized flagged line, or the sentinel `file-level`.
- **Occurrence**: One counted unit of an identity key in the current or the baseline multiset.
- **Gate result**: The exit code, the counts, and the new and removed occurrences of one run.

The fields and transitions appear in `design/data-model.md`. The file formats appear in `design/contracts/`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After one blank line is inserted above a live finding, the gate exits 0 and prints `gate: 0 new findings vs baseline`.
- **SC-002**: After one weak assertion joins a test with an accepted finding, the gate exits 1 and prints `gate: 1 new findings vs baseline`.
- **SC-003**: After one matched finding is removed, the gate exits 0 and prints `gate_removed: 1`. The prune command then removes that entry.
- **SC-004**: With two identical baseline occurrences, a third identical finding exits 1, and a removed identical occurrence exits 0.
- **SC-005**: The full-suite gate prints a `gate_scope` line with a file count above 0.
- **SC-006**: After the migration, the gate exits 0 and each retained entry matches an entry on main by category, rule, file, line, and explanation.
- **SC-007**: The `Test quality ratchet (gate)` job passes on the pull request and on main after the merge.

## Out of Scope

- Detector rules, rule thresholds, and rule categories.
- The report contract file `report.schema.json` and the report JSON content.
- The CI job names, the job command, the required check names, and the reusable workflow pins.
- The CodeQL verdict register from issue 3069.
- The split of `tests/unit` into domain packages from issue 4142.
- The historical text of `documentation/development-tooling-migration.md`.
- The file `CHANGELOG.md`, which the release coordinator owns.

## Assumptions

- A1: The release that contains FR-001 to FR-010 ships before the MistHelper pin changes. The current pin `2239e7bd` equals upstream main and has no identity repair (`requirements-dev.txt` line 197, R-06).
- A2: The analyzer reads source files with universal newlines. Its line numbers match the flagged line text read the same way.
- A3: Each file-level finding comes from the `_finding` helper at `missing_failure_mode.py` line 760 (R-45).
- A4: Each source module named by an untested-function finding exists on main at check time (`untested.py` line 151, R-46).
- A5: The `test_quality_gate` job uses the analyzer exit code as its result (`ci.yml` lines 623-632, R-04).

## Clarifications

- Q1: Should removing an accepted finding fail the gate? A: No. Issue acceptance 3 requires that removal does not fail the gate. Decision D-6 applies.
- Q2: Should the identity use the test function name? A: No. The name is absent from 176 baseline entries. Decision D-2 uses a content anchor.
- Q3: Should the migration keep stale entries? A: No. The migration keeps live matches and lists each dropped entry. Decision D-8 applies.
- Q4: Does this record need a human decision? A: No. No category in section 6 of the brief applies.
- Q5: Can the MistHelper change start now? A: No. The upstream release is the blocker. Tasks T001 to T009 run first.

## Dependencies

- A misthelper-devtools release that contains the identity repair. Tasks T001 to T009 deliver it.
- Coordination with issue 4142 for future test file moves. A move changes file paths, and the migration must run again after the move.

Warning: a pushed release tag is public. Do not delete or move a release tag after it ships.
