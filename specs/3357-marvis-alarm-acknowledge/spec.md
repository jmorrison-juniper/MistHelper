# Feature Specification: Guarded Marvis Alarm Acknowledge

**Issue**: #3357

## Goal

After mode 3 verifies a Marvis Action resolve, let the operator acknowledge its
joined Marvis alarm. Keep this optional write off by default.

## Behavior

1. Search the Marvis alarms before mode 3 sends a resolve request.
2. Join alarms through `action_id`, then through `id`.
3. Include only actions whose verify read reports a closed status.
4. Require the exact text `ACKNOWLEDGE <count>`.
5. Send `ackOrgMultipleAlarms` with no more than 1,000 alarm IDs per request.
6. Put the resolve code and the operator comment in the alarm note.
7. Record the acknowledge result in each mode 3 result row.
8. Never call `ackOrgAllAlarms` or `unackOrgAllAlarms`.

## Safety

Warning: an acknowledge can hide an active fault from the unacknowledged alarm
view. The acknowledge changes the alarm state for every organization
administrator.

The alarm acknowledge control has a blank default. A blank or incorrect value
sends no acknowledge request.

## Acceptance Criteria

- [x] The step is off by default and needs a typed count.
- [x] Each request holds no more than 1,000 alarm IDs.
- [x] The result file records the acknowledge result for each eligible alarm.
- [x] The endpoint report names `ackOrgMultipleAlarms`.
- [x] Mocked tests prove the guard, the batch limit, and the result fields.
- [ ] A person reviews the change before merge.
- [ ] Every pull request quality gate passes.

## Live Test Boundary

No automated or agent-run test acknowledges a live alarm. A human can approve a
live test after review, but a live write is not required to prove the code
guards and request shape.
