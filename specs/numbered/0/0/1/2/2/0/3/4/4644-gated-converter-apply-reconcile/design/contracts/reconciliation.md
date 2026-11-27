# Contract: Reconciliation

This contract defines how `ReconciliationReader` and `OutcomeClassifier` classify an outcome. It uses read calls only after the write. It makes no write call during reconciliation.

## Classification Steps

1. After each write call, `OutcomeClassifier` maps the HTTP status or the transport error to one class, as the table below shows.
2. For a class that allows a read-back, `ReconciliationReader` reads the object with the matching R operation from `mist-write-families.md`.
3. `ReconciliationReader` compares each approved field with the read-back value. It compares the digest of the unrelated fields with the before-state digest.
4. The item outcome is `verified` only when both comparisons match. A mismatch gives `partial`.
5. The operation phase follows the rules in `data-model.md`.

## Status Class Map

| Class | Source | Read-back | Outcome |
| --- | --- | --- | --- |
| 2xx with a valid body | Response | Yes | `verified` or `partial` |
| HTTP 400, 401, 403, or 404 | Response | Yes | `failed` |
| Final HTTP 429 | Response after SDK retries | Yes | `indeterminate` |
| HTTP 5xx | Response | Yes | `indeterminate` |
| Timeout | Wait bound from decision D-8 | Yes | `indeterminate` |
| Connection loss or proxy error | SDK `APIResponse` with no response | Yes | `indeterminate` |
| Malformed success body | Response | Yes | `indeterminate` |
| Create with no natural ID | Response and read | Yes | `indeterminate` |
| Item after a stop | Run state | No | `not-applied` |

## Rules

- A read-back for an indeterminate outcome does not clear the indeterminate state by itself. The phase moves to `reconciled` only after the read finishes.
- A reconciliation read never writes. The test TST-21 counts the write calls and expects zero.
- A new write needs a new approval and a new operation. A reconciled outcome never starts a write.

Warning: A reconciled `indeterminate` outcome can still hide a completed change. The operator must review the object in Mist before creating a new approval.
