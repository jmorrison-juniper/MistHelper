# Specification: Upgrade capture stored size measurement

## Problem
The upgrade capture store measures `stored_size_bytes` on every write. The current write path serializes the whole capture several times while the value settles.

## Objective
Reduce sequential CPU time for upgrade capture write size stamping. Keep the stored size byte identical to the current canonical JSON rule.

## Scope
This change covers `src\upgrade_portal\capture\store.py`. It covers `measure_size_bytes()`, `_stamp_size()`, `_capture_size_bytes()`, and `_edge_size_bytes()`.

## Non-goals
Do not add parallel execution. Do not call the Mist API. Do not change storage schema or public return types.

## Behavior contract
The stored size remains the byte count of the canonical JSON body. Fields whose names start with `_` stay outside the capture body size. The edge size still counts the four edge fields.

## Acceptance criteria
- Record a baseline before application code changes.
- Keep unit and contract tests passing.
- Add tests for size digit boundaries at 99, 100, 999, and 1000 bytes.
- Retain the change only if the measured gain clears the optimization policy.
