# Contract: Stop Record

The stop record is the durable evidence of one stop. It is stored in the parent record under the key `family_stop`. A run with no stop has no `family_stop` key.

## Shape

```json
{
  "family": "switch",
  "reason_code": "refused",
  "child_ids": ["child-3f2a9c41"],
  "gate_state": "not_run",
  "sentence": "The cloud refused a switch firmware call. The run stopped before the next family. Read the run before any new action.",
  "stopped_at": "2026-11-26T18:00:00+00:00"
}
```

## Fields

- `family`: The family where the stop occurred. The value is `gateway`, `switch`, or `ap`.
- `reason_code`: One code from the table below.
- `child_ids`: The child identities that the stop affects. The list holds the refused child, the unknown child, or each child that did not start.
- `gate_state`: The family gate state before the stop. The value is `not_run`, `settled`, `failed`, or `unknown`.
- `sentence`: The operator sentence from the table below. The sentence holds no host, token, or cloud body.
- `stopped_at`: The UTC time in ISO 8601 form.

## Reason Codes

The text `{family}` in the table below is replaced by the family name of the stop at run time.

| Reason code | Trigger | Operator sentence |
| - | - | - |
| `refused` | A child has the status `rejected`. | The cloud refused a {family} firmware call. The run stopped before the next family. Read the run before any new action. |
| `unknown_outcome` | A child has the status `submission_unknown`. | The cloud reply for a {family} firmware call is unknown. The run stopped and sent no retry. Read the cloud state before any new action. |
| `gate_failed` | The family gate returned `failed`. | The {family} family did not settle within the phase limit. The run stopped before the next family. Read the devices, then the run. |
| `gate_unknown` | The family gate returned `unknown`. | The portal cannot prove that the {family} family settled. The run stopped before the next family. Read the run before any new action. |
| `lock_lost` | A site lock of the run was lost before a child claim. | A site lock of this run was lost. The run stopped before the next write. Read the run before any new action. |
| `cancelled` | A cancellation request exists before a child claim. | A cancellation request stopped the run before the next family. Read the run before any new action. |
| `process_lost` | The wait marker is older than the claim lease. | The portal stopped while it waited for the {family} family. The run sent no retry. Read the run before any new action. |

## Write Rules

- The stop record is written through compare-and-set before the background run ends.
- The compare-and-set write retries within the bounded attempts of the existing helper. A failed write ends the run without a new cloud call.
- A run holds at most one stop record. A second stop does not replace the first.
- The stop record is one-way. No later write removes it.
- Issue #4022 reads this record for resume. This change does not resume a run.
