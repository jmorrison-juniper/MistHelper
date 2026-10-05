# Implementation Plan: WebSocket Operation Form Cancellation

**Branch**: `3760-websocket-form-cancellation` | **Date**: 2026-10-04 | **Spec**: `spec.md`

**Input**: Feature specification from `specs/3888-websocket-form-cancellation/spec.md`

## Summary

Add an explicit Cancel action for an unsubmitted WebSocket operation selection.
Cancellation must clear the authoritative pending selection and its values,
invalidate every picker read started for that selection, and leave started
sessions unchanged. The current page keeps `state.selectedEntry` inside a
private closure in `web/static/websockets.js`; the start handler checks that
state before sending a request. Therefore a template-only change or a separate
controller that only clears visible controls cannot satisfy the contract.

**Implementation status**: The source-ownership blocker is resolved. PR #3814
and PR #3891 have merged, so this worktree owns the existing page controller
changes needed for authoritative cancellation and picker response fencing.
The implementation stays inside the existing controller, template, and
browser test module. The focused browser regression, related browser tests,
and CI mypy scope pass.

## Technical Context

**Language/Version**: Python 3.13+ for the portal and tests; browser JavaScript
for the WebSocket page.

**Primary Dependencies**: Flask/Jinja templates, existing vanilla JavaScript
page code, pytest, and Playwright browser tests. No new runtime dependency.

**Storage**: None. Pending form state remains client-side; no persistent or
server-side record is introduced.

**Testing**: pytest; a normal-user Playwright browser regression using the
existing fake portal harness, with delayed picker responses and request
observation. No live Mist operation is needed.

**Target Platform**: The Operations portal in a supported desktop browser.

**Project Type**: Server-rendered web portal with a browser-side controller.

**Performance Goals**: No new polling or network round trips. Cancellation
must be immediate; stale picker callbacks must return without visible or
shared-state effects.

**Constraints**:
- Keep the change in the existing template, controller, and browser test
  module. PR #3814 and PR #3891 have merged.
- Do not modify `tests/tools/websocket_dialog_audit` or
  `specs/3760-issue3862-websocket-dialog-audit`.
- Do not change issue #3890 catalog text or `utility_text`.
- Cancellation applies only before submission and must not affect session
  cards or issue a session-stop request.
- Do not add a direct child to an already overfull source or test directory.
  Keep the regression in the existing browser test module.
- This feature introduces no Mist API request or owned WebSocket transport.

**Scale/Scope**: One shared start form serves the catalog's 72 live operation
entries. No catalog entry or operation behavior is added or removed.

## Constitution Check

*Gate result: PASS for the selected implementation and documentation surface.*

- **Five-item rule**: `spec.md`, `.spec-context.json`, `plan.md`, `tasks.md`,
  and `checklists/` are the five direct children of this feature directory.
  The feasibility notes are captured in this plan, so no separate
  `design-notes.md` file is needed. Store other generated design artifacts
  inside the existing `checklists/` child. The source static directory and
  WebSockets E2E directory already exceed five direct children; do not add
  new files there. The issue-specific release fragment is a required unique
  record in the established process directory and is covered by the
  constitution's process-record exception.
- **Separate incremental remediation**: Track a separate follow-up to
  incrementally remediate the existing overfull source/test directories.
  This plan does not restructure unrelated files or directories.
- **Authoritative state**: Keep cancellation and selection-generation
  behavior in the existing page controller. Do not create a second state
  owner or a sidecar controller.
- **Safety**: Cancel is a local discard of unsent form state. It must not call
  a start endpoint, a session stop endpoint, or any live operation.
- **Deployment/release process**: Add exactly one issue-specific
  `changelog.d/issue-3888-websocket-form-cancellation.md` fragment. Do not edit
  `CHANGELOG.md`. Any later implementation must follow the full deployment
  pipeline and use a Conventional Commit title accepted by repository policy.
- **Product output**: No product data is generated; no output is placed in
  `data/`.
- **Mist Cloud/API gate**: No new Mist REST or WebSocket transport is
  proposed. Existing picker routes remain unchanged; no transport contract or
  SDK replacement is in scope.

## Design and Integration

The integrated design follows `checklists/research.md` and
`checklists/contracts/ui-cancellation.md`:

1. Treat the selected catalog entry as the authoritative pending operation.
2. Advance a monotonically changing selection generation on every selection
   replacement and on Cancel.
3. Capture the generation and exact selected-entry object for each picker
   read. Discard successful, empty, and failed replies before DOM or shared
   `state.labels` changes when either identity is stale. Keep the per-control
   request serial for reads within one current selection.
4. Cancel clears the authoritative selection, target and parameter controls,
   confirmation, notices, errors, and selected-entry styling. It disables
   Start and leaves session state untouched.
5. Hide Cancel while a start request is pending and after that entry submits
   successfully. A rejected start makes the unsubmitted form cancelable again.

## Implemented File Surface

### Implementation files

- `src/mist/realtime/websocket_streams/web/templates/websockets_page.html`:
  provides the form-only Cancel control.
- `src/mist/realtime/websocket_streams/web/static/websockets.js`:
  clears authoritative form state, fences picker replies, and keeps Cancel
  unavailable during submission.
- `tests/e2e/websockets_tab/test_websockets_terminal.py`: extends the existing
  fake-harness browser coverage with catalog, cancellation, stale-picker, and
  live-session checks.
- `changelog.d/issue-3888-websocket-form-cancellation.md`: exactly one
  issue-specific release fragment.
- `specs/3888-websocket-form-cancellation/plan.md`, `tasks.md`, and
  `.spec-context.json`: record the cleared ownership gate and progress.

### Scope note

No backend picker route, catalog entry, session service, `utility_text`, or
session-card control changes. No sidecar JavaScript file is added.

## Project Structure

### Documentation (this feature)

```text
specs/3888-websocket-form-cancellation/
├── spec.md
├── .spec-context.json
├── plan.md
├── tasks.md
└── checklists/
    ├── requirements.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    └── contracts/
        └── ui-cancellation.md
```

### Source Code (repository root)

```text
src/mist/realtime/websocket_streams/web/
├── templates/
│   └── websockets_page.html      # form-only Cancel control
└── static/
    └── websockets.js             # authoritative cancellation and picker fence

tests/e2e/websockets_tab/
└── test_websockets_terminal.py   # existing fake-harness browser regression

changelog.d/
└── issue-3888-websocket-form-cancellation.md
```

**Structure Decision**: Reuse existing page and browser-test modules. Do not
add a controller source file or browser-test file to directories that already
exceed the five-item limit. Cancellation and picker fencing now live in the
existing page controller.

## Complexity Tracking

| Constraint | Why it remains | Resolution |
|---|---|---|
| Resolved ownership | PR #3814 and PR #3891 have merged, so the existing controller was available for this integration. | The authoritative selection remains in the existing controller. |
| Existing directory-count debt | The source static directory and WebSockets test directory already exceed the five-child limit. | Reuse their existing files and add no direct child there. |
| Focused browser validation | The targeted normal-user Playwright regression is the applicable local validation gate for this feature. | `.venv/bin/python -m pytest tests/e2e/websockets_tab/test_websockets_terminal.py -k 'cancellation or cancel_is_hidden' -q` passed: 2 tests, using fake routes only. |
