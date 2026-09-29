# Feature Specification: Spectrum RF Diagnostics

**Feature Branch**: `feat/3570-spectrum-rfdiag`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 290 spectrum analysis and RF diagnostic recording. An RF problem needs a spectrum scan or a client RF recording. Mist offers a spectrum analysis endpoint pair and an rfdiag recording start, stop, and download set. The download alone sits in the endpoint catalog. No operation runs the full flow. The operation offers two modes. Spectrum: ask for a site and an AP, start the analysis, poll the running state, and print the result. Recording: ask for a site and a client MAC, start the recording, wait for the operator or a duration, stop it, download the file under data/rfdiags/, and print the path. It writes RfDiagnostics.csv with each run."

## Background

Operators need one guided RF diagnostic flow for site issues. Today, they must know several Mist actions and run them by hand. The new menu 290 flow gives two safe choices:

- Spectrum analysis for an AP at a site.
- Client RF diagnostic recording for a client at a site.

The feature is limited to the RF diagnostic package and its unit tests. Integration wiring is recorded in `specs/3570-spectrum-rfdiag/wiring.md` and completed later from that manifest.

## Definitions

- **Spectrum analysis**: A scan for RF conditions around one access point at one site.
- **RF diagnostic recording**: A client RF recording that starts, stops, and downloads one file.
- **Run**: One operator attempt to do spectrum analysis or RF diagnostic recording.
- **Operator wait**: A pause that ends when the operator presses a key, the chosen duration ends, or the operator interrupts the wait.
- **Diagnostic file name**: A download name that includes the site, client MAC, and run time.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run AP spectrum analysis (Priority: P1)

An operator selects menu 290, chooses spectrum mode, selects a site and an AP, confirms the action, and receives the scan result.

**Why this priority**: Spectrum analysis is the fastest diagnostic check for many RF problems and needs no client file download.

**Independent Test**: Use a site and AP test double. Confirm the operation asks for confirmation, starts analysis only after `y`, polls until the running state ends, prints the result, and records the run.

**Acceptance Scenarios**:

1. **Given** the operator selected spectrum mode, **When** the operator chooses a site and AP and answers `y`, **Then** the operation starts the scan, waits for completion, and prints the result.
2. **Given** the operator selected spectrum mode, **When** the operator answers `N` or presses Enter at the start prompt, **Then** no scan starts and the operation records a cancelled run.
3. **Given** the scan stays running for several checks, **When** the operation polls the state, **Then** it keeps waiting until a final state or a clear failure is available.

---

### User Story 2 - Record client RF diagnostics (Priority: P1)

An operator selects menu 290, chooses recording mode, selects a site and client MAC, confirms the action, records for a chosen wait, stops the recording, downloads the file, and receives the saved path.

**Why this priority**: Client RF recordings capture evidence that support teams need when an RF issue affects one client.

**Independent Test**: Use a site, client, wait, interrupt, and file-system test double. Confirm the operation starts only after `y`, always tries to stop after a wait interruption, downloads under `data/rfdiags/`, prints the path, and records the run.

**Acceptance Scenarios**:

1. **Given** the operator selected recording mode, **When** the operator chooses a site and client MAC and answers `y`, **Then** the operation starts the recording and enters the wait.
2. **Given** a recording is in progress, **When** the operator wait reaches the chosen duration, **Then** the operation stops the recording, downloads the file, and prints the saved path.
3. **Given** a recording is in progress, **When** Ctrl+C interrupts the wait, **Then** the operation still requests stop before it exits or downloads.
4. **Given** the operator answers `N` or presses Enter at the start prompt, **When** recording mode is ready to start, **Then** no recording starts and no file download occurs.

---

### User Story 3 - Keep a run audit trail (Priority: P2)

An operator or maintainer reviews RF diagnostic runs in `data/RfDiagnostics.csv` and sees one row per attempt.

**Why this priority**: Operators need a durable record of what was tried, when it happened, and where output was saved.

**Independent Test**: Run spectrum, recording success, cancelled start, and failed run cases. Confirm each run writes one row with the selected mode, site, target, status, time, and result reference.

**Acceptance Scenarios**:

1. **Given** any spectrum or recording run starts, **When** the operation reaches a final outcome, **Then** `data/RfDiagnostics.csv` contains one row for that run.
2. **Given** a recording download succeeds, **When** the run row is written, **Then** the row includes the downloaded file path.
3. **Given** a run is cancelled before start, **When** the run row is written, **Then** the row shows cancelled status and no remote action result.

---

### User Story 4 - Prove request and wiring shape (Priority: P2)

A maintainer can review tests and the wiring manifest before integration. The evidence shows that request bodies match the OpenAPI schemas and that menu wiring work is explicit.

**Why this priority**: Correct request shape prevents Mist API failures, and deferred wiring must stay visible.

**Independent Test**: Review unit tests for the RF diagnostic package. Confirm the tests assert each start, stop, and spectrum request body shape. Review `wiring.md` for the deferred menu and registry wiring list.

**Acceptance Scenarios**:

1. **Given** spectrum mode starts, **When** tests inspect the start request body, **Then** it matches the documented OpenAPI schema fields for that action.
2. **Given** recording mode starts and stops, **When** tests inspect the request bodies, **Then** each body matches the documented OpenAPI schema fields for that action.
3. **Given** implementation is ready for integration, **When** maintainers open `wiring.md`, **Then** it lists the deferred menu, registry, endpoint catalog, and changelog wiring work.

### Edge Cases

