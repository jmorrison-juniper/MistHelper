# Research: Block child submission after a multi-site cancel

**Issue**: #3327

## Decision 1: Guard the child claim

- **Decision**: Read the aggregate cancellation marker inside the child claim
  compare-and-set update.
- **Rationale**: A read before the compare-and-set update leaves the same race.
  The marker and the child state must decide one atomic winner.
- **Alternative**: Refuse every cancel while a parent submission claim exists.
  This can make an operator wait for all child requests.

## Decision 2: Guard new parent claims

- **Decision**: Refuse a new parent submission claim after the cancellation
  marker exists.
- **Rationale**: The child guard prevents cloud writes, but the parent guard
  also prevents repeated no-op submission requests.

## Decision 3: Retry only an unavailable cancel

- **Decision**: A second cancel can replace `unavailable` only when the child
  now holds a cloud job identifier.
- **Rationale**: The first result proved that the cancel had no cloud job to
  reach. A later identifier changes that fact.
- **Alternative**: Replace all prior results. This can repeat a destructive
  cancellation request with an unknown outcome.

## Evidence

- `_claim_child` previously checked only `status == "planned"`.
- `_cancel_child` previously skipped every child that held any result.
- The new concurrency test fails on both old decisions.
