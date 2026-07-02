# Coding Guideline Compliance Report

- **Generated**: 2026-07-02 10:29:08 UTC
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
| src\firmware\org_ap_upgrader.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |

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
      "path": "src\\firmware\\org_ap_upgrader.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    }
  ]
}
```

## File: src\firmware\org_ap_upgrader.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 2803 |
| Executable code lines | 1717 |
| Functions | 227 |
| Classes | 2 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 99.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _validate_msp_context | 5 |
| _try_msp_mode | 5 |
| _collect_msp_selection | 5 |
| _parse_dash_selection_range | 5 |
| _step4_fetch_available_firmware | 5 |

No violations found. This file complies with the guidelines.

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

No remediation tasks: every analyzed file complies with the guidelines.

