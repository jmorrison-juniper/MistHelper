# Contract: Baseline entry

## Scope

This contract covers one record in `.github/test-quality-baseline.json`. The analyzer writes the file. MistHelper reads it through the gate. This work changes `weak_zero_assertions` entries only.

## File

- The file holds one JSON array.
- The array holds one object for each accepted finding in the repository.
- The file uses two-space indentation, and each object lists its keys in alphabetical order.

## Object fields

| Field | Type | Required | Rule |
| - | - | - | - |
| `category` | string | yes | `weak_assertion` for every `weak_zero_assertions` entry. |
| `explanation` | string | yes | Starts with `Test function '` and ends with `' contains no assertions.` |
| `file_path` | string | yes | POSIX path relative to the repository root. Must exist on `main` for a live entry. |
| `heuristic` | boolean | yes | `false` for every `weak_zero_assertions` entry. |
| `line_number` | integer | yes | The 1-based line of the `def` line. Must match the current file for a live entry. |
| `related_source` | string | yes | Equal to `file_path`. |
| `remediation` | string | yes | `Add at least one assertion verifying observable behavior.` |
| `rule_id` | string | yes | `weak_zero_assertions` for this work. |
| `severity` | string | yes | `medium` for every `weak_zero_assertions` entry. |

## Key

The analyzer compares entries by the tuple `(category, rule_id, file_path, line_number, explanation)`. A change to `line_number` creates a new key.

## Write rules

1. Write the file only through the analyzer write command with the full-suite scope.
2. Do not edit a line number or an explanation by hand.
3. Remove an entry only when the analyzer reports no matching finding.
4. Keep every entry of another rule unchanged in a `weak_zero_assertions` pull request.
5. Keep the file parseable JSON. A parse failure stops the gate.

## Example

```json
{
  "category": "weak_assertion",
  "explanation": "Test function 'test_validate_token_writes_cache' contains no assertions.",
  "file_path": "mist-ops-platform/tests/unit/api/test_auth.py",
  "heuristic": false,
  "line_number": 114,
  "related_source": "mist-ops-platform/tests/unit/api/test_auth.py",
  "remediation": "Add at least one assertion verifying observable behavior.",
  "rule_id": "weak_zero_assertions",
  "severity": "medium"
}
```

The example entry describes a current entry in the baseline file. T004 decides whether it remains.
