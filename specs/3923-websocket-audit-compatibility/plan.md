# Implementation Plan: WebSocket Audit Compatibility

**Branch**: `jmorrison-juniper-websocket-live-audit-compatibility` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/3923-websocket-audit-compatibility/spec.md`

## Summary

Update the isolated WebSocket audit so `ReadScope` permits a client read only after approved site and device responses establish the same-site relationship. Update `DialogInspector` to report the visible Cancel control count and the existing missing-control finding. Keep all changes in the audit support code and its isolated tests.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: pytest, Playwright, and the installed `mistapi` SDK for source inspection.

**Storage**: None. Keep identifiers in memory during the audit.

**Testing**: The existing isolated pytest fixtures use synthetic local responses and guarded browser routing.

**Target Platform**: Local test runs on Windows, macOS, and Linux. No portal deployment or live request is in scope.

**Project Type**: Test-only audit support for the WebSockets portal.

**Performance Goals**: No new performance target. Keep the existing per-test timeouts and complete inventory count.

**Constraints**: Preserve default denial, exact origin and path checks, redirect denial, method restrictions, SDK source-only verification, and the complete audit denominator. Do not use credentials or invoke live methods.

**Scale/Scope**: Update `ReadScope` and `DialogInspector` in existing audit support modules. Add regressions to the existing isolated inventory and dialog test modules. Do not change portal behavior, shared instructions, branch state, or deployment files.

## Constitution Check

*GATE: Pass before research and after design.*

- **Five-Item Rule**: The `specs/` directory already contains established feature records. The workflow permits this feature's unique planning artifacts as direct children. Keep source and test changes inside existing files and directories. Track separate folder cleanup outside this feature.
- **Class structure**: Keep behavior in the existing `ReadScope` and `DialogInspector` classes. Do not add wrapper functions, modules, or packages.
- **Mist Cloud safety**: Add no transport or API call. Permit only a scoped GET after valid local evidence. Keep all isolated tests synthetic and prove denied requests transmit zero times.
- **Dialog safety**: Inspect rendered controls only. Do not submit a form or start an operation.
- **Test scope**: Select only `test_inventory.py` and `test_dialogs.py`. Do not select `test_live.py`.
- **Files and outputs**: Keep all test evidence in memory or pytest temporary paths. Do not create product output under another directory.
- **Workflow boundary**: Implement the repair, validate it locally, and publish a new pull request. Do not merge, deploy, or run live checks.
- **Deployment pipeline**: The user prohibits live operations and deployment. Run isolated validation and the applicable local gates instead.
- **Release notes**: This internal-only harness repair requires no fragment under `changelog.d/README.md`. Record the reason in the pull request.

**Post-design gate**: Pass. The design changes two existing audit classes and their existing test modules. It adds no production integration, data store, or public interface.

## Phase 0: Research

The current code paths and tests resolve the implementation questions. See [research.md](research.md). No external research or new dependency is needed.

## Phase 1: Design

See [data-model.md](data-model.md) for in-memory scope and result records. The audit exposes no new external interface, so no contract files are required. See [quickstart.md](quickstart.md) for isolated validation commands.

## Implementation Sequence

1. Add failing isolated tests for site-to-device scope, the exact client path, malformed parent evidence, and unchanged denial boundaries.
2. Add failing dialog tests for zero, one, hidden, and duplicate visible Cancel controls. Check the report count and the existing `operation-cancel` finding.
3. Repair `ReadScope` to register device IDs under the site that supplied them and to authorize only the exact client GET for a registered device.
4. Extend source-only SDK verification to cover the client discovery method without invoking it.
5. Repair `DialogInspector` and its cancellation evidence helper to count only visible, exact-name Cancel controls in the operation form.
6. Run the isolated audit suite and the relevant Python quality gates. Run the guide preflight and test-quality gates before publication.

## Test Plan

Run the regressions first and confirm that they fail for the missing scope association and fixed cancellation value. After the repair, run:

```text
python -m pytest tests/e2e/websockets_tab/dialog_audit/test_inventory.py tests/e2e/websockets_tab/dialog_audit/test_dialogs.py
python -m py_compile tests/e2e/websockets_tab/dialog_audit/support/policy.py tests/e2e/websockets_tab/dialog_audit/support/journeys.py tests/e2e/websockets_tab/dialog_audit/test_inventory.py tests/e2e/websockets_tab/dialog_audit/test_dialogs.py
python -m ruff check tests/e2e/websockets_tab/dialog_audit/support/policy.py tests/e2e/websockets_tab/dialog_audit/support/journeys.py tests/e2e/websockets_tab/dialog_audit/test_inventory.py tests/e2e/websockets_tab/dialog_audit/test_dialogs.py
python -m black --check tests/e2e/websockets_tab/dialog_audit/support/policy.py tests/e2e/websockets_tab/dialog_audit/support/journeys.py tests/e2e/websockets_tab/dialog_audit/test_inventory.py tests/e2e/websockets_tab/dialog_audit/test_dialogs.py
```

Do not run `test_live.py`, a live portal probe, or an operation.

## Project Structure

### Planning artifacts

```text
specs/3923-websocket-audit-compatibility/
├── data-model.md
├── plan.md
├── quickstart.md
├── research.md
└── spec.md
```

### Existing audit support and tests

```text
tests/e2e/websockets_tab/dialog_audit/
├── support/
│   ├── journeys.py       # DialogInspector and cancellation evidence
│   └── policy.py         # ReadScope and client request policy
├── test_dialogs.py       # Isolated dialog regressions
└── test_inventory.py     # Isolated scope and SDK-source regressions
```

**Structure Decision**: Reuse the two existing support modules and their isolated test modules. Do not add files to the audit package.

## Complexity Tracking

No new class, module, package, or production behavior is planned. Existing `specs/` folder growth is legacy workflow debt. Keep that separate from this feature.
