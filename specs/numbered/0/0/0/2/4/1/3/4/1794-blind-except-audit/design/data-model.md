# Data model: Blind except handler audit (issue 1794)

This model defines the records that the audit creates or updates. The records live in the slice pull request bodies, in `.github/blind-exception-handler-baseline.json`, and in the held commit list of `plan.md`. The audit creates no database table and no runtime data.

## Entities and natural keys

### HandlerSite

A `try` block whose `except` clause names `Exception` or `BaseException`.

| Field | Rule |
| - | - |
| Natural key | Repository path, enclosing symbol, and ordinal inside that symbol. Line numbers change during slices, so they do not form the key. |
| Source | Ruff BLE001 listing (Q-4) and the text search (Q-8). |
| Bound name used | Yes or no. A handler with an unused bound name counts as blind for the growth guard (RC-032). |
| State | Candidate, outcome set, applied, tested, merged, or removed. |

### OutcomeRow

One audited site inside one slice.

| Field | Rule |
| - | - |
| Natural key | Slice identifier and HandlerSite key. |
| Outcome | `delete`, `narrow`, or `keep` (FR-007). |
| Exception types after | Operational types only for `narrow`. Empty for `delete`. Never `TypeError`, `AttributeError`, `NameError`, or `AssertionError` (FR-010). |
| Log call | Error record for each continued handler (`contracts/log-record.md`). |
| Caller evidence | Required for `delete` and `narrow` (FR-009). |
| Test name | Required for each row (FR-021). |
| Reason | Required for `keep` (FR-012, FR-014). |

### Slice

One cluster of candidate sites from `plan.md`.

| Field | Rule |
| - | - |
| Natural key | Slice identifier, S01 to S23, plus S24 for the final gate. |
| Paths | Repository paths named in the slice row of `plan.md`. |
| Site count | At most 40 (FR-017). The count equals the number of OutcomeRow records. |
| Destructive path | Yes for S07, S10, S11, and S19. These slices need a human review and no `auto-merge` label. |
| Changelog fragment | One file under `changelog.d/` (FR-035). |
| State | Planned, open, rebased, gates passed, or merged. A failed check moves the slice back to open. |

### BaselineEntry

One row in `.github/blind-exception-handler-baseline.json`.

| Field | Rule |
| - | - |
| Natural key | Repository path. |
| Count | Positive integer. |
| Transition | The count falls with each slice (FR-019). The count never rises. |
| Removal | The final gate removes each entry at zero (T031). |

### HeldCommit

One local or remote commit that holds unmerged work.

| Field | Rule |
| - | - |
| Natural key | Full commit SHA. |
| Owner | Slice identifier, or none when a squash commit supersedes the commit. |
| State | Held, rebased, checked, replaced, or preserved. |
| Replacement | Squash commit on main, when the owning slice merges. |

The 16 held commits are RC-104, RC-106, and RC-112 to RC-125. Commits `c3d0f769` and `8a700b2b` have no owner, because squash commits RC-103 and RC-105 supersede them.

### Decision

One choice in `design/research.md`.

| Field | Rule |
| - | - |
| Natural key | Decision identifier, D-1 to D-14. |
| Fields | Alternatives, chosen option, reason, and risk. |
| Human flag | Always false (`human_decision_required`). |

## State transitions

### HandlerSite

1. Candidate: the site appears in the Q-4 output.
2. Outcome set: the implementer reads the site and its caller, then sets one outcome (FR-008).
3. Applied: the code change exists in the slice branch.
4. Tested: the propagation test, the redaction test, or both pass (FR-021).
5. Merged: the slice merges to main.
6. Removed: a delete outcome or a narrow outcome removes the broad handler from the code.

### Slice

1. Planned: the slice row exists in `plan.md`.
2. Open: the pull request exists. Its body contains one OutcomeRow for each site (FR-018).
3. Rebased: the branch contains current main (FR-020).
4. Gates passed: each gate in `design/quickstart.md` Q-6 passes.
5. Merged: the squash merge reaches main. The slice moves to the next row.

### BaselineEntry

1. Count N: the value in the baseline file before a slice.
2. Count M: the value after the slice, where M is less than N (FR-019).
3. Removed: the value is zero in the final gate. The final gate removes the entry (T031).

### HeldCommit

1. Held: the commit is not an ancestor of main (Q-17).
2. Rebased: the owning slice rebases the commit onto current main (FR-027).
3. Checked: the owning slice passes the checks for the files that the commit changes.
4. Replaced: a squash commit on main contains the change.
5. Preserved: the remote branch keeps the commit with a preservation note until step 4 occurs (FR-028, SC-011).
