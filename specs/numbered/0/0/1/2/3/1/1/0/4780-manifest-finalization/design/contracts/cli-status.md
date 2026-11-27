# Contract: CLI Run Status and Parent Session State

This contract covers the console lines of the hardware collection and the state of the public parent session.

## Console Lines

After the target results print, the CLI prints these lines in order.

1. For each run whose output is not final, one line in this form: `Batch output not final for run <run_id>. Native files are kept.` The `<run_id>` value is the 32-character run folder name, not a path.
2. The run status line, `Run status: partial` or `Run status: complete`. This line stays the last line of the output.

Rules:

- A run with a final output prints no unfinished-run line.
- The run status reads partial when a target did not collect, when a run output is not final, or when the operator stopped the batch.
- The report and master XML lines keep their existing form.

## Parent Session State

| Condition | State | Reason text |
|-----------|-------|-------------|
| `artifacts.finish()` returns False | FAILED | The batch output could not be finalized. |
| The target status is stopped | STOPPED | The batch stopped. |
| The target status is failed | FAILED | The batch finished. |
| Any other target status | FINISHED | The batch finished. |

The first row is new. The other rows keep the existing rule at `factory.py:354`.

## Portal Summary

- `artifact_status` keeps its values: `writing`, `ready`, and `failed`.
- A failed finalization reports `artifact_status` as `failed`.
- The batch summary holds no new key.
