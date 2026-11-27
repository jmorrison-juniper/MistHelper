# Data Model: Persist resumable firmware phase state

## Entities and natural keys

| Entity | Storage | Natural key | Notes |
| - | - | - | - |
| Run | `upgrade_runs` document (RC-064) | `run_id`, with `org_id` and `site_id` | The run key already exists. This change adds fields only. |
| Phase entry | `phases` list of the run document | `name` (gateways, switches, aps, clients) | Existing fields stay. The field `submission` is new. |
| Recovery point | `recovery_point` object of the run document | one for each stopped run | Replaced at each stop. The record keeps no history here. |
| Resume attempt | `resume_attempts` list of the run document | `attempted_at` with `phase` | Append only. Each entry is verified (FR-003). |
| Site hold | Derived from `recovery_point.hold` and the phase submissions | `org_id` and `site_id` | No separate document. A query over the run store finds the holds for one site. |
| Reconciliation proof | `resume_attempts[].reconciliation` | `attempted_at` | Read-only counts and the verdict. |

## Field definitions

### Phase entry (additive)

- `submission`: one of `not_sent`, `accepted`, `refused`, `unknown`. The default is `not_sent`.
- `submitted_at`: an ISO 8601 UTC text. It is `null` for `not_sent`.

### Recovery point

- `phase`: the recovery phase name.
- `reason`: one plain sentence for the operator. It names the phase and the cause.
- `submission`: the submission state of the recovery phase.
- `stopped_at`: an ISO 8601 UTC text.
- `hold`: `true` when a phase is `unknown`, or when a phase is `accepted` and unsettled. Otherwise `false`.
- `next_step`: one plain sentence that names the operator action.

### Resume attempt

- `attempted_at`: an ISO 8601 UTC text.
- `phase`: the recovery phase at the attempt.
- `actor`: the operator work email address. The log never prints this value.
- `reconciliation`: counts for `at_target`, `not_started`, `job_found`, and `unproven`.
- `outcome`: one of `refused`, `observed`, `submitted`, or `hold_kept`.

## State transitions

### Run state

The state `resuming` is new in this change. The current `RunState` enum has no such state (RC-008). In the diagram, `settling_<phase>` stands for one of `settling_gateways`, `settling_switches`, `settling_aps`, or `settling_clients`.

```text
created -> pre_capture_running -> pre_capture_done -> awaiting_confirmation -> upgrade_submitting -> upgrade_running -> settling_gateways -> settling_switches -> settling_aps -> settling_clients -> post_capture_running -> post_capture_done -> complete
any live state -> stopping -> stopped (writes recovery_point)
stopped (recovery_point present) -> resuming (writes resume attempt) -> settling_<phase>
stopped (no recovery_point) -> no move (final)
any live state -> failed (writes error)
```

- `stopped` with a recovery point moves only to `resuming`. Other moves from `stopped` stay refused.
- `resuming` moves to `settling_<phase>` for the recovery phase, or to `stopped` again, or to `failed`.
- Each move is verified (FR-003). A failed verification keeps the hold (FR-004).

### Phase submission

```text
not_sent -> accepted      (firmware call returns an accepted reply with an identity)
not_sent -> refused       (documented refusal, no conflict)
not_sent -> unknown       (transport fault, 408, 429, 499, any 5xx, undocumented status, or a reply without identity)
unknown  -> not_sent      (reconciliation proves no job and no version change. The proof is recorded.)
unknown  -> accepted      (reconciliation finds a job)
refused  -> accepted      (resume after the operator confirms the repair and the reconciliation finds no job)
accepted -> settled       (settle gate reports settled)
accepted -> failed        (settle gate reports failed)
```

### Phase state (existing values, unchanged)

```text
pending -> waiting -> settled
pending -> skipped        (no device of the family)
waiting -> failed         (settle gate reports failed, or a refused submission)
failed  -> pending        (resume reset for the recovery phase only)
```

## Site hold rule

A site hold is active when any run at the site has a recovery point with `hold` set to `true`. The start route, the pre-check, the takeover, and the retry route refuse while a hold is active (FR-022). A resume of the same run may proceed only after its reconciliation proves the outcome (FR-014).

## Invariants

- Each phase submits at most once for each resume attempt (FR-013).
- A phase with state `settled` or `skipped` never returns to `pending` (FR-012).
- The recovery phase is the first phase in cascade order whose state is neither `settled` nor `skipped`. The clients phase is never a recovery phase.
- A device at its target version never receives a firmware call (FR-011).
- A `hold` value of `true` forces the lock to stay with the run until the hold clears (FR-018).
