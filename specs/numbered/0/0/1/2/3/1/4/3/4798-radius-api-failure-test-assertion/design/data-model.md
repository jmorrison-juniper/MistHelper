# Data Model: RADIUS API Failure Test Assertion

This change adds no table, file format, or stored record. The model below describes the analyzer data that the failure depends on.

## Test-Quality Finding

One result from the analyzer. The analyzer creates findings for each scanned test module.

| Field | Type | Value for the target test |
| - | - | - |
| `category` | text | `weak_assertion` |
| `rule_id` | text | `weak_zero_assertions` (research RC-18) |
| `severity` | text | `medium` |
| `file_path` | text | `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` |
| `line_number` | integer | 694 on `main`. 707 on fixture repair `1f4843c`. None after the assertion (research RC-02, RC-09, RC-08) |
| `explanation` | text | `Test function 'test_an_api_failure_is_contained' contains no assertions.` |
| `remediation` | text | `Add at least one assertion verifying observable behavior.` |
| `heuristic` | boolean | `false` |
| `related_source` | text | The test module path |

**Natural key**: The tuple `(category, rule_id, file_path, line_number, explanation)` identifies a finding (research RC-19). The analyzer excludes `severity` and `remediation` from the key. A change to either field does not create a new finding.

## Baseline Entry

One accepted finding in `.github/test-quality-baseline.json` (research RC-14, RC-16).

- The file holds a JSON array. Each element has the same fields as a finding.
- The natural key matches a finding by the five-tuple above.
- The file holds 733 entries in total (RC-16). Nine entries name the target module (RC-15).
- The baseline entry for the target test has `line_number` 694 (RC-14).

## Gate Result

The output of one run of the test-quality gate.

| Field | Meaning |
| - | - |
| `gate_scope` | The number of files that the run checked and the number of findings in those files |
| `new findings` | The number of current findings that match no baseline entry |
| `exit code` | 1 when the new-finding count is above zero. 0 otherwise (research RC-20) |

## State Transitions for the Target Finding

| Step | Commit | Target finding | Baseline match | Gate |
| - | - | - | - | - |
| 1 | `main` | Present at line 694 | Matches the entry at 694 | `0 new findings` |
| 2 | Fixture repair `1f4843c` | Present at line 707 | No match. The entry at 694 becomes removed | `1 new finding`, exit 1 |
| 3 | Assertion commit `843be63` | Absent | The entry at 694 has no current finding | `0 new findings`, exit 0 |

Step 2 explains the failure in issue #4798. Step 3 removes the failure without a baseline edit.

## Relationships

- Each finding belongs to one test module.
- Each baseline entry belongs to one test module.
- A finding matches a baseline entry only when the natural key matches exactly.
- A removed baseline entry does not fail the gate (research RC-20).
