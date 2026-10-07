# Implementation Plan: Operation Stream Recovery

**Branch**: `jmorrison-juniper-sse-run-state-4027` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Approved feature specification for issues #4027 and #4032.

## Summary

Repair the Operations page in `web_portal/static/js/operations.js`.
The browser will check the existing status endpoint every five seconds while
an operation stream stays active. One request can be active at a time.
Each timer, response, and stream event will verify the current run identity.
Any terminal transition will close the stream and clear the status timer.

The same browser controller will replace each run output presentation from an
exact path set. Identity will combine `run_id` and the exact server path.
An identical replay will not render links or load the preview again.
A terminal empty set will clear only the output presentation.
It will not replace the terminal message.

## Technical Context

**Language/Version**: Browser JavaScript as used by the existing portal, with Python 3.13 or newer for tests

**Primary Dependencies**: Browser `EventSource`, Fetch API, Bootstrap DOM classes, Flask portal, Playwright 1.63.0, pytest-playwright 0.9.0

**Storage**: Existing in-memory operation records behind `GET /api/operations/status/<run_id>`

**Testing**: Pytest and Playwright with a controlled `EventSource`, intercepted status responses, and intercepted preview responses

**Target Platform**: Current desktop browsers on Windows 11, macOS, and Linux

**Project Type**: Existing Flask web portal with a browser controller

**Performance Goals**: One status request per active run every five seconds, with no overlapping status requests

**Constraints**: No server contract change, no manual reconnect requirement, exact path identity, one dedicated browser test module

**Scale/Scope**: One browser controller, one Playwright module, two existing release-note fragments, and this feature record

## Constitution Check

*GATE: Passed before research. Passed again after design.*

- The feature uses the approved managed numeric specification route.
- The two changelog files are unique issue records under `changelog.d/`.
- The change creates no product output outside `data/`.
- Browser test evidence can use the ignored `test-artifacts/` directory.
- The change uses no Mist Cloud transport and adds no direct Mist API request.
- The existing status route and output discovery contracts remain unchanged.
- The implementation will not change a destructive operation.
- The implementation will not add a top-level declaration to the already
  noncompliant `operations.js` module.
- The implementation will replace the `currentSSE` scalar with one state
  record. The replacement reduces declaration pressure and holds cleanup data.
- The implementation will touch the existing long `startSSEStream` function.
  This function is grandfathered structural debt.
- A separate remediation action must divide the Operations controller after
  this repair. That action must not enter the #4027 or #4032 commits.
- Each generated code line must receive an inline cause or purpose comment.
- Each browser request must have a before log and an after result log.
- Commit subjects and the pull request title must use accepted Conventional
  Commit forms.

### Required File Boundary

The implementation may change only these product and test files:

```text
web_portal/static/js/operations.js
tests/e2e/web_portal/test_operation_stream_recovery.py
changelog.d/issue-4027-operation-stream-recovery.md
changelog.d/issue-4032-output-replay-deduplication.md
```

The implementation must not change these files:

```text
web_portal/services/operation.py
web_portal/services/output_scan.py
MistHelper.py
tests/e2e/web_portal/test_operations_panel_workflow.py
```

Planning files in this feature directory are also in scope.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/2/1/0/2/4027-operation-stream-recovery/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/
│   └── browser-operation-run-state.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
web_portal/
└── static/
    └── js/
        └── operations.js

tests/
└── e2e/
    └── web_portal/
        └── test_operation_stream_recovery.py

