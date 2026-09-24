# Feature Specification: One canary phase rule for both modes

**Issue**: #3223
**Feature Branch**: `fix/3223-canary-phase-rule`
**Status**: Implemented
**Found by**: the journey harness of #3200

## Problem

The shared option mapper checked only that each canary phase was a whole
number. The single-site mode and the multi-site mode therefore accepted
`50,10`, `10,101`, `10,50`, and `0,100`, and sent them in the upgrade request.
The multi-site journey of #3200 started a job with `50,10`.

## User Story (P1): The portal refuses a phase list that does not rise to 100

**Acceptance scenarios**:

1. **Given** a phase list that falls, **When** the operator sends the options,
   **Then** the portal answers 400 and builds no plan.
2. **Given** a phase above 100 or a phase of 0, **When** the operator sends the
   options, **Then** the portal answers 400.
3. **Given** a list whose last phase is not 100, **When** the operator sends the
   options, **Then** the portal answers 400.
4. **Given** `1,10,50,100`, **When** the operator sends the options, **Then** the
   portal accepts it.

## Requirements

- **FR-001**: Each phase MUST be between 1 and 100.
- **FR-002**: Each phase MUST be higher than the phase before it.
- **FR-003**: The last phase MUST be 100.
- **FR-004**: The single-site help text MUST state the rule.
- **FR-005**: The rule MUST live in one place, `_read_canary` of
  `src/upgrade_portal/upgrade/options.py`, which both modes call.

## Non-goals

- The wording of the refusal message belongs to #3206.
