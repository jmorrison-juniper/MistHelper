# Coding Guideline Compliance Report

- **Generated**: 2026-07-05 13:46:10 UTC
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
| src\maps\_maps_matplotlib.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |

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
      "path": "src\\maps\\_maps_matplotlib.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    }
  ]
}
```

## File: src\maps\_maps_matplotlib.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 427 |
| Executable code lines | 210 |
| Functions | 31 |
| Classes | 5 |
| Average complexity | 2.0 |
| Max complexity | 4 |
| Inline comment coverage | 81.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _entries_for_map | 4 |
| _resolve_initial_site | 4 |
| _fetch_site_maps | 4 |
| _plot_devices | 3 |
| _device_to_marker | 3 |

No violations found. This file complies with the guidelines.

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

No remediation tasks: every analyzed file complies with the guidelines.

