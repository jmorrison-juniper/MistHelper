# Implementation Plan: One canary phase rule for both modes

**Issue**: #3223 | **Spec**: [spec.md](spec.md)

## Design

1. Add `_PHASE_LOWEST = 1` beside `_PERCENTAGE_HIGHEST`.
2. Add `_check_phase_order(phases)`. It raises `BadOptionError("canary_phases")`
   when a phase is outside 1 to 100, when the list does not rise, or when the
   last phase is not 100.
3. Call it in `_read_canary`, right after `_read_number_list`.
4. State the rule in the `canary_phases` help text.

Both modes reach `_read_canary`: the single-site options route through
`build_options`, and the multi-site route through `_aggregate_saved_options`,
which calls `build_options` before it builds the plan.

## Constitution Check

- Validate early, return early: the rule runs before any plan exists.
- One rule, one place: `org_upgrade_body.py` keeps its own copy for the old
  AP-only body, which uses the same rule.

## Risks

- A stored run that already holds an invalid list keeps it. A retry of that run
  now refuses the list, which is the safe outcome.
