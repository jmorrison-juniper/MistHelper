# Feature Specification: Keep a running multi-site job active

**Issue**: #3220
**Feature Branch**: `fix/3220-aggregate-running-states`
**Status**: Implemented
**Found by**: the journey harness of #3200

## Problem

The aggregate service kept the raw cloud word of each child, for example
`upgrading`. The service treats only `accepted`, `partial`, `running`, and
`read_unknown` as active. A normal in-progress word therefore caused three
faults:

1. `_can_read` refused the child, so the portal never read it again.
2. `_aggregate_state` returned `attention_required`.
3. `attention_required` counted as settled, so the first status refresh
   released every site lock during the write. The browser also stopped its
   poll on that state.

Warning: another operator could start a capture or a second upgrade at the
same sites while the devices wrote firmware.

## User Story (P1): A running job stays running

An operator starts a multi-site upgrade. The cloud reports `queued`, then
`downloading`, then `upgrading`, then `completed`.

**Acceptance scenarios**:

1. **Given** a child that reports any running word of the Mist enums, **When**
   the portal reads the status, **Then** the child state is `running` and the
   exact word stays visible.
2. **Given** a running child, **When** the next poll arrives, **Then** the
   portal reads the child again.
3. **Given** a child that is not past the write, **When** the portal refreshes
   the operation, **Then** every site lock stays held.
4. **Given** a cancel request, **When** a child still runs, **Then** every site
   lock stays held until each child reaches a final state.
5. **Given** an invalid status answer or an unknown word, **When** the portal
   reads the child, **Then** the child state is `read_unknown`, and the next
   poll reads it again.

## Requirements

- **FR-001**: The service MUST map `created`, `queued`, `downloading`,
  `downloaded`, `upgrading`, `inprogress`, `scheduled`, `starting`, `pending`,
  `in_progress`, `accepted`, and `running` to `running`.
- **FR-002**: The service MUST map `completed` and `success` to `completed`,
  and `failed` and `error` to `failed`.
- **FR-003**: The service MUST map an unknown word and an invalid answer to
  `read_unknown`.
- **FR-004**: The service MUST keep the exact cloud word in `cloud_status`.
- **FR-005**: The route MUST release the site locks only when every child is
  `completed`, `cancelled`, `failed`, `rejected`, or `not_submitted`.
- **FR-006**: The progress page MUST keep its poll for `attention_required`.
- **FR-007**: The progress table MUST show the state and, when it differs, the
  exact cloud word.

## Non-goals

- The change does not turn on the multi-site write gate (#3203).
- The change does not change the aggregate words for a mix of final states.
