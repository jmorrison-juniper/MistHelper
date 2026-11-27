# Contract: Resume route (single site)

## Route

- **Method and path**: `POST /api/runs/<run_id>/resume`. This route is new.
- **Body fields**: `confirm`, one text value. The body can be a form or JSON.
- **Typed word**: `RESUME`. The match is exact and case sensitive. The route does not trim the value.

## Refusal rules

The route checks the rules in this order. The first failed rule ends the request.

1. The typed word must equal `RESUME`.
2. The run must exist.
3. The run state must be `stopped`, and the run must hold a recovery point.
4. No driver thread may be live for the run.
5. The site must not be held by another operator.
6. The site hold must be clear, or the reconciliation must prove the outcome.
7. The verified write of the resume attempt must succeed.

## Responses

| Status | Code | When | Operator message | Mist request |
| - | - | - | - | - |
| 200 | none | The resume starts | The run resumes at the recovery phase. The portal reads the live devices first. | Reads, and at most one firmware call |
| 400 | confirmation_required | The typed word is missing or wrong | The resume control needs the exact text RESUME. | None |
| 404 | run_not_found | The run key is unknown | The run was not found. Open the run list and choose the run again. | None |
| 409 | run_not_resumable | The run is not stopped, or it has no recovery point | This run has no stopped phase to resume. Read the run page for the next step. | None |
| 409 | run_active | A driver thread is live for the run | This run still has a live driver thread. Wait for the run to end. | None |
| 409 | site_locked | Another operator holds the site | Another operator holds this site. Ask that operator before you try again. | None |
| 409 | site_hold_active | The outcome of the recovery phase is not proven | The portal cannot prove the outcome of the stopped phase. Read the evidence on the run page. | Reads only |
| 503 | resume_store_unavailable | A verified write failed | The portal could not save the resume. The site stays held. Try again after the store recovers. | Reads only |

## Idempotency

A second request after a successful start meets state `resuming`. The route refuses it with `run_not_resumable`. The second request sends no Mist request.

## Logging

- Before the reconciliation, the route writes one info line that names the run key and the phase.
- After each read, the route writes one debug line with the counts.
- The route never writes the actor email, the typed word, or any token.

## Multi-site

The multi-site route is defined in this contract when issue #4021 merges. It uses the same refusal order and the same messages. Its path is `POST /upgrade/org/resume`, and it takes the same `confirm` field.
