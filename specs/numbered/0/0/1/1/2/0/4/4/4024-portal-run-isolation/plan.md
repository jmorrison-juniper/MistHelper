# Implementation Plan: Portal Run Evidence Isolation

**Branch**: `4024-portal-run-isolation` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Numeric feature specification from `/specs/numbered/[base-5-route]/[###-feature-name]/spec.md`, or timestamp feature specification from `/specs/live/[timestamp-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Isolate each concurrent legacy portal run by the worker thread that owns its capture scope.
`_RunLogHandler` will accept records only from its owner thread.
`OutputFileScanner` will assign tracked writes only to the scanner for the calling owner thread.
It will reject paths with multiple tracked owners.
It will disable timestamp fallback for every scanner whose lifetime overlaps another scanner.
Single-run timestamp fallback, the shared `data/` directory, existing responses, and concurrent execution will remain unchanged.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Python `logging`, `threading`, `pathlib`, and `concurrent.futures`; Flask portal services; pytest

**Storage**: Existing shared `data/` filesystem output; existing in-memory operation run records; no database schema change

**Testing**: pytest unit and integration-style worker tests with `threading.Barrier` and `threading.Event`

**Target Platform**: Windows 11, macOS, Linux, and the existing rootless Podman deployment

**Project Type**: Flask web portal inside the MistHelper Python application

**Performance Goals**: Preserve `ThreadPoolExecutor` concurrency; keep tracked write attribution at constant-time owner lookup; avoid full filesystem walks during overlap

**Constraints**: No global operation lock; no operation-specific output directory; no public response shape change; exact hook restoration after the last scanner

**Scale/Scope**: One portal process, up to `max(1, CPU count - 1)` concurrent workers, bounded run logs, and bounded output file lists

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Pre-design result: PASS**

- The feature uses the managed eight-level route under `specs/numbered/`.
- The plan adds only feature-owned records below the existing issue directory.
- The feature does not add a Mist Cloud transport or change a Mist API call.
- Product output remains in the shared `data/` directory.
- The feature preserves safe concurrent execution and adds no destructive operation.
- External inputs, credentials, and output paths do not change.
- The implementation must use `pathlib.Path` for output path checks.
- The implementation must retain bounded stores and must not add unbounded ownership history.
- The implementation must add action logging without logging file content or credentials.
- The implementation must use a Conventional Commit subject such as `fix(web-portal): isolate concurrent run evidence`.

**Existing structural debt**

- `web_portal/services/operation.py` is an existing large module with more than five top-level names.
- `OperationExecutor` and `_RunLogHandler` exceed the five-member guidance.
- `web_portal/services/output_scan.py` has more than five module-level names and class methods.
- This feature will make narrow edits to existing children and will add no new product module.
- A separate remediation issue must split portal execution, capture ownership, and output scanning after issue #4024.

**Post-design result: PASS**

- The design adds private state to two existing classes and one existing run record.
- No new product hierarchy level or wrapper function is required.
- The owner checks fail closed for foreign logs, ownerless writes, and ambiguous paths.
- Tests prove overlap before release and prove both completion orders.
- The design preserves exact process hook values after the final scanner exits.

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
specs/numbered/0/0/1/1/2/0/4/4/4024-portal-run-isolation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/
│   └── run-evidence-isolation.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
web_portal/
├── routes/
│   └── operations.py                 # Existing run-specific SSE replay and stream filter
└── services/
    ├── event_bus.py                  # Existing run_id subscriber filter
    ├── operation.py                  # Worker owner, log capture, and completion evidence
    └── output_scan.py                # Owner-specific tracked writes and fallback policy

tests/
└── unit/
    ├── test_operation_output_file_discovery.py
    └── web_portal/
        ├── test_event_bus.py
        ├── test_operation_output_files_cap.py
        ├── test_operation_run_registry_caps.py
        ├── test_output_scan_clock_race.py
        ├── test_output_scan_runtime_files.py
        ├── test_portal_log_routing.py
        ├── test_portal_run_isolation.py      # New synchronized concurrency tests
        └── test_portal_silent_completion.py
```

**Structure Decision**: Keep the implementation in the two existing portal service classes.
Add one focused test module for synchronized overlap scenarios.
Reuse existing focused tests for routing, caps, fallback, completion, SSE filtering, and output ordering.

## Phase 0 Research Decisions

The detailed decisions and alternatives are in [research.md](research.md).

1. Capture one worker thread identifier at the start of `_capture_and_run`.
2. Pass that identifier to `_RunLogHandler` and `OutputFileScanner`.
3. Filter log records through `LogRecord.thread` before storage, file extraction, or SSE publication.
4. Replace scanner fan-out with one active scanner per owner thread.
5. Mark a path ambiguous in every active owner that tracked the same path.
6. Mark every scanner that overlaps another scanner as fallback-ineligible.
7. Keep hooks installed until the active scanner registry becomes empty.

## Phase 1 Design

### Operation worker ownership

- `_execute_operation` continues to run in the existing worker pool.
- `_capture_and_run` captures `threading.get_ident()` once.
- The private run record stores `_owner_thread_id` for the capture lifetime.
- `_RunLogHandler` receives the same identifier.
- `OutputFileScanner` receives the same identifier.
- Cleanup removes the handler and scanner registration in the existing `finally` path.

### Log isolation

- `_RunLogHandler.emit` compares `record.thread` with its owner identifier.
- A mismatch returns before formatting, storage, output-file extraction, or SSE publication.
- Owner records retain the current user-facing and debug routing rules.
- Each handler updates only its run's bounded deques and discard counter.
- Existing `PortalEventBus` filtering remains unchanged because every published event already carries `run_id`.

