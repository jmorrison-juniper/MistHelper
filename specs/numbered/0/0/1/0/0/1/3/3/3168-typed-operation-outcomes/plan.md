# Implementation plan: typed operation outcomes

**Issue**: #3168 part B  
**Specification**: [spec.md](spec.md)  
**Base**: `origin/main` at `f1505203d1d5ec845c94cb54f55118d613cf4e49`

## Delivery rules

1. Wait for pull request #4001 to merge.
2. Start every implementation issue from the latest merged `main`.
3. Keep one open pull request for `MistHelper.py`.
4. Do not add a prose fallback or a compatibility alias.
5. Use mocked or stubbed clients for focused tests.
6. Keep generated artifacts under the controlled `data/` location.
7. Do not make Mist write calls.

## Batch list

### Batch 0: Part A merge gate

Wait for #4001. Rebase the first implementation branch on the merged
`main`. Resolve overlap only after the part A files are on `main`.

### Batch 1: Define the portal contract

Create the frozen `OperationOutcome` model and the contract tests. Record the
four states, message rules, and detail rules. Do not change portal
classification until all producers in the next batches are ready.

Expected files:

- `src/foundation/models/operation_outcome.py`
- Focused model and portal contract tests

### Batch 2: Migrate existing named return handlers

Migrate the six named handlers that already return values. Replace each
existing return value with an `OperationOutcome` that preserves the existing
meaning. Add focused tests for each state.

Do not change `MistHelper.py` in this batch unless a handler definition is
required for a complete named-handler contract.

### Batch 3: Migrate remaining named handlers

Migrate the remaining 163 resolved named handlers by operation family. Give
each handler an explicit return annotation and a typed result for normal,
empty, missing-input, and failed paths that the handler can report.

Use one serial issue per operation family when the file set is independent.
Do not open a later issue against a shared file before the earlier issue
merges.

### Batch 4: Convert lambda handlers

Open a separate issue for the 112 lambda menu rows. Convert each lambda to a
named function with an explicit return annotation and a typed outcome.

This batch owns `MistHelper.py`. It must not include the portal cutover or
unrelated menu changes.

### Batch 5: Cut over the portal

After all supported producers return `OperationOutcome`, change
`_capture_and_run` to consume the result. Remove the marker tuples, prose
readers, and prose-dependent tests in the same batch.

Update REST and SSE contract tests. Verify that the browser receives the
typed state and operator-facing message.

### Batch 6: Full contract verification

Run the focused tests and the applicable repository gates. Inspect the
changed symbols and generated artifacts. Confirm that no prose classifier,
fallback branch, or duplicate `OperationOutcome` remains.

## Required test changes

Update the following assertions in the implementation batches:

| Test | Required assertion |
|---|---|
| `tests/unit/export/test_endpoint_family_exporter.py:592` | The empty trend result returns an explicit typed outcome. The test must not accept a silent discard. |
| `tests/unit/marvis/actions/test_alarms.py:30,328` | The test must not import or inspect `HANDLED_ERROR_MARKERS`. It must assert the typed result. |
| `tests/unit/marvis/actions/test_portal_contract.py:109,113` | The test must exercise the typed portal contract, not private prose classifiers. |

Add tests for each allowed state, REST output, SSE output, handler exceptions,
and missing or empty results.

## Validation commands

Run the smallest applicable command after each implementation batch:

```powershell
python -m pytest tests/unit/web_portal/test_portal_silent_completion.py
python -m pytest tests/unit/marvis/actions/test_portal_contract.py
python -m pytest tests/unit/marvis/actions/test_alarms.py
python -m pytest tests/unit/export/test_endpoint_family_exporter.py
python -m ruff check <changed Python files>
python -m black --check <changed Python files>
python -m mypy <changed Python files> --config-file pyproject.toml
python -m py_compile MistHelper.py
symbol-diff --base origin/main <changed Python files>
```

Run the full repository gates before the final pull request. Do not claim a
gate passed unless the command produced a successful result.

## Risks and controls

| Risk | Control |
|---|---|
| Part A overlap | Merge #4001 before implementation. |
| Hot-file contention | Isolate the 112-lambda conversion. |
| Duplicate type names | Supersede the unshipped 1021 model. |
| Hidden prose dependency | Remove the marker tuples and private readers in the cutover batch. |
| User-visible message drift | Test REST, SSE, and browser message paths. |
| Mutating validation | Use mocks and stubs only. |

## No issue filing in this specification

The implementation issues are listed here only. Do not file them as part of
this specification task.

- Typed outcome model and contract.
- Six existing value-return handler migrations.
- Named handler family migrations.
- 112-lambda conversion in `MistHelper.py`.
- Portal cutover and prose classifier removal.
- Final contract and gate verification.
