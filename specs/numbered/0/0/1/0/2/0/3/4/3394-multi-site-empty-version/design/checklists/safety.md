# Checklist: Firmware Safety for Issue 3394

**Purpose**: Check that the change keeps firmware plans safe before the implementation starts.
**Created**: 2026-11-26
**Feature**: `spec.md` and `plan.md` in this folder

- [x] The refusal happens before the plan write (RC30) and before the browser session write (RC29).
- [x] The change adds no default target version. A default could upgrade a device that the operator did not choose.
- [x] A refused save keeps the operator in control. The form keeps each typed value (RC41, RC44).
- [x] The refusal names the device type, so the operator knows the next step (D-5).
- [x] The new log lines hold no device address and no secret (FR-012).
- [x] The change starts no firmware job. The existing submit path starts any job later, and that path does not change.
- [x] The change leaves the confirmation page and the submit route unchanged (Out of Scope).
- [x] The rollback steps restore the prior behavior, and the plan states the restored risk (plan, Rollback Steps).
- [x] A human reviews the pull request before merge (D-12). Explained: the label `needs-human-review` stays on the issue.
- [x] The browser flow runs in task T007. Explained: the run is pending, and analysis item U-2 records that no browser run occurred in this phase.
