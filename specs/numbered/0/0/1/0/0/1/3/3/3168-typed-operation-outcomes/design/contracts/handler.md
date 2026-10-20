# Handler Return Contract

## Scope

This contract establishes `OperationOutcome` for future producer migrations.
The portal does not consume it yet. Issue #3168 remains open.

Import the type from `src.foundation.models.operation_outcome`.
Do not create an alias or a second type with the same purpose.

## State Meaning

| State | Meaning |
| - | - |
| `completed` | The requested work succeeded. A later caller verifies any required output evidence. |
| `no_output` | The work succeeded and intentionally produced no result records. |
| `missing_input` | Required input or context was absent. The work did not complete. |
| `failed` | The requested work failed, including a failure caught by the handler. |

Supply a nonblank operator message for every state.
Use optional nonblank detail for additional explanation.
Never include credentials or private response data in either field.

Preserve the state independently of wording. A warning can contain failure
words without changing a completed state. An actual failure needs no marker phrase.
The model validates field shape, not the truth of the handler's report.

## Producer Migration

Migrate each normal, empty, missing-input, and caught-failure return path.
Inspect every caller before replacing an existing boolean or data return.
Do not wrap an untyped result with an assumed successful outcome.
Do not change a shared helper's data contract merely because a handler calls it.

The next batch inventories current named handlers and their callers.
It migrates the existing value-return handlers with focused behavior tests.
Later batches migrate named operation families and the lambda rows.
The lambda batch requires a separate issue and exclusive ownership of `MistHelper.py`.

## Final Portal Replacement

Do not change portal classification during producer migration.
After all supported producers return this type, replace the classifier in one batch.
Delete the marker tuples, private prose readers, and prose-dependent tests.
Do not add a compatibility fallback.

The final batch must verify typed state and message behavior through REST,
SSE, and the browser. Unknown or absent outcomes must fail explicitly.
An output file must not override a typed failure.
An empty file must not override `no_output`.

The preserved migration sequence is in
[PR #4019](https://github.com/jmorrison-juniper/MistHelper/pull/4019).
Its inventory is historical. Use the current measurement in
[research.md](../research.md) as the starting point.
