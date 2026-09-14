# Feature Specification: Fail a scheduled pre-check with no targets

## Problem

Issue #2657 reports that a scheduled pre-check can pass when a job carries no target devices. The worker used `all(...)` on the check result list. Python returns `True` for an empty list. The safety gate therefore reported success when it did not evaluate a device.

## Scope

This repair changes only the Mist Ops Platform worker checks, worker task aggregation, tests, and the release note. It does not change `MistHelper.py`.

## Acceptance Criteria

1. If a scheduled pre-check carries no targets, the task reports `passed: false`.
2. If a scheduled pre-check carries no targets, the service returns one failed result that states no target was evaluated.
3. If the pre-check task receives no check results, it reports failure.
4. If one target passes, the scheduled pre-check reports success.
5. If one target fails, the scheduled pre-check reports failure.
6. If one target passes and one target fails, the scheduled pre-check reports failure.
7. If a target check raises an exception, the service returns a failed result.
8. If a target check returns `None`, the service returns a failed result.
9. If the inventory API returns 403, the service reports a permission error.
10. The pull request body lists the reviewed `all(...)` and `any(...)` sites.
