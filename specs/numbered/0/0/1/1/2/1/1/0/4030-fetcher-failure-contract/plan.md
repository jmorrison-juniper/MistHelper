# Implementation Plan: Fetcher Failure Contract

**Branch**: `jmorrison-juniper-fix-4030-fetcher-failure-contract` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/numbered/0/0/1/1/2/1/1/0/4030-fetcher-failure-contract/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Change the unresolved-site branch in `DeviceDataFetcher.fetch()` from an
implicit successful return to an explicit failed fetch. The branch will log
`! Error fetching device data: site ID could not be resolved.` and return
`False` before device selection or Mist access.

Extend the existing fetcher unit test with the exact error and side-effect
contract. Extend the portal silent-completion test with a red-green regression.
The regression will run the real `InteractiveDisplayUtils.device_tests`,
`DeviceDataFetcher`, `OperationExecutor`, and `OutputFileScanner` path. It will
create unrelated output during site selection. The test must observe Complete
before the repair and Failed after the repair.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, Python logging, and the existing source dependency resolver

**Storage**: No product storage change. The portal regression uses a temporary directory for output evidence.

**Testing**: pytest, `monkeypatch`, `caplog`, `MagicMock`, and the real portal output scanner

**Target Platform**: Windows 11, macOS, Linux, and the existing Podman deployment

**Project Type**: Python CLI with a Flask web portal

**Performance Goals**: Stop the unresolved-site path before device selection, network access, transforms, rendering, or file output.

**Constraints**: Edit one production file and two named test files. Preserve all portal classifiers and display code.

**Scale/Scope**: One Menu 95 failure branch, one focused fetcher contract, and one portal terminal-state regression

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Pre-design result**: PASS.

- The numeric specification uses the required eight-level base-5 route.
- The feature edits existing files and adds no production module or package.
- The only production edit is
  `src/foundation/support/refactors/device_data_fetcher.py`.
- The plan does not edit `web_portal/services/operation.py`,
  `PARAMETER_REGISTRY`, or
  `src/interfaces/visualization/ui/interactive_display_utils.py`.
- The repair validates the required site scope and returns before Mist access.
- The failure log uses ASCII text and contains no secret or identifier value.
- The production change adds no parameter, function, class, or top-level name.
- The implementation must add the required inline comment to each changed
  executable line.
- The implementation must log the failed action before the explicit return.
- The tests use controlled doubles and no production credential.
- The existing changelog fragment remains unchanged.
- The pull request title must use `fix: ...` or `fix(scope): ...`.

**Existing structural debt**:

- `device_data_fetcher.py` has more than five top-level names.
- `tests/unit/web_portal/` has more than five direct children.
- The feature folder follows the Spec Kit process-file exception.

This feature adds no top-level production name and no test file. A separate
incremental action must reduce the refactor module hierarchy before a future
feature adds another top-level name. The process-folder baseline remains the
authority for managed specification records.

**Mist Cloud gate**:

- The failed path makes no REST request.
- The valid path keeps the existing
  `mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest` call.
- The focused test must prove that the Mist callable is not called.
- No owned WebSocket transport or authentication change applies.

For repository structure and generated files:

- Confirm that the commit subject and pull request title use a Conventional
  Commit form that the pull request title guard accepts.
- If repository workflow requires a direct child in an established process
  folder, confirm that the change adds only its own unique record.
- Record existing process-folder debt and a separate incremental remediation
  action.
- Confirm that product outputs remain under `data/`.
- Generated test evidence MAY use the established, git-ignored
  `test-artifacts/` folder.

For a feature that uses Juniper Mist Cloud:

- Confirm that every REST request uses a working mistapi method.
- If the feature proposes an owned WebSocket transport, name the matching
  mistapi WebSocket path and the contract that it cannot meet.
- Name the contract tests that prove the SDK path is broken, incomplete, or
  cannot preserve required output.
- Confirm that the owned transport preserves SDK authentication and endpoint
  contracts.
- Confirm tests cover output, failure handling, safety, and secret redaction.
- Treat a missing proof or contract test as a failed gate.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/2/1/1/0/4030-fetcher-failure-contract/
├── spec.md
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/
│   └── fetcher-failure-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── foundation/support/refactors/
│   └── device_data_fetcher.py             # Only production edit
└── interfaces/visualization/ui/
    └── interactive_display_utils.py        # Read-only existing contract

web_portal/
└── services/
    └── operation.py                        # Read-only marker and verdict contract

tests/
└── unit/
    ├── refactors/
    │   └── test_device_data_fetcher.py
    └── web_portal/
        └── test_portal_silent_completion.py
```

**Structure Decision**: Keep the repair at the fetcher boundary. Reuse the
display and portal contracts without edits. Extend the two existing test
modules so the feature adds no new test hierarchy child.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0: Research

Research confirms that the defect begins when `fetch()` returns `None` after
site resolution fails. The existing display treats only explicit `False` as a
failure. The portal then accepts unrelated output evidence as completion.

The selected repair logs the exact operator error and returns `False` from the
fetcher. The existing display suppresses its completion log. The existing
portal marker `error fetching` selects the exact failure before output evidence.
See [research.md](research.md).

## Phase 1: Design

The design changes no persistent schema. It defines the transient fetch outcome,
captured log evidence, and portal run verdict in [data-model.md](data-model.md).

The behavioral contract is
[contracts/fetcher-failure-contract.md](contracts/fetcher-failure-contract.md).
The validation sequence is [quickstart.md](quickstart.md).

## Implementation Sequence

1. Add the focused fetcher assertions before the production edit.
2. Add the portal regression with real Menu 95 dependencies.
3. Run the portal regression against the current code.
4. Record that unrelated output produces a completed run before the repair.
5. Change only the unresolved-site branch in `DeviceDataFetcher.fetch()`.
6. Emit the exact required error and return explicit `False`.
7. Rerun both focused modules and the applicable quality gates.
8. Confirm the portal run is failed and preserves the exact failure reason.

## Post-Design Constitution Check

**Post-design result**: PASS.

- All unknowns are resolved.
- The design keeps the strict three-file implementation scope.
- The portal test uses the real display, fetcher, executor, and scanner path.
- The test adds unrelated output through site selection, not by editing the run.
- The red-green procedure proves the before and after terminal states.
- The exact error contains `error fetching` for the existing handled-error
  classifier.
- Issue #3168 remains the owner of broader marker coupling.
- No portal control, parameter, display, or classifier change is planned.
