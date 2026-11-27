# Feature Specification: Native Report Failure-Boundary Tests

**Issue**: #4783 "Test quality: native report tests miss failure-boundary checks"

**Status**: Draft

**Route**: `specs\numbered\0\0\1\2\3\1\1\3\4783-native-report-failure-boundary-tests`

**Related issue**: #4773 "feat(web-portal): add EX transceiver master report and CLI collection"

**Created**: 2026-11-26

**Input**: Test-quality ratchet findings from the committed changes for #4773.

## Glossary

- **Chain**: The four local commits of #4773 that create the hardware test modules. They are `5e3868f87`, `8140bb37c`, `58ab484ba`, and `07cf3eec5`.
- **Chain tip**: Commit `07cf3eec5`, the last commit of the chain.
- **Raw reply**: Device output as bytes, before any decoding.
- **Native text**: Decoded XML or JSON text that the report writer stores.
- **Native file**: A stored XML or JSON artifact in a test temporary folder.
- **Master report**: The file `transceivers-master.csv`.
- **Source-driving helper**: A module-level test function that calls repository source.
- **Marker-only code**: Code that adds a detector marker without a real boundary.
- **Test-quality gate**: The `test-quality-analyzer --gate` run that CI requires.
- **Finding**: One row of analyzer output.

## Clarifications

### Session 2026-11-26

- Q: Does GitHub hold the chain? A: No. GitHub returns HTTP 422 for all four commit SHAs (research R28 to R31).
- Q: Does main hold the hardware test modules? A: No. Main holds none of the three named test modules (research R15 to R19).
- Q: Can a class staticmethod count as source-driving? A: No. The detector bridges only module-level helper functions (research R35).
- Q: Can an empty-body test enter the product at a real boundary? A: Yes. The decoder accepts raw bytes (research R22).
- Q: Can this change branch from the chain? A: No. AGENTS.md requires a branch from main only.
- Q: Who decides whether unfinished chain code lands on main? A: The human owner decides. Decision D-2 records the recommendation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Refuse an empty raw reply at the byte boundary (Priority: P1)

Maintainers need proof that an empty device reply never becomes an inventory or a file. The proof enters through the product byte boundary.

**Why this priority**: An empty reply that passes would publish a false zero-module inventory.

**Independent Test**: Run the normalization and report test modules. The empty cases pass, and each one enters through the decoder with `b""`.

**Acceptance Scenarios**:

1. **Given** an empty raw reply, **When** the decoder reads it for the `xml` or `json` command, **Then** it raises `HardwareOutputError`.
2. **Given** empty native text, **When** the report writer publishes it, **Then** the result is `output_failed`, and no native file or master report exists.

### User Story 2 - Refuse malformed JSON and keep the evidence (Priority: P1)

Maintainers need proof that malformed saved JSON fails the report. The native bytes must stay unchanged.

**Why this priority**: Malformed JSON must never count as a valid inventory, and the operator must keep the collected evidence.

**Independent Test**: Run the malformed JSON cases in both modules. The normalizer error must wrap `json.JSONDecodeError`, and the report manifest must record one failed source.

**Acceptance Scenarios**:

1. **Given** the text `{"chassis-inventory":`, **When** the normalizer reads it as JSON, **Then** it raises `HardwareOutputError` with a `json.JSONDecodeError` cause.
2. **Given** that text saved as the native file, **When** the report finishes, **Then** the manifest result is `failed`, and the native bytes stay unchanged.

### User Story 3 - Pass the gate without changing the baseline or the settings file (Priority: P2)

Maintainers need the test-quality gate to pass on the committed change. The pass must rest on real evidence, not from a baseline or settings edit.

**Why this priority**: A changed baseline hides findings. The repository rule forbids that change.

**Independent Test**: Run the gate with the changed-from scope and with the full suite. Compare the blob SHAs of the baseline and the settings file with main.

**Acceptance Scenarios**:

1. **Given** the committed change, **When** the gate runs with `--changed-from origin/main`, **Then** it prints `gate: 0 new findings vs baseline`.
2. **Given** the committed change, **When** the blob SHAs are compared with main, **Then** the baseline and the settings file match main.

### User Story 4 - Use exact assertions in the changed tests (Priority: P2)

Maintainers need each changed assertion to compare an exact value. A truthiness check does not prove the expected state.

**Independent Test**: Read the assertion that admits a run in `test_contracts.py`. It must compare `manager.started is True`.

**Acceptance Scenarios**:

