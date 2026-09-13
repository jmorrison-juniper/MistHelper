# Feature Specification: Packet capture and bootstrap/session auth decomposition wave

**Feature Branch**: `[194-capture-bootstrap-decomposition]`  
**Created**: 2026-05-27  
**Status**: Draft  
**Input**: User description: "Create or update a feature specification for a new MistHelper decomposition wave focused on two groups from MistHelper.py only: (1) packet capture cleanup/final migration and (2) bootstrap/session/auth selection extraction. The user explicitly wants decomposition and refactor into src modules/submodules outside the main script, with no thin wrappers or generic 'helpers' modules. Use the existing repo conventions and the current wave-2 spec as a style reference, but do NOT copy its exact scope. The spec should capture: problem/goal, interfaces & behavior, constraints/performance, security & secrets, test plan, migration/compatibility, acceptance criteria, implementation notes, and UI behavior if applicable (likely none). Include explicit assumptions based on discovery: packet capture already exists in src/capture but MistHelper.py still contains legacy logic and wave-1 guardrails that will need to change; bootstrap/session logic currently lives in MistHelper.py and has no dedicated src/bootstrap package or dedicated unit tests. Mention that existing packet capture tests exist and will need adjustment, and bootstrap/session tests do not exist yet and will need creation. Emphasize that GlobalImportManager is not a target unless import rewiring is strictly required by moved classes. Keep the spec concise but actionable and aligned to a future plan/tasks workflow."

## Problem Statement

`MistHelper.py` still owns two high-risk decomposition areas that should live in `src/` modules: the remaining packet capture workflow and the session/bootstrap/auth selection flow. Packet capture already has a home in `src/capture`, but legacy code and wave-1 guardrails remain in the main script. Bootstrap/session/auth selection still lives entirely in `MistHelper.py`, with no dedicated `src/bootstrap` package and no dedicated unit coverage. This leaves the main script oversized, increases regression risk, and makes it harder to maintain a clean module boundary.

## Goals

- Finish the packet capture migration so `MistHelper.py` keeps only orchestration and compatibility glue for capture-related paths.
- Extract bootstrap/session/auth selection into semantically named `src/bootstrap` modules and submodules.
- Keep user-visible menu flows, prompts, and authentication choices stable during the refactor.
- Replace legacy main-script logic with module-owned behavior, not thin wrappers or generic helper buckets.
- Update and extend tests so the refactor is verified by existing packet capture coverage plus new bootstrap/session coverage.
- Keep `GlobalImportManager` out of scope unless a minimal import rewrite is strictly required by moved classes.

## Non-Goals

- Do not introduce new user-facing features or menu operations.
- Do not broaden the wave to unrelated `MistHelper.py` classes.
- Do not create generic `helpers` or `utils` modules whose only purpose is to hide moved logic.
- Do not refactor `GlobalImportManager` unless import rewiring cannot be completed cleanly without it.
- Do not change the overall authentication model or capture semantics beyond what is needed to preserve existing behavior.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete packet capture migration (Priority: P1)

As a NOC engineer, I want packet capture behavior to come from `src/capture` instead of the main script so the codebase has one clear home for capture workflows and fewer regression-prone paths.

**Why this priority**: Packet capture is already partially extracted, so finishing it removes known legacy duplication and closes the highest-risk refactor gap.

**Independent Test**: Run the packet capture test set and affected menu flows after removing the remaining legacy paths from `MistHelper.py`; behavior should remain unchanged.

**Acceptance Scenarios**:

1. **Given** an existing packet capture menu path, **When** the workflow is executed, **Then** the same capture options, prompts, and outcomes are still available.
2. **Given** the packet capture logic has been fully migrated, **When** the main script is inspected, **Then** only orchestration or compatibility wiring remains for capture-related behavior.
3. **Given** existing packet capture tests, **When** they are updated for the new module boundaries, **Then** they continue to validate the same behavior without relying on stale `MistHelper.py` internals.

### User Story 2 - Extract bootstrap/session/auth selection (Priority: P2)

As a NOC engineer, I want session bootstrap and authentication selection to be owned by dedicated `src/bootstrap` modules so startup behavior is easier to test and maintain.

**Why this priority**: This flow currently has no dedicated package or unit tests, so extracting it creates a cleaner boundary and immediate testability gains.

**Independent Test**: Add focused unit tests for bootstrap/session/auth selection and verify the existing startup flow still chooses the same authentication path under the same inputs.

**Acceptance Scenarios**:

1. **Given** a normal startup or login path, **When** the authentication choice is made, **Then** the same user-facing selection and session setup behavior occurs as before.
2. **Given** EOF, cancellation, or invalid input during startup, **When** the user is prompted, **Then** the flow still exits or retries safely using the same defensive behavior expectations.
3. **Given** the refactor is complete, **When** the main script is reviewed, **Then** bootstrap/session/auth selection logic is no longer implemented directly in `MistHelper.py`.

### Edge Cases

- Packet capture still depends on a legacy guardrail in `MistHelper.py` that must be replaced rather than duplicated.
- Packet capture tests reference old main-script entry points and need to be updated to the new module ownership.
- Bootstrap/session/auth selection needs to handle EOF and cancellation without leaking secrets or leaving partially initialized state behind.
- Import rewiring introduces a cycle unless the new `src/bootstrap` and `src/capture` boundaries stay one-way.
- A moved class only needs `GlobalImportManager` changes if import rewiring cannot be done any other way.

## Interfaces & Behavior

### In-Scope Behavior

- Packet capture entrypoints continue to present the same menu choices and capture outcomes.
- Bootstrap/session/auth selection continues to honor the same inputs, prompts, and cancellation behavior.
- `MistHelper.py` becomes a thin orchestrator for these flows, not the implementation owner.
- New code lives in semantically named `src/capture` and `src/bootstrap` modules or submodules.