### Tracked write isolation

- `OutputFileScanner._active_scanners` becomes an owner-keyed registry.
- A writable `builtins.open` or `Path.open` call resolves the calling thread identifier.
- The hook records the path only for the scanner owned by that thread.
- A write from a child thread or unrelated thread has no owner and receives no tracked attribution.
- When two active owners track the same path, both scanners mark that path ambiguous.
- `_changed_tracked_files` excludes every ambiguous path.

### Overlap-safe fallback

- A scanner records `_overlap_detected` when another scanner is active during its lifetime.
- The existing directory-mark fallback and full-walk fallback run only when `_overlap_detected` is false.
- A scanner that ever overlapped stays fallback-ineligible, even if the other scanner finishes first.
- A scanner that never overlaps retains the current new-file and in-place rewrite fallback behavior.
- This rule rejects non-Python and ownerless evidence during overlap.

### Hook lifecycle

- The first active scanner stores and replaces the current `builtins.open` and `Path.open` values.
- Additional scanners reuse the installed hooks.
- A completed or failed scanner removes only its owner registration.
- The final scanner restores the exact saved function objects.
- Cleanup remains safe when scanners finish in either order.

### Completion and preview behavior

- The executor merges only scanner-approved names.
- Existing file existence checks remain unchanged.
- Existing prompt-cache ordering remains unchanged.
- Ambiguous or foreign files cannot satisfy `_completion_message`.
- A run without owned output still needs an existing no-output reason.

## Compatibility Constraints

- Keep the `OperationExecutor.start_operation`, status response, active-run response, and SSE payload shapes unchanged.
- Keep `log_messages`, `debug_messages`, `output_files`, and discard counters as bounded collections.
- Keep same-menu conflict behavior unchanged.
- Keep independent menu operations concurrent.
- Keep the existing `ThreadPoolExecutor` worker count.
- Keep the shared `data/` root and legacy output names.
- Keep single-run tracked writes and timestamp fallback behavior.
- Keep runtime-file filters, excluded directories, output caps, and preview ordering.
- Keep `PortalEventBus` run filtering and terminal replay behavior.
- Do not add environment variables, dependencies, database records, or migration work.
- Current CI `MYPY_PATHS`, `RADON_PATHS`, and coverage scope do not measure `web_portal`.
  The implementation must run explicit portal complexity and focused tests instead of claiming coverage from those gates.

## Test Strategy

### New synchronized test module

Add `tests/unit/web_portal/test_portal_run_isolation.py`.

- Run two different safe menu entries through one `OperationExecutor`.
- Use a `threading.Barrier` to prove both workers are active before either can finish.
- Emit distinct main and debug log markers from each worker.
- Write distinct tracked result files from each worker.
- Subscribe one event-bus client to each run identifier.
- Assert that each run and each subscriber receives only its own evidence.
- Overflow one run's log cap and assert that the other run keeps a zero discard count.
- Repeat the isolation scenario 100 times without sleeps.
- Release workers in both completion orders.
- Raise from each worker in separate cases and assert handler and scanner cleanup.

### Scanner ownership tests

- Prove that each owner receives only its tracked path.
- Prove that two owners of one path make the path ambiguous for both scanners.
- Prove that an ownerless child-thread write is excluded during overlap.
- Prove that a low-level or non-Python new file is excluded during overlap.
- Prove that single-run new-file fallback remains valid.
- Prove that single-run in-place rewrite fallback remains valid.
- Prove that hooks remain installed after the first scanner stops.
- Prove that the final stop restores the exact original hook objects.

### Existing regression tests

- Keep log routing tests for user-facing and debug classification.
- Keep output scanner tests for runtime files, clock races, new files, and rewrites.
- Keep output cap and log cap tests.
- Keep output merge, existence, and preview ordering tests.
- Keep silent-completion tests so foreign evidence cannot create success.
- Add an event-bus filter case to `test_event_bus.py` only if no current case proves two run filters.
- Run the existing operations panel workflow without changing its contested test file.

## Exact Relevant Quality Gates

Run these commands after implementation:

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m pytest tests\unit\web_portal\test_portal_run_isolation.py tests\unit\test_operation_output_file_discovery.py tests\unit\web_portal\test_output_scan_runtime_files.py tests\unit\web_portal\test_output_scan_clock_race.py tests\unit\web_portal\test_portal_log_routing.py tests\unit\web_portal\test_operation_run_registry_caps.py tests\unit\web_portal\test_operation_output_files_cap.py tests\unit\web_portal\test_event_bus.py tests\unit\web_portal\test_event_bus_deadlock.py tests\unit\web_portal\test_portal_silent_completion.py -q
python -m pytest tests\e2e\web_portal\test_operations_panel_workflow.py -q
radon cc web_portal\services\operation.py web_portal\services\output_scan.py -j | complexity-gate --max 10
bandit-exclude-check
python -m bandit -c pyproject.toml -r .
vulture src\ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src\ wsgi.py web_portal
interrogate src\ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v
symbol-diff --base origin\main web_portal\services\operation.py
symbol-diff --base origin\main web_portal\services\output_scan.py
python -B -m pytest -p no:cacheprovider -s -q tests\guardrails\local_test_quality_loop\test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github\test-quality-config.toml --baseline .github\test-quality-baseline.json --changed-from origin\main --full-gate-path .github\workflows\ci.yml --full-gate-path requirements-dev.txt
```

Run the two `pytest-chunks` commands from `.github/copilot-instructions.md` before the push.
Run the full test-quality gate before a manual CI request or push.

## Complexity Tracking

No new constitution violation is required.
The implementation will make narrow changes inside existing grandfathered modules.
