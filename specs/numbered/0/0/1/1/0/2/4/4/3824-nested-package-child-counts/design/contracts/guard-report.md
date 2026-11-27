# Interface Contract: Guard Report

The nested package guard prints one report line and raises one assertion for each failed rule. CI reads these messages as its failure evidence. Source: `tests/guardrails/test_nested_package_structure.py`, remote main, blob `5678277a376271483a6d340751e4c8ff7b5d92a3`.

## Report Line

The function `report_measurement` at line 157 prints this line:

`nested_package_scope: {examined} directories examined, {violations} violations, {excess} total excess`

The fields are the count of measured directories, the count of directories above five children, and the sum of the counts above five.

## Expected Line in the Test

The test `test_nested_package_ratchet_matches_main` at lines 169 to 179 requires this exact text after the examined count:

`33 violations, 236 total excess`

Each slice replaces these two values with the totals in `plan.md`. The examined count is not fixed in the test. It comes from `len(actual)` at line 175.

## Failure Messages

| Rule | Message form | Source line |
| - | - | - |
| Unknown violation | `Unknown violations: [paths]` | 136 to 139 |
| Stale baseline entry | `Stale baseline entries: [paths]` | 137 to 141 |
| Increased child count | `Increased child count: {path} {expected} -> {measured}` | 145 to 146 |
| Entry reached five | `Stale baseline entry reached five children: {path}` | 148 to 149 |
| Total excess increased | `Total excess increased: {baseline_excess} -> {actual_excess}` | 152 to 153 |

The assertion joins the messages with a newline at line 154.
