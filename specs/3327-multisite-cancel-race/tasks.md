# Tasks: Block child submission after a multi-site cancel

**Issue**: #3327 | **Plan**: [plan.md](plan.md)

## Phase 1: Reproduce

- [x] Add the deterministic live-submission cancellation test.
- [x] Add the second-cancel regression test.
- [x] Run both tests against the old behavior and record both failures.

## Phase 2: Repair

- [x] Guard the parent and child submission claims with the cancellation marker.
- [x] Stop the child loop when the cancel wins the child claim.
- [x] Permit the limited second cancel after an unavailable result.

## Phase 3: Verify

- [x] Run the focused unit and regression tests.
- [x] Run the required static checks and type check.
- [x] Add the release-note fragment.
- [x] Run the relevant validation.
- [ ] Open the pull request and verify the required checks.
