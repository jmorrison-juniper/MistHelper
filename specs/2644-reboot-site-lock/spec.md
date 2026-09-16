# Feature Specification: Reboot Site Lock Safety

**Feature Branch**: `fix/2644-reboot-site-lock`

**Created**: 2026-09-16

**Status**: Draft

**Input**: GitHub issue #2644: "A long scheduled reboot outlives the site lock"

## User Scenarios & Testing

### User Story 1 - Refuse unsafe long schedules (Priority: P1)

An operator schedules a firmware reboot from the upgrade portal. The portal refuses a schedule that can outlive the site lock.

**Why this priority**: A run must not keep polling a site after another operator can take the site.

**Independent Test**: Unit tests build upgrade options with a span above the safe limit and verify a refusal.

**Acceptance Scenarios**:

1. **Given** a schedule longer than the safe site lock window, **When** the operator submits it, **Then** the portal refuses the field.
2. **Given** a schedule inside the safe site lock window, **When** the operator submits it, **Then** the portal keeps the schedule.

---

### User Story 2 - Stop polling before the scheduled reboot (Priority: P2)

An operator schedules a reboot in the future. The run waits without cloud polling until the reboot window starts.

**Why this priority**: A long wait spends cloud calls for no useful evidence before the device can return.

**Independent Test**: A phase gate test schedules a future reboot and verifies that no cloud poll occurs before the schedule.

**Acceptance Scenarios**:

1. **Given** a future reboot time, **When** the phase gate starts, **Then** it sleeps until the reboot window before the first cloud poll.
2. **Given** a future reboot time, **When** the gate reaches the reboot window, **Then** it uses the normal phase deadline.

---

### User Story 3 - Fail closed when the lock is lost (Priority: P1)

A running firmware workflow loses the site lock. The run stops before it reads or writes the site again.

**Why this priority**: Two operators must never upgrade one site at the same time.

**Independent Test**: A driver test uses a heartbeat that loses the lock and verifies that no phase gate or capture runs.

**Acceptance Scenarios**:

1. **Given** a heartbeat that reports a lost lock, **When** the driver reaches the next site action, **Then** the run fails.
2. **Given** a lost lock, **When** the run fails, **Then** the run record holds a clear lock loss message.

### Edge Cases

- If the process dies, the heartbeat stops and the Redis site lock expires on its normal TTL.
- If the lock store is unreachable for the retry window, the run fails closed and records the reason.
- If the browser submits an old one-year epoch value, the portal refuses it under the new ceiling.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST reject `start_time` and `reboot_at` spans that exceed the safe lock window.
- **FR-002**: The safe lock window MUST be less than or equal to the maximum site lock life.
- **FR-003**: The phase gate MUST make no cloud polling call before a future scheduled reboot window starts.
- **FR-004**: The run driver MUST fail before each site action when the heartbeat reports a lost lock.
- **FR-005**: The failure record MUST state that the site lock was lost.
- **FR-006**: A lost lock MUST NOT report success.
- **FR-007**: A lock MUST keep its expiry so a crashed process cannot hold a site forever.

### Key Entities

- **Site lock**: The Redis record that names the site, operator, token, and run.
- **Run record**: The durable record that holds the state, phase results, and lock loss report.
- **Scheduled reboot**: The epoch second or duration that delays a switch or gateway reboot.
- **Phase gate**: The polling loop that waits for one device family to return.

## Verified Measurements

| Value | Source | Measurement |
| - | - | - |
| Poll interval | `src\upgrade_portal\upgrade\gate.py` `POLL_INTERVAL_SECONDS` | 20 seconds |
| Calls for each round | `src\upgrade_portal\upgrade\phase_gate.py` `CALLS_PER_ROUND` | 2 |
| Longest accepted schedule before this change | `src\upgrade_portal\upgrade\options.py` `START_TIME_HORIZON_SECONDS` | 31536000 seconds |
| Longest site lock life | `src\upgrade_portal\runtime\lock.py` `MAX_LOCK_LIFE_SECONDS` | 43200 seconds |

The old maximum schedule produced 1576800 poll rounds and 3153600 cloud calls for one run.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A schedule above the safe lock window raises `BadOptionError`.
- **SC-002**: A scheduled wait uses zero cloud calls before the scheduled reboot time.
- **SC-003**: A lost lock fails the run before phase polling and before post-check capture.
- **SC-004**: The worst-case cloud call volume falls below 3153600 calls for the old one-year schedule.

## Assumptions

- The Redis site lock remains the authority for site ownership.
- A process death stops heartbeat renewal. The existing TTL then releases the site.
- Pull request #2720 may add the same reboot delay control to multi-site runs.
