# Feature Specification: The multi-site options page offers each advanced control

**Issue**: #3383
**Feature Branch**: `feat/3383-multisite-advanced-controls`
**Status**: Draft
**Found by**: the parity review of the upgrade journey harness (issue #3200)

## Problem

The single-site options page offers eleven advanced upgrade controls that the
multi-site options page does not offer. An operator who plans one change for
many sites cannot set these controls. The operator must start one single-site
run for each site, or accept the cloud default of each control.

| Cloud field | The single-site control |
| - | - |
| `max_failures` | The failure count of each canary phase |
| `version` with the word `stable` | The vendor stable build |
| `enable_p2p` | The peer download of an access point |
| `p2p_cluster_size` | The size of one download group |
| `p2p_parallelism` | The count of download groups that run together |
| `rrm_first_batch_percentage` | The size of the first radio batch |
| `rrm_max_batch_percentage` | The size of each later radio batch |
| `rrm_node_order` | The order of the radio batches |
| `rrm_mesh_upgrade` | The order of the mesh access points |
| `rrm_slow_ramp` | The growth of each radio batch |
| `channel` | The release train of a session smart router |

## User Story 1 (P1): Set a failure count for each canary phase

**Acceptance scenarios**:

1. **Given** the canary strategy and the phases 10, 50, and 100, **When** the
   operator writes 1, 2, and 3 as the failure counts, **Then** the confirm page
   lists the counts, and each child job body carries `max_failures` [1, 2, 3].

2. **Given** the same phases, **When** the operator writes two counts,
   **Then** the save refuses the plan and names the control label.

3. **Given** a strategy other than canary, **When** the page shows, **Then**
   the failure count control stays hidden and posts no value.

## User Story 2 (P1): Let access points take the firmware from a neighbor

**Acceptance scenarios**:

1. **Given** the Access points box, **When** the operator chooses yes and
   writes a group size and a group count, **Then** the access point child body
   carries `enable_p2p` true and both sizes.

2. **Given** the no choice, **When** the page shows, **Then** the two size
   controls stay hidden and post no value.

3. **Given** no Access points box, **When** the page shows, **Then** the peer
   download controls stay hidden.

## User Story 3 (P1): Set the radio batches of the rrm strategy

**Acceptance scenarios**:

1. **Given** the Access points box and the rrm strategy, **When** the operator
   sets each of the five radio controls, **Then** the access point child body
   carries each value.

2. **Given** another strategy, **When** the page shows, **Then** the five radio
   controls stay hidden and post no value.

## User Story 4 (P2): Choose the vendor stable build for switches and gateways

**Acceptance scenarios**:

1. **Given** the Switches box or the Gateways box, **When** the operator
   chooses the stable build, **Then** each switch child and each gateway child
   carries the version `stable`, and the confirm page names the stable build.

2. **Given** the Access points box and the stable build, **When** the operator
   saves, **Then** the portal refuses the plan. The message names the control
   and tells the operator to clear the Access points box or to keep the typed
   versions.

## User Story 5 (P2): Choose the release train of a session smart router

**Acceptance scenarios**:

1. **Given** a selected site that holds a session smart router, **When** the
   operator opens the options page with the Gateways box, **Then** the release
   train control shows.

2. **Given** no selected site that holds a session smart router, **When** the
   page shows, **Then** the release train control is absent.

## User Story 6 (P1): A test keeps the two pages in step

**Acceptance scenarios**:

1. **Given** a new advanced control on the single-site page, **When** the
   contract suite runs, **Then** the parity test fails until the multi-site
   page offers the control or the name map records the reason.

## Functional requirements

- **FR-001**: The multi-site page offers each control of the table above.

- **FR-002**: The save gives each value to the single-site option mapper, so
  one reader validates each value in both modes.

- **FR-003**: Each control shows only when a selected device type reads it. A
  hidden control is disabled, so it posts no value.

- **FR-004**: A refusal names the label that the multi-site page shows.

- **FR-005**: The access point child body carries the peer download fields and
  the radio fields under the same rules as the single-site body.

- **FR-006**: The organization body check accepts the nine access point fields
  and refuses a value outside its rule.

- **FR-007**: The save refuses the stable build when the plan holds an access
  point.

- **FR-008**: The Back link and a retry show each earlier value again.

- **FR-009**: The confirm page lists each advanced control that the operator
  set and that at least one child request carries. The summary reads the
  stored body of each child, so the page never promises a field that the cloud
  does not get. A router child and the per-device call carry no failure count.

- **FR-010**: An empty control keeps the cloud default, and the plan of an
  operator who sets no advanced control does not change.

- **FR-011**: The legacy access point request, which names no device type,
  reads no advanced control.

## Out of scope

- The failure percentage control of the big bang strategy. Issue #3326 covers
  that control.

- The stable build for an access point of a multi-site plan. The organization
  schema names no stable word. A follow-up issue asks for a live check.

## Success criteria

- **SC-001**: The parity contract test fails on the old page and passes on the
  new page.

- **SC-002**: A browser journey sets each visible control, reads each value on
  the confirm page, and reads each value again after Back.

- **SC-003**: A plan with no advanced control produces the same child bodies as
  before the change.
