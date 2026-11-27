# Data Model: Main workflow recovery

No database changes. The entities below describe the recovery records that the evidence queries read. Each entity has a natural key. This record adds no storage.

## Entities

| Entity | Natural key | Fields | Source |
| - | - | - | - |
| Pull request merge | Pull request number and merge commit | Merged by, merged at, merge commit, state | Pull request reads (RC-47, RC-55, RC-56 to RC-64) |
| Enable attempt | Run ID and pull request number | Run created at, enable result, dispatch result, logged result line | Run jobs and run logs (RC-53, RC-54, RC-56 to RC-63) |
| Main workflow | File name | Push trigger, dispatch trigger, path filter | Workflow files (RC-36 to RC-40) |
| Tip coverage | Tip commit and file name | Run ID, event, conclusion | Run list by head commit (RC-48, RC-50, RC-65) |

## State transitions: pull request

| From | Event | To | Recovery start | Evidence |
| - | - | - | - | - |
| Open, no request | Labeled run. Checks are green. The enable call merges the pull request. | Merged | Same run, dispatch job | Confirmed merge line (RC-56 to RC-63) |
| Open, no request | Labeled run. Checks are pending. The enable call is accepted. | Open with pending request | None | Pending line (RC-26). No dispatch. |
| Open with pending request | Checks pass and the merge happens later. | Merged | A closed run or a scheduled run (A-3) | Not observed in the survey (RC-68) |
| Open | Pull request closed without merge | Closed | None | The dispatch job needs a merged close (RC-29) |
| Merged by a person | Closed event | Merged | Closed run | RC-49, RC-64 |
| Merged | Schedule tick | Unchanged | Coverage check, then a start if a workflow is missing | RC-65, RC-67 |

## State transitions: tip coverage

| From | Event | To | Evidence |
| - | - | - | - |
| Missing | Coverage check finds no run on the tip after five checks | Started by dispatch call | Started line (RC-34) |
| Missing | Dispatch call fails | Failed. The job exits 1 after the merge. | Failure line (RC-34) |
| Covered | Coverage check finds one run on the tip, queued or complete | Unchanged | Covered line (RC-31, RC-34) |

## Constraints

- The job reads the tip once at the start and uses that commit for every check (RC-31).
- A queued run counts as coverage of the tip (RC-34, lines 335 to 336).
- A later tip does not prove coverage of an earlier merge (RC-31, the edge case in `spec.md`).
- A pull request that edits a workflow file has no confirmed merge through the token (RC-27).
