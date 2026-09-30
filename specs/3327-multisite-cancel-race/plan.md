# Implementation Plan: Block child submission after a multi-site cancel

**Issue**: #3327 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Technical context

- Python 3.13.
- `AggregateUpgradeService` coordinates parent claims, child claims, and
  cancellation claims through compare-and-set writes.
- No schema change and no new dependency.

## Changes

1. `src/firmware/aggregate_upgrade_service.py`
   - Add a cancellation-request error for a safe submission stop.
   - Check the cancellation marker in the parent and child submission claims.
   - Stop the child loop when a concurrent cancel wins the child claim.
   - Let a second cancel replace only an `unavailable` result that now holds
     a cloud job identifier.
2. `tests/unit/firmware/test_aggregate_upgrade_service.py`
   - Add a deterministic test for the parent-claim and child-claim race.
   - Add a regression test for the second cancel.
3. `changelog.d/issue-3327-cancel-race.md`
   - State the operator-visible safety repair.

## Risks

- A child claim can win before the cancellation marker. The cloud write can
  then start, because the claim represents an in-progress destructive call.
- The second cancel repair limits the replacement to `unavailable`. It keeps
  every uncertain or completed cancellation result final.
