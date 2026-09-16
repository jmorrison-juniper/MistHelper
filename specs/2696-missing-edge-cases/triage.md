# Triage: Missing Edge Case Findings

## Measurement Summary

| Rule | Issue count from 2026-09-15 | Current pre-repair count | Current post-repair count | Delta from issue | Decision |
| - | - | - | - | - | - |
| `missing_ec_empty_input` | 75 | 76 | 0 | +1 before repair | Rule misfire. Repair the rule. |
| `missing_ec_negative_value` | 213 | 214 | 0 | +1 before repair | Rule misfire. Repair the rule. |
| `missing_ec_none_input` | 134 | 135 | 0 | +1 before repair | Rule misfire. Repair the rule. |
| `missing_ec_zero_value` | 158 | 158 | 0 | 0 before repair | Rule misfire. Repair the rule. |

## Triage Table

| Finding group | Current count | Classification | Evidence | Action |
| - | - | - | - | - |
| Empty input | 76 | Rule misfire | The detector inferred an empty-input obligation from a positive integer in the same file. A positive integer does not prove that the source under test accepts a collection. | Require `test-quality: edge-case-required=collection` before this rule emits. |
| Negative value | 214 | Rule misfire | The detector inferred a negative-value obligation from status codes, range bounds, mock calls, and fixture builders. Many of those values are categorical or test support data. | Require `test-quality: edge-case-required=numeric` and ignore support calls before this rule emits. |
| `None` input | 135 | Rule misfire | The detector inferred a `None` obligation without signature evidence that the parameter accepts `None`. | Require `test-quality: edge-case-required=none` before this rule emits. |
| Zero value | 158 | Rule misfire | The detector inferred a zero-value obligation from the same incidental integer patterns as the negative-value rule. | Require `test-quality: edge-case-required=numeric` and ignore support calls before this rule emits. |

## Cut Line

This pull request changes four analyzer and test files plus SpecKit and release-note files. It does not repair hundreds of tests, because the re-measurement shows one shared analyzer cause. No follow-up issue is needed for this rule family after the post-repair scan reports zero findings.

## Baseline Decision

No baseline file changed. The repair removes untrusted findings at the detector layer. It does not add or remove a committed baseline entry.
