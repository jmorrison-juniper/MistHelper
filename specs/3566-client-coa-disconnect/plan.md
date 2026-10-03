# Implementation Plan: Client CoA Disconnect

**Branch**: `feat/3566-client-coa-disconnect` | **Date**: 2026-09-29 | **Spec**: `specs/3566-client-coa-disconnect/spec.md`

**Input**: Feature specification from `specs/3566-client-coa-disconnect/spec.md`

## Summary

Add the implementation package and wiring manifest for menu 286 as a destructive MistHelper operation for client session control.
The operation selects a site, selects an action, accepts a client MAC or rogue BSSID, shows the normalized target, requires exact typed confirmation, and then sends the Mist request.
The handler supports `--dry-run`, which prints the request preview and sends no Mist request.
It writes one audit row to `data/ClientSessionControlLog.csv` for each request attempt.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, `pytest`, and the Python standard library.
Use existing MistHelper utilities for safe input, site selection, logging, and CSV output where they fit the contract.

**Storage**: `data/ClientSessionControlLog.csv` only.
No database schema change is planned.

**Testing**: Unit tests under `tests/unit/device/client_session_control/`.
Use fakes for the Mist API functions and for operator input.
Do not send live destructive Mist requests from automated tests.

**Target Platform**: MistHelper CLI on Windows and Linux containers.

**Project Type**: CLI menu operation with a feature package under `src/mist/resources/device/client_session_control/`.

**Performance Goals**: A helpdesk operator can complete a request in less than 2 minutes when the site and target are known.

**Constraints**:

- Use Simplified Technical English in user text and documentation.
- Do not use semicolons in specification and planning documents.
- Keep this planning step inside `specs/3566-client-coa-disconnect/**`.
- Do not edit `.specify/feature.json` during this step.
- Do not edit repository wiring files during this step.
- Menu 286 is destructive and must stay out of all automated test passes.
- The fleet contract defers hot-file wiring, README edits, menu documentation edits, and primary-key strategy handling to the integration pull request.
- `--dry-run` must print the request and send no Mist request.
- Exact typed confirmation is required before each live Mist request.
- Read existing MAC normalization and client lookup helpers under `src/mist/resources/device/` before implementation work starts.
- Verify the required OpenAPI operation IDs and installed `mistapi` functions before client code starts.

**Scale/Scope**: One menu operation, five supported actions, one CSV audit file, one handler package, and one unit test package.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
| - | - | - |
| I. Five-Item Rule | PASS WITH DOCUMENTED EXCEPTION | The required package is `src/mist/resources/device/client_session_control/`. `src/mist/resources/device/` already has more than five direct children. The user requirement makes this path mandatory. The implementation must add a nested package, not a loose module, and must record the existing debt. |
| II. Class-Based Architecture | PASS | The handler is `ClientSessionControl` with static `run()`. Helper behavior belongs in focused classes or dataclasses. |
| III. Safety-First | PASS | The operation validates the target early, shows the normalized target, requires exact confirmation, and supports `--dry-run`. |
| IV. Full Deployment Pipeline | PASS FOR PLAN | This step edits only planning artifacts. Implementation must add tests, local gates, release note, wiring, and pull request evidence. |
| V. Observability and Logging | PASS | The implementation must log before and after API calls, prompts, normalization, and CSV writes. Secrets must not appear in logs. |
| VI. Inline Comments | PASS | All implementation code must include inline comments on generated executable lines. |
| VII. Action Logging | PASS | The implementation must log each meaningful action before and after it runs. |
| Technology Constraints | PASS | The plan uses Python 3.13 and `mistapi` 0.64.0 from the worktree virtual environment. |

## Project Structure

### Documentation for this feature

```text
specs/3566-client-coa-disconnect/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── wiring.md
├── contracts/
│   └── client-session-control.md
└── tasks.md
```

### Source Code for implementation

```text
src/mist/resources/device/client_session_control/
├── __init__.py
├── actions.py
├── audit.py
├── handler.py
└── models.py

tests/unit/device/client_session_control/
├── __init__.py
├── test_client_session_control_confirmation.py
├── test_client_session_control_dry_run.py
├── test_client_session_control_log.py
├── test_client_session_control_normalization.py
└── test_client_session_control_wiring.py
```

**Structure Decision**: Use a nested package at `src/mist/resources/device/client_session_control/` because the specification requires that package.
Keep the package at five direct files.
Put unit tests under `tests/unit/device/client_session_control/`.
Defer repository registration to `specs/3566-client-coa-disconnect/wiring.md`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| Add `src/mist/resources/device/client_session_control/` under noncompliant `src/mist/resources/device/` | The feature specification and user input require this exact package. | A different package would violate FR-016 and the current user contract. A loose file under `src/mist/resources/device/` would add less structure and more debt. |
| Deferred repository wiring | The current step is limited to `specs/3566-client-coa-disconnect/**`. | Editing `MistHelper.py` or registry files now would violate the fleet contract. |
| Deferred README and primary-key strategy handling | The operation is destructive control, not data export or data collection, and the user explicitly forbids these hot-file edits in this branch. | The integration pull request will own registration, menu documentation, and any primary-key strategy N/A record or registry policy update that reviewers require. |
| Phase checkpoint commits | The fleet contract for issue #3566 explicitly requires a commit after each completed task group. | A single end-only commit would violate the issue-specific instruction for this worktree. |

## Phase 0 Research Output

See `specs/3566-client-coa-disconnect/research.md`.
All technical unknowns are resolved.

## Phase 1 Design Output

See these artifacts:

- `specs/3566-client-coa-disconnect/data-model.md`
- `specs/3566-client-coa-disconnect/contracts/client-session-control.md`
- `specs/3566-client-coa-disconnect/quickstart.md`
- `specs/3566-client-coa-disconnect/wiring.md`

## Post-Design Constitution Check

| Principle | Status | Evidence |
| - | - | - |
| I. Five-Item Rule | PASS WITH DOCUMENTED EXCEPTION | The design uses one nested feature package with five files. The known parent debt stays documented. |
| II. Class-Based Architecture | PASS | The contract centers on `ClientSessionControl.run()`. |
| III. Safety-First | PASS | Dry run, exact confirmation, validation, and destructive exclusion are explicit contracts. |
| IV. Full Deployment Pipeline | PASS FOR PLAN | No code is edited. Implementation tasks must run the full local and pull request workflow. |
| V. Observability and Logging | PASS | The data model includes one audit row per request attempt. |
| VI. Inline Comments | PASS | The implementation contract keeps the repository code comment rule active. |
| VII. Action Logging | PASS | The contract requires action logging around prompts, API calls, and file writes. |
| Technology Constraints | PASS | The research verifies OpenAPI and worktree `mistapi` 0.64.0 support. |