1. **Given** an admitted start, **When** the test reads the manager state, **Then** the assertion compares the value with `is True`.

### Edge Cases

- A reply of only whitespace fails at the prompt check, not as an empty inventory. The decoder must refuse it.
- A reply with invalid UTF-8 bytes fails with `HardwareOutputError`. No native file exists after that failure.
- A valid zero-module reply still publishes a header-only master report. The empty-body fix must not refuse it.
- In a both-format run, one empty source keeps its own refusal reason. The valid source still publishes.
- A malformed JSON file in the report does not change the native bytes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The test modules MUST prove that an empty raw reply fails at the product byte boundary.
- **FR-002**: The empty raw reply MUST be bytes, `b""`, that enter `HardwareXmlSupport.Decoder.decode_output`. Marker-only code is prohibited.
- **FR-003**: The normalizer malformed JSON test MUST assert that the `HardwareOutputError` cause is `json.JSONDecodeError`.
- **FR-004**: The report malformed JSON test MUST assert one failed source in the manifest and unchanged native bytes.
- **FR-005**: The report empty test MUST assert `output_failed`, no native file, and no master report.
- **FR-006**: Each boundary test MUST call repository source directly or through a source-driving helper.
- **FR-007**: The contracts test MUST compare the manager state with `is True`, not with truthiness.
- **FR-008**: The test-quality gate MUST print `gate: 0 new findings vs baseline` for the changed scope and for the full suite.
- **FR-009**: The baseline and the settings file MUST keep the blob SHAs that main holds.
- **FR-010**: No file under `src/` MUST change. The change MUST add no product behavior.
- **FR-011**: `ReportRun` MUST become the module-level function `create_report_run`. Every call site MUST change, and no alias MUST remain.
- **FR-012**: Each new or changed function MUST have 25 lines or fewer, five parameters or fewer, and five logical blocks or fewer.
- **FR-013**: Each changed line MUST have an inline comment. The publication helper MUST log before and after the publication call.
- **FR-014**: Implementation MUST start after the chain is on GitHub and decision D-2 is recorded. A stacked branch is prohibited.
- **FR-015**: The change MUST add one changelog fragment named `issue-4783-native-report-failure-boundary-tests.md`.
- **FR-016**: The analyzer blind spot and the six-child test folder MUST be tracked in separate issues. This change MUST NOT fix either one.

### Mist Cloud Transport Requirements *(not applicable)*

Not applicable: the change adds tests only. It adds no mistapi call, no Mist REST request, and no WebSocket transport.

### Key Entities *(include if feature involves data)*

- **Raw reply**: Device output as bytes. The decoder receives it first.
- **Native text**: The decoded XML or JSON text. The report writer stores it.
- **Native file**: The stored artifact. A refused reply produces no native file.
- **Master report**: The CSV that exists only after a successful run.
- **Source-driving helper**: A module-level test function that calls repository source.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The changed-scope gate prints `gate: 0 new findings vs baseline` with exit code 0.
- **SC-002**: The full-suite gate prints `gate: 0 new findings vs baseline` with exit code 0.
- **SC-003**: The pytest run for the four changed test modules passes, including the seven changed cases in `plan.md`.
- **SC-004**: The baseline blob SHA is `512da22b0769e8343a4b5b734c507d6aa3969ac6`, and the settings blob SHA is `d0c88405e03f11e71b1fc8fe9238f14936991da7`.
- **SC-005**: The commit that carries this fix changes no path under `src/`.
- **SC-006**: Each FR maps to at least one task and at least one planned test.
- **SC-007**: The pull request body names each gate result, the symbol-diff output, and the Principle IV exception.

## Assumptions

- The chain reaches GitHub before implementation starts. Task T001 checks this.
- The pinned devtools commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` defines the analyzer that CI runs.
- The decoder keeps its current signature and its strict UTF-8 decoding. A change to either requires a new spec.
- The prompt value does not change the empty-reply outcome. The tests use `mist@EX>`, as `test_native.py` does.
- Device output is UTF-8. The byte boundary refuses other encodings.

## Out of Scope

- Changes to the analyzer, its rules, its severity map, or the pinned devtools commit.
- Changes to `.github/test-quality-baseline.json` or `.github/test-quality-config.toml`.
- The #4773 menu entry, README entry, and entry-point wiring in `MistHelper.py`.
- The six-child layout of `tests/unit/websocket_streams/web/hardware/`.
- Mist API behavior, mistapi calls, and the owned WebSocket transport.
- Container, port, and operator documentation changes.