changelog.d/
├── issue-4027-operation-stream-recovery.md
└── issue-4032-output-replay-deduplication.md
```

**Structure Decision**: Keep the repair in the existing browser controller.
Add one dedicated Playwright module for both issue contracts.
Keep one release-note fragment for each issue.

## Browser Design

### Run State

Replace the `currentSSE` scalar with one browser state record.
Keep `currentRunId` as the active run identifier.
The state record will hold these values:

- The current `EventSource`.
- The current five-second status timer.
- The run identifier of the active status request.
- The run identifier that reached a terminal state.
- The run identifier for the displayed output set.
- The ordered exact paths in the displayed output set.
- The canonical output identity signature.
- Whether an output set was applied for the displayed run.

The replacement must not add another top-level declaration.

### Five-Second Status Check

`startSSEStream(runId)` will schedule one `setTimeout` for 5,000 milliseconds.
It will not use a second interval.
`checkRunStatus(runId)` will refuse a request when another status request is
active.

After a `running` response, the browser will schedule the next five-second
check. It will schedule the next check only after the current request settles.
This rule guarantees one in-flight request.

Each response will compare its captured `runId` with `currentRunId`.
It will also reject a run that already reached a terminal state.
A late `running` response cannot replace a completed or failed presentation.

### Terminal Transition

A completed response will set the final progress, set the completion message,
apply the full output set, and finish the matching run.
A failed response will set the failure message, append the error line, and
finish the matching run.

`finishRun(runId)` will act only for the matching run.
It will clear the status timer, close the matching stream, and clear request
ownership.
It will then mark the run terminal before it clears `currentRunId`.

Starting another run or reconnecting will clear the old timer and close the
old stream before it creates new run state.
An `EventSource.onerror` path will also clear the timer before its final status
check.

### Output Replay

`showOutputFiles` will receive `runId`, the complete path list, and terminal
context.
It will remove duplicate exact paths from one delivery.
It will preserve the first order of each distinct exact path.

The canonical identity will use `runId` plus each full server path.
It will not use a base file name.
The browser will compare identity sets without path-order differences.

If the identity set matches the applied set, the browser will return before it
changes links or calls `OperationResults.showForRun`.
If the identity set changes, the browser will replace the link list.
It will not append to the existing list.

For a terminal empty set, the browser will hide and clear the output list.
It will call `OperationResults.reset()` to remove stale preview loading state.
It will not call `resetExecutionPanel`, because that function resets the
terminal status message.

## Test-First Commit Sequence

Implementation must use these separate commits in this order:

1. `test(web-portal): reproduce operation stream recovery failure`
   Add only the #4027 failing cases to the dedicated Playwright module.
   Run the #4027 selectors and record the expected failure.
2. `fix(web-portal): recover terminal operation status`
   Repair #4027 in `operations.js`.
   Include the #4027 release-note fragment.
   Run the #4027 selectors and record the pass.
3. `test(web-portal): reproduce output replay duplication`
   Add only the #4032 failing cases to the same dedicated module.
   Run the #4032 selectors and record the expected failure.
4. `fix(web-portal): make output replay idempotent`
   Repair #4032 in `operations.js`.
   Include the #4032 release-note fragment.
   Run all tests in the dedicated module and record the pass.

Do not combine a failing test with its repair.
Do not combine the two repairs in one commit.

## Playwright Proof

The dedicated module will install a controlled `EventSource` before page
scripts load.
The test double will record listeners, emitted terminal events, close calls,
and error-handler calls.

The module will replace only five-second browser timeouts with immediate test
timeouts. It will record the requested delay and assert 5,000 milliseconds.
Other timeout values will keep their normal behavior.

The module will intercept the status endpoint.
One case will return `running` and then `completed`.
Another case will return `failed`.
Neither case will call the stream error handler.

The module will intercept result preview requests.
It will count each preview load.
The #4032 cases will cover these inputs:

- One exact path from status replay and terminal event replay.
- Two distinct exact paths with the same base file name.
- The same exact path under two run identifiers.
- A terminal empty output set after a visible loading presentation.

The tests will print the required examined counts.
The output will name status checks, terminal transitions, replay sources,
exact paths, rendered links, and preview loads.

## Validation Gates

Run the smallest browser proof after each red or green commit:

```powershell
python -m pytest tests\e2e\web_portal\test_operation_stream_recovery.py -q -s
```

After the final repair, run these applicable gates:

```powershell
python -m ruff check tests\e2e\web_portal\test_operation_stream_recovery.py
python -m black --check tests\e2e\web_portal\test_operation_stream_recovery.py
python -m pytest tests\e2e\web_portal\test_operation_stream_recovery.py -q -s
python -m pytest tests\guardrails\test_changelog_fragment_policy.py -q
```

Run the test quality preflight before the required committed comparison.
Run `test-quality-analyzer` after the test commits exist.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `operations.js` already has more than five top-level names. | The approved scope requires a narrow repair in this controller. The design replaces one declaration and adds none. | A new browser module would expand the measured product scope and require another script contract. |
| `startSSEStream` already exceeds 25 lines. | The repair must add status recovery to the active stream lifecycle. | A full controller division would mix structural work with two urgent defects and would block separate red and green commits. |

The separate remediation action is a later controller division.
It must preserve the browser contract from this feature.
