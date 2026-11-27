# Feature Specification: Restore -LiteralPath in the setup scripts

**Feature Branch**: `fix/4910-routed-literal-path`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4910, "Routed setup scripts dropped the 1.4.3 -LiteralPath hardening." The routed port replaced `Test-Path -LiteralPath` with `Test-Path` for the optional document checks. Restore the hardening. Add a guard that fails when a setup script drops it again.

**Related**: Issue #4873 (routed port to Spec Kit 1.4.3). Issue #4910 does not depend on issue #4873 closing.

## Terms

- **Probe**: a `Test-Path` or `Get-ChildItem` call that reads a path.
- **Literal probe**: a probe that passes `-LiteralPath`. Wildcard characters have no meaning in a literal probe.
- **Bare probe**: a `Test-Path` call without `-LiteralPath`, or a `Get-ChildItem -Path` call.
- **Scoped scripts**: the four setup scripts that the guard reads. See Clarifications.
- **Optional document**: `research.md`, `data-model.md`, the `contracts` folder, or `quickstart.md` under a feature folder.
- **Feature folder**: the folder that holds one spec record.
- **Bracket folder**: a feature folder whose name holds the characters `[` and `]`.

## Clarifications

### Session 2026-11-26

- Q: Which scripts does the guard cover? A: Four scripts that prepare a feature folder: `check-prerequisites.ps1`, `setup-plan.ps1`, `setup-tasks.ps1`, and `create-new-feature.ps1`. `update-agent-context.ps1` and `common.ps1` stay out of scope.
- Q: Does the fix cover `Get-ChildItem -Path`? A: Yes. The contracts check reads its folder in the same condition as its `Test-Path`. A wildcard read on that line still gives a wrong state.
- Q: Which channel carries the action logs? A: `Write-Verbose` for info lines and `Write-Debug` for debug lines. Both stay silent by default, so the text and JSON output do not change.
- Q: Where does the guard live? A: In `tests/guardrails/test_routed_core_port.py`. That file holds the guards for the 1.4.3 routed rules. A new file in `tests/guardrails` would add a child to a folder that already holds 81 tracked children.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Optional documents appear in a bracket folder (Priority: P1)

An agent runs the prerequisite check or the task setup for a bracket folder. The script lists each optional document that exists in the folder. The routed port lists none of them, because the wildcard read hides the files.

**Why this priority**: The agent reads the wrong document state and takes the wrong next step. The failure gives no error.

**Independent Test**: Create a bracket folder that holds `design/research.md`. Run `check-prerequisites.ps1 -Json` and `setup-tasks.ps1 -Json`. Verify that both lists name `design/research.md`.

**Acceptance Scenarios**:

1. **Given** a bracket folder that holds `design/research.md`, **When** the agent runs `check-prerequisites.ps1 -Json`, **Then** `AVAILABLE_DOCS` names `design/research.md`.
2. **Given** the same bracket folder, **When** the agent runs `setup-tasks.ps1 -Json`, **Then** `AVAILABLE_DOCS` names `design/research.md`.
3. **Given** a bracket folder with no optional document, **When** either script runs, **Then** the script exits with code 0 and lists no optional document.

---

### User Story 2 - The guard fails when a probe is bare (Priority: P1)

A maintainer changes a scoped script or merges an upstream sync. The guard reads each scoped script line by line. It fails when a probe is bare, and it names the script and the line.

**Why this priority**: The routed port lost the hardening with no failing test. The guard stops the same loss in a future sync.

**Independent Test**: Run the guard on the repository. Run its self-check on synthetic lines. The guard passes on the repository and fails on each bare form.

**Acceptance Scenarios**:

1. **Given** the four scoped scripts with literal probes only, **When** the guard runs, **Then** it reports the probe lines it examined and passes.
2. **Given** a scoped script that holds `Test-Path $paths.RESEARCH`, **When** the guard runs, **Then** it fails and names the script and the line.
3. **Given** a scoped script that cannot be read, **When** the guard runs, **Then** it fails and reports that it examined 0 lines.

---

### User Story 3 - Spec creation checks the spec file with a literal probe (Priority: P2)

An operator creates a feature with `create-new-feature.ps1`. The script checks the spec file and the spec template with literal probes. The spec file is written as before.

**Why this priority**: The same wildcard risk applies to the spec file. The risk is lower because the file name is fixed, but the guard requires the literal probe.

