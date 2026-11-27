# Data Model: Weak zero-assertion triage

## Entities

### BaselineEntry

One record in `.github/test-quality-baseline.json`. The analyzer writes each record.

| Field | Type | Meaning |
| - | - | - |
| `category` | string | Category of the rule. The `weak_zero_assertions` entries use `weak_assertion`. |
| `rule_id` | string | The rule. This work changes `weak_zero_assertions` only. |
| `file_path` | string | POSIX path relative to the repository root. |
| `line_number` | integer | The 1-based line of the test function definition. |
| `explanation` | string | The message. It names the test function in single quotes. |
| `severity` | string | `medium` for every `weak_zero_assertions` entry. |
| `heuristic` | boolean | `false` for the entries of this work. |
| `related_source` | string | The test file path, equal to `file_path`. |
| `remediation` | string | The message for the fix. |

**Natural key (current analyzer)**: `(category, rule_id, file_path, line_number, explanation)`. The line number is part of the key. An edit above a flagged test changes the key.

**Natural key (requested upstream)**: `(rule_id, file_path, function name)`. The function name does not change when code above it moves. T005 requests this key.

### Finding

One current analyzer result. It uses the same key as a BaselineEntry. The gate compares the set of findings with the set of baseline entries.

### Disposition

The class of one BaselineEntry. Each entry has exactly one class.

| Class | Test of the class | Owner |
| - | - | - |
| `stale-counted` | The body holds an assert statement, a strong mock call, or a `pytest.raises` block. | T004 |
| `stale-self-assert` | The class is a TestCase, and the body calls `self.assert*`. | T004 |
| `stale-missing-file` | The `file_path` is absent on `main`. | T004 |
| `gap-mock-call-count` | The body calls `assert_called_once()`, `assert_awaited()`, or `assert_called(args)`. | T005 |
| `gap-helper-assert` | The body calls a helper whose name starts with `assert`. The helper body holds the assertion. | T003, T005 |
| `gap-playwright-expect` | The body calls the Playwright `expect` function. | T005 |
| `zero-construct` | The body holds no assertion construct, and no helper with an assertion. | T006 to T015 |

Counts: `stale-counted` 284, `stale-self-assert` 17, `stale-missing-file` 12, `gap-mock-call-count` 99, `gap-helper-assert` 20, `gap-playwright-expect` 10, `zero-construct` 115.

### Slice

One domain group of test files. One slice equals one pull request.

| Field | Meaning |
| - | - |
| `id` | `R01` to `R10` |
| `files` | The test paths listed in `tasks.md` |
| `entries` | The count of zero-construct entries in the slice |
| `branch` | `test/2711-<slice-slug>` |
| `state` | open, in review, merged, or blocked |

Slice totals: R01 9, R02 7, R03 10, R04 12, R05 5, R06 6, R07 8, R08 14, R09 17, R10 27. The sum is 115.

### Repair

One repaired test function.

| Field | Meaning |
| - | - |
| `test` | `file_path::function name` |
| `assertion` | The behavior check that the repair adds |
| `control` | The in-memory mutation that breaks the guarded behavior |
| `control_result` | `fails-repaired-test` when the control fails the test. `passes-on-main` when the unmodified code passes. |

## State transitions

### BaselineEntry

- `present` to `stale` when the code change or the repair removes the finding.
- `stale` to `removed` when the write command runs on the full-suite scope.
- `present` to `shifted` when an edit above the function moves its line. The shifted entry looks new until it is re-keyed.
- `shifted` to `present` after the write command re-keys it.

### Finding

- `zero-construct` to `repaired` when a behavior assertion is added and the mutation control fails the test.
- `gap-*` to `resolved` only after the pinned devtools commit changes. The entry then becomes `stale`.

### Slice

- `open` to `in review` when the pull request opens with its gate output.
- `in review` to `merged` after the serial merge.
- `in review` to `blocked` when the changed-from gate reports a new finding that the slice cannot repair.

## Relationships

- One BaselineEntry belongs to one file.
- One file holds many BaselineEntries.
- One Slice holds one to three files in most cases. R10 holds one file.
- One Repair belongs to one BaselineEntry with the `zero-construct` class.

Not applicable: no database, no schema migration, and no persisted runtime state.
