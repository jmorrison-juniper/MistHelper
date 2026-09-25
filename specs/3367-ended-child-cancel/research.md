# Research: Send no cancel request to a child job that already ended

**Issue**: #3367

## Decision 1: Use the stored child state

- **Decision**: The service reads the state that the last status read stored.
  It sends no extra status read before the cancel.
- **Rationale**: The single-site stop decides from the stored run state, and it
  sorts the devices from the stored status answer. The page reads each child
  job every 30 seconds. An extra read on the cancel path adds one cloud call
  for each child job and one more failure path.
- **Alternative**: A fresh status read before each cancel call. The spec
  rejects it for this issue, because the single-site stop does not do it.

## Decision 2: Keep the identifier check first

- **Decision**: A child job with no upgrade identifier keeps the result
  `unavailable`.
- **Rationale**: The cancel outcome panel reads `unavailable` with the raw
  status to prove that no cloud job exists (issue #3327). A rejected child job
  with no identifier must keep that proof.

## Decision 3: Store three empty lists and a note

- **Decision**: The ended result stores three empty lists. The panel shows the
  message and a note, and it hides the three lists.
- **Rationale**: The empty text of the third list reads "Every device has a
  cancel path." That sentence is not true for a child job that ended. The note
  states the fact once, and no list can name a device of the child job.

## Decision 4: One status word

- **Decision**: The status word is `already_ended`, and the result also stores
  the final state in the field `state`.
- **Rationale**: The Cancellation cell prints `Status: already_ended.` and the
  message. The word differs from every cloud word, so no reader can take it for
  a cloud answer.

## Evidence

- `AggregateUpgradeService._cancel_child` checks only the stored cancel claim.
- `AggregateUpgradeService._cancellation_result` refuses only a child job with
  no upgrade identifier.
- `test_mixed_status_and_cancellation_keep_all_results` pins the old behavior.
  It asserts `ap_child["cancellation"]["cancelled"] == ["001122334455"]` for an
  access point child job in the state `completed`.