### Out of Scope Behavior

- No new UI screens or web views are expected.
- No new command-line flags or menu operations are introduced.
- No generic cross-cutting helper package is introduced just to host moved code.

## Constraints / Performance

- The refactor must not add noticeable delay to packet capture startup, download, or session bootstrap paths.
- Module splitting must preserve the current interaction flow; users should not see extra prompts or duplicate network calls.
- New modules must remain easy to import on Windows and in container runs.
- The import graph must remain acyclic after the move.
- The refactor should stay within the existing repo conventions: semantically named modules, no wrapper-only classes, and no generic catch-all helper package.

## Security & Secrets

- No tokens, passwords, or session secrets may be logged while extracting bootstrap/session/auth selection.
- `.env` remains the source of truth for credentials and other sensitive runtime values.
- New bootstrap/session code must preserve EOF-safe and cancellation-safe behavior without exposing partial credentials.
- Test fixtures should mock secrets rather than storing live values in the repository.

## Test Plan

### Existing Coverage to Update

- Packet capture tests already exist and must be adjusted to the new `src/capture` ownership and any changed import paths.
- Existing menu or integration coverage that still touches packet capture must remain valid after the move.

### New Coverage to Create

- Create dedicated unit tests for bootstrap/session/auth selection behavior, including happy-path startup and EOF/cancellation paths.
- Add regression coverage for the new `src/bootstrap` boundary so the startup flow is exercised without `MistHelper.py` owning the implementation.

### Validation Layers

1. Unit tests for packet capture migration behavior.
2. Unit tests for bootstrap/session/auth selection behavior.
3. Regression tests for affected menu or startup paths.
4. Import graph checks to prevent circular dependencies.
5. Existing project quality gates for syntax, linting, and build/test validation.

## Migration / Compatibility

- The packet capture migration must preserve current menu IDs, prompts, and capture semantics while removing the last meaningful capture logic from `MistHelper.py`.
- The bootstrap/session extraction must preserve the same startup choices and auth behavior from the user perspective.
- Any compatibility shim in `MistHelper.py` must be temporary and limited to orchestration; it should not become the new long-term implementation.
- If a minor import rewrite is needed for moved classes, it must stay localized and must not expand the scope to unrelated ownership changes.

## Requirements *(mandatory)*

### Scope Constraints

- **SCOP-001**: This wave MUST focus only on packet capture cleanup/final migration and bootstrap/session/auth selection extraction.
- **SCOP-002**: `GlobalImportManager` MUST remain out of scope unless a moved class cannot be wired without a minimal import rewrite.
- **SCOP-003**: New code MUST live in semantically named `src/` modules or submodules, not in generic helper or wrapper-only packages.
- **SCOP-004**: `MistHelper.py` MUST retain only orchestration or compatibility wiring for the in-scope flows after the refactor.

### Functional Requirements

- **FR-001**: Packet capture logic MUST be fully owned by `src/capture` modules, with `MistHelper.py` reduced to orchestration for packet capture entrypoints.
- **FR-002**: Bootstrap/session/auth selection logic MUST be extracted into a dedicated `src/bootstrap` package or package family with clear ownership boundaries.
- **FR-003**: The refactor MUST preserve current packet capture behavior, prompts, and output semantics.
- **FR-004**: The refactor MUST preserve current bootstrap/session/auth selection behavior, including safe handling of EOF, cancellation, and invalid input.
- **FR-005**: Existing packet capture tests MUST be updated to match the new module boundaries and continue covering the same behavior.
- **FR-006**: New bootstrap/session tests MUST be created and must cover the startup and auth-selection flows that currently have no dedicated unit coverage.
- **FR-007**: The module split MUST not introduce thin wrappers, generic helpers modules, or duplicate business logic.
- **FR-008**: The final structure MUST keep import boundaries acyclic and must not require unnecessary changes to `GlobalImportManager`.
- **FR-009**: Any temporary compatibility wiring in `MistHelper.py` MUST be minimal and must be removable once parity is confirmed.

### Key Entities *(include if feature involves data)*

- **Packet Capture Flow**: The set of actions for starting, tracking, and completing packet captures, including current menu-driven paths and any legacy guardrails.
- **Bootstrap Session Flow**: The startup path that prepares session state before menu or operational actions begin.
- **Auth Selection State**: The decision logic that chooses the active authentication path based on user input and runtime context.
- **Compatibility Wiring**: Temporary orchestration retained in `MistHelper.py` only while the moved modules are verified.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All packet capture behavior in scope is owned by `src/capture`, with no remaining implementation-heavy packet capture logic in `MistHelper.py`.
- **SC-002**: Bootstrap/session/auth selection behavior is owned by a dedicated `src/bootstrap` package family, and the main script no longer implements that logic directly.
- **SC-003**: Existing packet capture tests are updated and pass, and new bootstrap/session tests exist and pass.
- **SC-004**: No accepted regressions are introduced in packet capture flows or startup/auth selection flows.
- **SC-005**: No new circular imports are introduced by the refactor.
- **SC-006**: The final structure avoids generic helper-only modules and keeps module ownership semantically clear.

## Assumptions

- Packet capture already exists in `src/capture`, and the remaining work is to finish migration and remove legacy main-script logic.
- Wave-1 guardrails around packet capture will need to be updated as part of the final migration.
- Bootstrap/session/auth selection currently lives in `MistHelper.py` and does not yet have a dedicated `src/bootstrap` package.
- Existing packet capture tests will need adjustment to match the new ownership model.
- Bootstrap/session/auth selection tests do not yet exist and must be created from scratch.
- No UI-specific work is expected for this wave; the changes are limited to CLI/menu-internal behavior and module boundaries.