- The operator declines the `y` or `N` prompt.
- The operator presses Enter at a `y` or `N` prompt. The default is `N`.
- Ctrl+C interrupts the recording wait after a recording starts.
- The spectrum analysis reports a failure or never leaves running before the allowed poll limit.
- The recording stop request fails after a recording starts.
- The recording download fails or returns no file content.
- The client MAC has separators or letter case that are unsafe for a file name.
- The site name or identifier contains characters that are unsafe for a file name.
- `data/rfdiags/` does not exist before download.
- `data/RfDiagnostics.csv` does not exist before the first run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The operation MUST present menu 290 as one RF diagnostics operation with spectrum and recording modes.
- **FR-002**: Spectrum mode MUST ask the operator for a site and an AP before it can start analysis.
- **FR-003**: Recording mode MUST ask the operator for a site and client MAC before it can start recording.
- **FR-004**: Before spectrum analysis starts, the operation MUST ask a `y` or `N` confirmation question and MUST treat Enter or any answer other than `y` as `N`.
- **FR-005**: Before RF diagnostic recording starts, the operation MUST ask a `y` or `N` confirmation question and MUST treat Enter or any answer other than `y` as `N`.
- **FR-006**: Spectrum mode MUST start analysis only after confirmation, poll the running state, and print the final result or a clear failure message.
- **FR-007**: Recording mode MUST start recording only after confirmation, wait for operator stop or a chosen duration, request stop, download the recording, and print the saved file path.
- **FR-008**: Recording mode MUST request stop when Ctrl+C interrupts the wait after recording starts.
- **FR-009**: Recording downloads MUST be saved under `data/rfdiags/`.
- **FR-010**: Recording download names MUST include the site, client MAC, and run time in a file-system safe form.
- **FR-011**: The operation MUST write `data/RfDiagnostics.csv` with exactly one row for each run attempt.
- **FR-012**: Each audit row MUST include the mode, site, selected AP or client MAC, start time, final status, and result reference when one exists.
- **FR-013**: Request bodies for spectrum analysis, recording start, and recording stop MUST follow the OpenAPI schema for the matching Mist action.
- **FR-014**: Unit tests MUST assert the shape of each request body used by spectrum analysis, recording start, and recording stop.
- **FR-015**: A wiring manifest MUST exist at `specs/3570-spectrum-rfdiag/wiring.md` and MUST list deferred menu, registry, endpoint catalog, and changelog work.
- **FR-016**: A changelog fragment MUST exist before implementation is complete.
- **FR-017**: The feature scope MUST stay bounded to package `src/troubleshooting/rf_diagnostics` and tests under `tests/unit/troubleshooting/rf_diagnostics`, except for deferred integration files listed in `wiring.md`.
- **FR-018**: The operation MUST use safe prompts with clear cancellation behavior for all operator input.
- **FR-019**: The operation MUST never print secrets, tokens, or raw credentials in run output, audit rows, or failure messages.

### Scope Boundaries

- In scope: RF diagnostic flow design for `src/troubleshooting/rf_diagnostics`.
- In scope: Unit test design for `tests/unit/troubleshooting/rf_diagnostics`.
- In scope: The `data/RfDiagnostics.csv` audit output and `data/rfdiags/` recording output behavior.
- Deferred: Menu, operation registry, endpoint catalog, and changelog integration. The deferred work is listed in `wiring.md`.
- Out of scope for this specification step: Edits to source files, tests, README, root feature state, and commits.

### Key Entities *(include if feature involves data)*

- **RfDiagnosticRun**: One operator attempt. It has mode, site, target AP or client MAC, start time, final status, and result reference.
- **SpectrumAnalysisSession**: One AP spectrum scan. It has site, AP, running state, final result, and failure reason when one exists.
- **RfDiagnosticRecording**: One client recording. It has site, client MAC, start response, stop response, downloaded path, and final outcome.
- **RfDiagnosticFile**: One downloaded recording file. It has a safe name, location under `data/rfdiags/`, source site, source client MAC, and run time.
- **WiringManifest**: A planning artifact that lists deferred integration tasks and their required files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of spectrum and recording starts require an explicit `y` answer before any remote action starts.
- **SC-002**: 100% of recording waits interrupted by Ctrl+C request recording stop before the operation returns control to the operator.
- **SC-003**: 100% of successful recording downloads are saved under `data/rfdiags/` with site, client MAC, and run time in the name.
- **SC-004**: 100% of run attempts write exactly one row to `data/RfDiagnostics.csv`.
- **SC-005**: Unit tests cover spectrum success, spectrum decline, recording success, recording decline, Ctrl+C stop, download naming, request body shape, and audit row output.
- **SC-006**: An operator can complete the happy path for either mode with no more than five required prompts after choosing menu 290.
- **SC-007**: A maintainer can identify all deferred integration files from `wiring.md` in less than two minutes.
- **SC-008**: The operation gives a clear printed outcome for 100% of success, cancel, stop failure, poll failure, and download failure cases.

## Assumptions

- Operators already have access to the relevant Mist organization, site, AP, and client information.
- The AP and client selectors can use existing project selection patterns.
- The client MAC is normalized for requests and made file-system safe for downloads.
- A cancelled confirmation is still a run attempt for the audit row.
- The default wait choice for recording can be operator stop or a finite duration, as long as the operation states the active wait mode clearly.
- The CSV audit file can be created when it does not exist.
- Integration into menu and registry files is deferred until the planning and implementation steps use `wiring.md`.
