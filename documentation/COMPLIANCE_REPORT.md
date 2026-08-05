# Coding Guideline Compliance Report

- **Generated**: 2026-08-05 21:45:14 UTC
- **Tool**: compliance-analyzer (tools/compliance_analyzer)
- **Files analyzed**: 1

Files are graded against the project guidelines: the 5-Item Rule, no
wrappers/delegators/aliases/shims, complexity limits, inline comments,
safe input handling, and portable file paths. Use the SpecKit Remediation
Plan at the end to drive fixes.

## Summary

- **Overall score**: 75.0 / 100
- **Overall grade**: C

| File | Score | Grade | Critical | High | Medium | Low | Total |
| - | - | - | - | - | - | - | - |
| MistHelper.py | 75.0 | C | 0 | 1 | 12 | 2 | 15 |

## Machine-Readable Summary

```json
{
  "overall_score": 75.0,
  "overall_grade": "C",
  "severity_totals": {
    "critical": 0,
    "high": 1,
    "medium": 12,
    "low": 2
  },
  "rule_totals": {
    "CONV-COMMENTS": 1,
    "STRUCT-COMPLEXITY": 2,
    "STRUCT-LENGTH": 11,
    "STRUCT-PARAMS": 1
  },
  "files": [
    {
      "path": "MistHelper.py",
      "score": 75.0,
      "grade": "C",
      "violations": 15
    }
  ]
}
```

## File: MistHelper.py

- **Score**: 75.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 6054 |
| Executable code lines | 2121 |
| Functions | 224 |
| Classes | 6 |
| Average complexity | 2.6 |
| Max complexity | 9 |
| Inline comment coverage | 79.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _preflight_verify_credentials | 9 |
| _establish_mist_session | 6 |
| _parse_requirement_line | 5 |
| _parse_requirements_file | 5 |
| _build_token_session_attempts | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 2729 | low | STRUCT-COMPLEXITY | _preflight_verify_credentials | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 5505 | low | STRUCT-COMPLEXITY | _establish_mist_session | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 7 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 79.9%; uncommented lines: 7, 12, 18, 56, 83, 84, 85, 101, 386, 389, 604, 607. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3199 | high | STRUCT-PARAMS | send | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 885 | medium | STRUCT-LENGTH | _get_latest_pypi_version | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2524 | medium | STRUCT-LENGTH | _attempt_interactive_login_with_rollback | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2598 | medium | STRUCT-LENGTH | _select_msp_and_org | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2729 | medium | STRUCT-LENGTH | _preflight_verify_credentials | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2764 | medium | STRUCT-LENGTH | _check_token_rate_limit | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 3188 | medium | STRUCT-LENGTH | _install_default_request_timeout | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 5254 | medium | STRUCT-LENGTH | _add_output_format_arguments | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 5283 | medium | STRUCT-LENGTH | _add_safety_arguments | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 5316 | medium | STRUCT-LENGTH | _add_interface_arguments | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 5360 | medium | STRUCT-LENGTH | _reject_unsupported_flag_variants | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 5505 | medium | STRUCT-LENGTH | _establish_mist_session | Function spans 37 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

### Phase: High (1 task(s))

- [ ] **CMP-001** `MistHelper.py:3199` - STRUCT-PARAMS (Structure)
  - Symbol: `send`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `send` in `MistHelper.py`.

### Phase: Medium (12 task(s))

- [ ] **CMP-002** `MistHelper.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 79.9%; uncommented lines: 7, 12, 18, 56, 83, 84, 85, 101, 386, 389, 604, 607.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `MistHelper.py`.
- [ ] **CMP-003** `MistHelper.py:885` - STRUCT-LENGTH (Structure)
  - Symbol: `_get_latest_pypi_version`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_get_latest_pypi_version` in `MistHelper.py`.
- [ ] **CMP-004** `MistHelper.py:2524` - STRUCT-LENGTH (Structure)
  - Symbol: `_attempt_interactive_login_with_rollback`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_attempt_interactive_login_with_rollback` in `MistHelper.py`.
- [ ] **CMP-005** `MistHelper.py:2598` - STRUCT-LENGTH (Structure)
  - Symbol: `_select_msp_and_org`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_select_msp_and_org` in `MistHelper.py`.
- [ ] **CMP-006** `MistHelper.py:2729` - STRUCT-LENGTH (Structure)
  - Symbol: `_preflight_verify_credentials`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_preflight_verify_credentials` in `MistHelper.py`.
- [ ] **CMP-007** `MistHelper.py:2764` - STRUCT-LENGTH (Structure)
  - Symbol: `_check_token_rate_limit`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_check_token_rate_limit` in `MistHelper.py`.
- [ ] **CMP-008** `MistHelper.py:3188` - STRUCT-LENGTH (Structure)
  - Symbol: `_install_default_request_timeout`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_install_default_request_timeout` in `MistHelper.py`.
- [ ] **CMP-009** `MistHelper.py:5254` - STRUCT-LENGTH (Structure)
  - Symbol: `_add_output_format_arguments`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_add_output_format_arguments` in `MistHelper.py`.
- [ ] **CMP-010** `MistHelper.py:5283` - STRUCT-LENGTH (Structure)
  - Symbol: `_add_safety_arguments`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_add_safety_arguments` in `MistHelper.py`.
- [ ] **CMP-011** `MistHelper.py:5316` - STRUCT-LENGTH (Structure)
  - Symbol: `_add_interface_arguments`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_add_interface_arguments` in `MistHelper.py`.
- [ ] **CMP-012** `MistHelper.py:5360` - STRUCT-LENGTH (Structure)
  - Symbol: `_reject_unsupported_flag_variants`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_reject_unsupported_flag_variants` in `MistHelper.py`.
- [ ] **CMP-013** `MistHelper.py:5505` - STRUCT-LENGTH (Structure)
  - Symbol: `_establish_mist_session`
  - Problem: Function spans 37 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_establish_mist_session` in `MistHelper.py`.

### Phase: Low (2 task(s))

- [ ] **CMP-014** `MistHelper.py:2729` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_preflight_verify_credentials`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_preflight_verify_credentials` in `MistHelper.py`.
- [ ] **CMP-015** `MistHelper.py:5505` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_establish_mist_session`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_establish_mist_session` in `MistHelper.py`.

