# Data Model: Dash module isolation for map callback tests

## Dash entry

- **Natural key**: The string `dash` in `sys.modules`.
- **States**: LOADED (a module object), NONE (the entry holds None), ABSENT (no entry), and STUB (the synthetic module from `_build_dash_stub`).
- **Attributes**: The entry value and whether the key is present.

State transitions under the fixture-only design, for each test that uses the autouse fixture:

| From | Event | To | Restore rule |
| - | - | - | - |
| ABSENT | Fixture installs the stub | STUB | Fixture pops the key |
| LOADED | Fixture installs the stub | STUB | Fixture restores the same module object |
| NONE | Fixture installs the stub | STUB | Fixture restores None |
| STUB | Test ends (finally block) | the state before the install | Exact restore |

Transitions under the current design, on main, for the four slice files:

| From | Event | To | Result |
| - | - | - | - |
| LOADED or ABSENT | Module import installs the stub | STUB | The stub stays after collection |
| STUB | Fixture saves the stub | STUB | Restore keeps the stub, not the prior entry |

Invariants after the change:

- The entry after collection equals the entry before collection, for LOADED and ABSENT (FR-020, FR-021).
- The entry after each test equals the entry before that test (FR-003).

## Slice

- **Natural key**: The repository path of the test file.
- **Attributes**: Wave name, branch name, commit SHA, pull request number, and the number of baseline entries for the file.
- **States**: The slice moves through these states, in order.
  - merged: The slice is on main. Wave E1 reached this state through PR #4735.
  - pending: Waves A, B/C, D, and E2 on main.
  - implemented: A slice branch passes its tests.
  - verified: The local gates pass.
  - held: The owner hold is in force.
  - published: A pull request is open.

Allowed transitions: pending to implemented to verified to published to merged. Held sits between verified and published. Held never returns to pending, because the held candidate commit stays unchanged (FR-027).

## Held candidate commit

- **Natural key**: The commit SHA.
- **Attributes**: File path, file blob SHA, and the owner branch name. The branch name is unverified (U-5).
- **States**: held. The commit stays unchanged while the owner keeps the hold.

## Baseline finding

- **Natural key**: The five-tuple `(category, rule_id, file_path, line_number, explanation)` from the baseline analyzer (research row R28).
- **States**: current, stale, and new.
  - current: The finding appears in the scan.
  - stale: The baseline holds the finding, but the scan does not.
  - new: The scan holds the finding, but the baseline does not.
- **Transitions**: A fix moves a finding from current to stale. A stale entry is advisory only. An edit above a finding changes its line number, which moves the finding from current to new. A new finding fails the gate. This transition is the reason for D-4.
