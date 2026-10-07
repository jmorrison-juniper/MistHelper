# Specification: ordered single-site firmware phases

- Issue: #4020
- Branch: `jmorrison-jnpr-feat-4020-ordered-single-site-firmware-p`
- Boundary: destructive. The change decides when firmware leaves the portal.

## Problem

The upgrade capture portal upgrades one site in four phases. The phase order is
`gateways`, `switches`, `aps`, `clients`. Every access point of a site reaches
the cloud through the switch of that site, and every switch reaches the cloud
through the gateway of that site.

Two defects broke that order.

1. The plan order followed the insertion order of the operator selection.
   `_group_targets` built one dictionary, and `plan_upgrade` read
   `groups.items()`. An operator who selected the access points first built the
   access point plan first.

2. The driver sent every plan before the first gate opened. `RunDriver.run`
   called `_submit(record)` and then `_cascade(record)`.
   `CloudUpgradeSubmitter.submit` sent every plan in one comprehension. The
   phase loop then only observed work that had already left the portal.

A gateway that failed to settle therefore could not hold the firmware of the
switches below it. The switches rebooted into a site with no path to the cloud,
and the operator lost the remote path to every device of that site.

### Measured proof of the defect

A mocked selection of one gateway group and one switch group, with the gateway
call refused, produced this answer against the code before this change.

```json
{"calls": ["gateways", "switches"], "result": true}
```

The switch firmware left the portal although the gateway above it took none.
The run also read as a success.

## Requirements

- FR-4020-01: `plan_upgrade` returns the plans in the order of
  `PLAN_FAMILY_ORDER`, which is `gateway`, `switch`, `ap`. The order of the
  operator selection never decides the order of the plans.
- FR-4020-02: The order inside one family is stable. Two version groups of one
  family keep the order that `_group_targets` built.
- FR-4020-03: The firmware of one family leaves the portal inside the phase of
  that family, immediately before that family settles.
- FR-4020-04: A family whose upstream family was lost takes no firmware. The
  record names that family `failed` with the sentence of `PHASE_BLOCKED_NOTE`.
  A family that the site does not hold reads `skipped` with no sentence.
- FR-4020-05: The portal never retries a destructive write by itself. A refused
  call ends the run, and an operator decides what the site does next.
- FR-4020-06: An accepted upgrade identifier survives a later failure. The stop
  path needs that identifier to cancel the firmware that is already moving.
- FR-4020-07: A phase that holds no plan sends no cloud call. The submitter
  answers with no reason, and the existing skip path marks the phase skipped.
- FR-4020-08: The client phase asks for no firmware, because a client is no
  device of this portal.
- FR-4020-09: A refused phase becomes `failed`, each later firmware family
  becomes terminal without a cloud call, and the run takes its post-check
  capture before it becomes `failed`.
- FR-4020-10: An empty, unknown, or mixed-family plan fails before the first
  cloud write. The terminal run record holds one plain validation sentence.
- FR-4020-11: Each accepted upgrade row becomes durable before the next plan of
  the phase leaves the portal. A durable stop request blocks the next plan and
  uses the normal `stopped` finalization path. The accepted-row write changes
  only the upgrade rows, so it cannot erase a stop that another worker stores.
- FR-4020-12: The stop write changes only the stop fields of the run record, so
  it cannot erase an accepted upgrade row, a state, a phase, or a post-check
  field that the driver stores at the same time.
- FR-4020-13: One run-scoped gate covers the stop check, the one firmware call,
  and the accepted-row write. A stop that claims the gate blocks each later
  firmware call of that run. A firmware call that holds the gate completes and
  records its evidence before the stop becomes durable.
- FR-4020-14: A stop that registers while a firmware dispatch asks for the run
  gate still wins. The dispatch takes the gate, reads the waiting-stop count
  again, gives the gate back, and sends no firmware call.
- FR-4020-15: A refused dispatch writes its refusal evidence inside the run
  gate through a narrow durable mutation, so a stop that commits at the same
  time cannot erase the refusal reason.
- FR-4020-16: The move of a run into the state `stopping` writes the state and
  the change time only. It reads the newest durable record first, and it
  reports the true state of a run that already reached a final state.
- FR-4020-17: A stopped run that captured no post-check writes the failure
  reason and the flag `post_check_captured` as `false` before it reaches the
  state `stopped`.
- FR-4020-18: The move of a run into the state `stopping` compares the state it
  read with the durable state before it writes. A driver that reached a final
  state at the same time keeps that state, and the route reports the newer
  state to the operator.
- FR-4020-19: A refused dispatch retries its evidence write a bounded number of
  times. If every attempt fails, the run receives a dispatch fence, the portal
  raises a visible error, and the run ends in the state `failed`. A fenced run
  starts no later firmware call, and the run gate still comes back.

## Owner decisions

The owner approved three decisions before the implementation started.

1. Use the limit of the existing `PhaseSettleGate`. Add no new timeout.
2. Use the existing phase anchor or the uptime proof for every required
   upstream device. An unknown state fails closed.
3. Never retry a destructive write automatically. Stop, persist the failure, and
   require an explicit operator resume. The resume itself is out of scope.

## Out of scope

- Issue #4021 and issue #4022.
- The destructive operation registry and the confirmation word.
- An operator resume path for a stopped run.
- A multiple-site run. This specification covers one site.

## Corrections to the issue body

The issue body holds four statements that the measurement did not support.

1. The `clients` phase has no firmware plan. It counts the clients of the site.
2. The zero-overlap statement is stale. Pull request #4075 also changed
   `upgrade/driver.py`.
3. The three owner decisions were not recorded at the time of the measurement.
4. The code proves the exposure to the defect. It does not prove one observed
   outage.

## Acceptance

- A mocked run reports `submitter.phases == ["gateways", "switches", "aps"]`.
- A mocked run with a lost gateway phase reports
  `submitter.phases == ["gateways"]`.
- A mocked submitter walk with a refused gateway group reports
  `calls == ["gateways"]`.
- The plans of a reversed selection read `gateway`, `switch`, `ap`.
- No test reaches the Mist cloud.
