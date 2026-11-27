# Interface Contract: Ratchet Baseline

The file `tests/guardrails/nested_package_baseline.json` is the input of the nested package guard. The guard `tests/guardrails/test_nested_package_structure.py` reads it in `load_baseline` (line 35). Each slice changes this file, and no other tool reads it.

## Document Shape

```json
{
  "version": 1,
  "source_root": "src",
  "max_children": 5,
  "violations": [
    {"path": "src/example/directory", "child_count": 6, "remediation_issue": 3824}
  ]
}
```

## Rules the Guard Enforces

| Field | Rule | Guard lines |
| - | - | - |
| `version` | Must equal the integer 1. | 45 |
| `source_root` | Must equal the string `src`. | 45 |
| `max_children` | Must equal the integer 5. | 47 |
| `violations` | Must be a nonempty list. | 49 to 51 |
| Entry `path` | Must start with `src/`. Must not contain a backslash or a `..` segment. | 70 to 75 |
| Entry `child_count` | Must be an integer above 5. | 76 to 77 |
| Entry `remediation_issue` | Must be a positive integer. | 78 to 79 |
| Entry paths | Must be unique and sorted in ascending order. | 80 to 85 |

## Failure Message

When the guard cannot read the file, it raises an `AssertionError` with this form:

`Cannot read nested package baseline {path}: {detail}. Examined {examined_count} directories.`

The source of this form is `_baseline_error` at lines 28 to 32.

## Ratchet Meaning

The guard allows an entry to stay only while its count stays above five. An entry must not increase. An entry that reaches five or fewer must be removed. Total excess must not increase.