**Independent Test**: Run the generator tests in `tests/guardrails/test_spec_route_contract.py`. They create a record and check its files. They pass as before.

**Acceptance Scenarios**:

1. **Given** a new feature, **When** the operator runs the generator, **Then** the spec file is written from the template as before.
2. **Given** the generator source, **When** the guard runs, **Then** both probes in `create-new-feature.ps1` use `-LiteralPath`.

### Edge Cases

- A folder name with `*` or `?` cannot exist on Windows. The behavior test uses only `[` and `]`.
- A missing optional document does not fail a script. The literal probe returns `False`, and the list omits the document.
- A probe split over two lines escapes the line scan.
  Caution: keep each probe on one line. A split probe can pass the guard without a literal path.
- A scoped script that cannot be read fails the guard. The failure reports 0 examined lines.
- A `Get-ChildItem -Path` call fails the guard, even when its `Test-Path` call is literal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `check-prerequisites.ps1` MUST use a literal probe for `research.md`, `data-model.md`, and `quickstart.md`.
- **FR-002**: `check-prerequisites.ps1` MUST use a literal probe for the `contracts` folder and read it with `Get-ChildItem -LiteralPath`.
- **FR-003**: `setup-tasks.ps1` MUST apply the literal probes of FR-001 and FR-002.
- **FR-004**: `create-new-feature.ps1` MUST use a literal probe for the spec file and for the spec template.
- **FR-005**: The four scoped scripts MUST keep the design document paths that `GetRelativePath` builds.
- **FR-006**: The guard MUST fail on each bare probe in a scoped script.
- **FR-007**: The guard MUST report the number of probe lines it examined in each scoped script.
- **FR-008**: The guard MUST fail when it cannot read a scoped script, and it MUST report 0 examined lines.
- **FR-009**: The guard MUST include a self-check that flags each bare form and passes each literal form.
- **FR-010**: The behavior test MUST prove that both listing scripts name the optional documents in a bracket folder.
- **FR-011**: The text and JSON output of the four scripts MUST NOT change for paths without wildcard characters.
- **FR-012**: Each changed line in a touched block MUST have an inline comment. Each touched action MUST have an info log before it and a debug log after it.
- **FR-013**: The change MUST add one changelog fragment, `changelog.d/issue-4910-routed-literal-path.md`.
- **FR-014**: The change MUST NOT edit a managed manifest under `.specify/integrations/`, or any file that the change map does not name.
- **FR-015**: The change MUST add no direct child to `tests/guardrails`. Each new folder MUST hold five children or fewer.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: the change calls no Mist Cloud endpoint and uses no mistapi method.

### Key Entities *(include if feature involves data)*

Not applicable: the change edits scripts and tests, and it stores no data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Before the change, the guard reports 10 bare probe lines among 26 examined lines. After the change, it reports 0 bare probe lines among 26 examined lines.
- **SC-002**: Both bracket-folder behavior tests fail before the change and pass after it.
- **SC-003**: The existing tests of `test_routed_core_port.py` and `test_spec_route_contract.py` keep their results after the change.
- **SC-004**: Each local gate that applies to the changed files passes. The pull request records each command and its result.
- **SC-005**: Every required remote check passes before the orchestrator authorizes auto-merge.

## Assumptions

- The four scoped scripts on remote `main` match the working copy. Verified by RC-01 to RC-16 and RC-60.
- `pwsh` runs the behavior tests on Windows and on the CI runner. The existing tests in `test_spec_route_contract.py` already require it (RC-65).
- The ten bare lines listed in `design/research.md` are the only bare probes in the scoped scripts (RC-60).
- No open pull request changes a file in the change map. The check on 2026-11-26 found seven open pull requests and no file overlap.
- Issue #4873 part 2 does not reclassify the four restored probe lines. `analysis.md` records the coordination.

## Out of Scope

- The feature-plan probes in `update-agent-context.ps1` (RC-22, RC-23, RC-58, RC-59). They need a separate issue.
- The template and override probes in `common.ps1` (RC-21). They need a separate issue.
- The 1.4.3 template priority and composition engine. Issue #4873 owns that decision.
- The managed-file hashes in `.specify/integrations/speckit.manifest.json` (RC-48, RC-49).
- A note about `pwsh` in `documentation/development-setup.md` (RC-96). The gap exists before this change.
