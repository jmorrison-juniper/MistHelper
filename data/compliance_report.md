# Coding Guideline Compliance Report

- **Generated**: 2026-06-28 11:53:13 UTC
- **Tool**: compliance-analyzer (tools/compliance_analyzer)
- **Files analyzed**: 1

Files are graded against the project guidelines: the 5-Item Rule, no
wrappers/delegators/aliases/shims, complexity limits, inline comments,
safe input handling, and portable file paths. Use the SpecKit Remediation
Plan at the end to drive fixes.

## Summary

- **Overall score**: 100.0 / 100
- **Overall grade**: A+

| File | Score | Grade | Critical | High | Medium | Low | Total |
| - | - | - | - | - | - | - | - |
| MistHelper.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |

## Machine-Readable Summary

```json
{
  "overall_score": 100.0,
  "overall_grade": "A+",
  "severity_totals": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "rule_totals": {},
  "files": [
    {
      "path": "MistHelper.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    }
  ]
}
```

## File: MistHelper.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 24271 |
| Executable code lines | 11278 |
| Functions | 1395 |
| Classes | 96 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 80.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _parse_requirement_line | 5 |
| _parse_requirements_file | 5 |
| _msp_resolve_name | 5 |
| _msp_parse_one_privilege | 5 |
| detect_msp_privileges | 5 |

No violations found. This file complies with the guidelines.

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

No remediation tasks: every analyzed file complies with the guidelines.

