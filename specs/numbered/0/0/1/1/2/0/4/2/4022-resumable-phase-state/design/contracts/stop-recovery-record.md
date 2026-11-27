# Contract: Stop recovery record

## Purpose

This contract names the durable fields that a stop writes to the run document. Each field has a fixed set of values. A reader uses these fields to show the next step and to decide whether a write may start.

## Run document fields (additive)

| Field | Type | Written by | Read by | Rule |
| - | - | - | - | - |
| `recovery_point` | object or absent | Stop path and failure path | Run page, resume route, retry route | Present only when a phase is unsettled. Absent for a clean complete run. |
| `resume_attempts` | list | Resume route | Run page | Append only. Each entry is verified before the resume continues. |
| `phases[].submission` | text | Submission path | Run page, reconciliation | One of `not_sent`, `accepted`, `refused`, or `unknown`. |
| `phases[].submitted_at` | text or null | Submission path | Run page | ISO 8601 UTC. Null when `submission` is `not_sent`. |

## Recovery point object

```json
{
  "phase": "switches",
  "reason": "The portal did not confirm the switch upgrade call.",
  "submission": "unknown",
  "stopped_at": "2026-11-26T18:00:00Z",
  "hold": true,
  "next_step": "Read the evidence on the run page, then type RESUME if the evidence shows no job."
}
```

The example above is one valid value. It contains no secret. It names no operator.

## Value rules

- `phase` is one of `gateways`, `switches`, `aps`, or `clients`. The value `clients` appears only for an observation stop. The resume never submits the clients phase.
- `submission` is one of `not_sent`, `accepted`, `refused`, or `unknown`.
- `hold` is `true` when `submission` is `unknown`, or when `submission` is `accepted` and the phase is unsettled.
- `reason` and `next_step` are plain sentences. Each sentence has one idea.

## Invariants

1. A run with a recovery point has state `stopped`, `resuming`, or `failed`.
2. A run with `hold` set to `true` keeps its site lock or its durable hold.
3. A phase with state `settled` or `skipped` never changes back to `pending`.
4. The field `resume_attempts` never shrinks.
5. A write that the read-back does not confirm leaves the previous value in place.

## Compatibility

- Records without these fields stay valid. The run page shows no recovery card for them.
- An older release reads an unknown state name as an error. A rollback is unsafe while a run holds `resuming`. See plan.md.
