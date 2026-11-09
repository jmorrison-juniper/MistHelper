# Implementation Plan: Site export write results

## Technical Context

The two persistence methods discard the Boolean writer result.
Their success messages therefore describe failed writes as successful exports.
The writer contract already returns `bool`.
No dependency, schema, transport, or public signature change is necessary.

## Constitution Check

The source classes already contain long persistence methods and more than five module-level names.
This repair changes only the reserved methods and does not add a source declaration.
It preserves the existing structure instead of expanding the repair into an unrelated refactor.
A later, separately reserved change can reduce the existing method and module debt.
The shared tests already exceed five module-level names.
The new test class contains five members.
The unique changelog fragment uses the process-record exception.
The specification uses the eight-level numeric route and at most five children per new directory.

## Phase 0: Research

**Decision**: Capture the Boolean writer result and return immediately after an error on failure.

**Reason**: The output writer owns persistence. The caller must not infer success from the absence of an exception.

**Alternative rejected**: Raising a new exception would change the existing persistence return contract.

## Phase 1: Design

**Data model**: The existing rows, sanitized rows, filename, and endpoint name remain unchanged.

**Interface contract**: The persistence methods still return `None`. Writer exceptions still propagate to the existing menu handlers.

**Failure output**: An error names the endpoint and filename. No success count follows that error.

**Success output**: The current persistence trace and exported-record message remain unchanged.

## File Ownership

Only these existing paths enter the repair:

- `src/operations/exporting/export/site_application_list_exporter.py`
- `src/operations/exporting/export/site_system_events_exporter.py`
- `tests/unit/export/test_site_asset_and_events_exporters.py`

The issue also owns this specification directory and `changelog.d/issue-4717-site-export-writer-results.md`.
The public reservation is issue comment `6745705768`.
The live check found 27 open pull requests and no reserved-path overlap.

## Verification

Run the independent reproduction before and after the repair.
Run the shared tests with explicit writer outcomes, empty data, exceptions, and menu entry points.
Block socket, DNS, and SQLite access before test collection.
Run targeted compile, lint, format, type, complexity, security, symbol, and test-quality checks where available.
Preserve exact commands and results in the session artifacts.
PowerShell setup commands are unavailable. Keep the existing branch and specification selector unchanged.
Skip optional intermediate commit hooks. Create the requested final local commit without a push.
