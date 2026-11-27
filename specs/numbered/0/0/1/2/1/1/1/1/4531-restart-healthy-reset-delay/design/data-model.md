# Data Model: Restart State

This change adds no stored data. The session script keeps the restart state in shell variables for one session. The natural key of one launch is the session identifier and the launch number. The tests read the state through the output lines and the launch entries.

## Entities

| Entity | Variable | First value | Source |
| - | - | - | - |
| Failed-start count | `FAILED_STARTS` | 0 | `container/scripts/misthelper-session.sh` line 127 |
| Restart delay | `RESTART_DELAY` | `RESTART_DELAY_SECONDS`, default 2 | Lines 37 and 128 |
| Measured duration | `RUN_SECONDS` | Set after each launch | Line 141 |
| Attempt limit | `MAX_START_ATTEMPTS` | Default 5 | Line 26 |
| Healthy threshold | `MIN_HEALTHY_SECONDS` | Default 30 | Line 32 |
| Delay cap | `MAX_RESTART_DELAY_SECONDS` | Default 60 | Line 42 |

## State transitions

1. **Start a launch**: `RUN_START_SECONDS` takes the value of `SECONDS` (line 133). The session script prints its start message (line 131).
2. **Run the recorder**: The script stores the exit code of the recorder (line 139).
3. **Clean exit**: If the exit code is 0, the loop ends (lines 144 to 146). No restart follows.
4. **Measure the run**: `RUN_SECONDS` takes the difference of the two readings (line 141).
5. **Healthy run**: If `RUN_SECONDS` is at least `MIN_HEALTHY_SECONDS`, the script sets `FAILED_STARTS` to 0 and restores `RESTART_DELAY` (lines 150 to 152). This is the healthy reset.
6. **Count the failure**: The script adds 1 to `FAILED_STARTS` (lines 150 to 160).
7. **Attempt limit reached**: If `FAILED_STARTS` is at least `MAX_START_ATTEMPTS`, the script exits with code 1 (lines 158 to 161).
8. **Wait and grow the delay**: The script prints the attempt and the delay (line 164), sleeps for `RESTART_DELAY` (line 165), and doubles it (line 167). A value above `MAX_RESTART_DELAY_SECONDS` returns to the cap (lines 167 to 170).

## Invariants

- The restart delay never exceeds `MAX_RESTART_DELAY_SECONDS`.
- Each launch changes `FAILED_STARTS` by one, or resets it to 0 after a healthy run.
- A clean exit with code 0 ends the loop before any count change.
