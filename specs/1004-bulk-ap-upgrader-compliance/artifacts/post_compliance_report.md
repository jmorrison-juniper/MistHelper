# Coding Guideline Compliance Report

- **Generated**: 2026-07-02 05:38:31 UTC
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
| src\firmware\bulk_ap_upgrader.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |

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
      "path": "src\\firmware\\bulk_ap_upgrader.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    }
  ]
}
```

## File: src\firmware\bulk_ap_upgrader.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 2256 |
| Executable code lines | 1300 |
| Functions | 160 |
| Classes | 2 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 95.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _run_discovery_phase | 5 |
| _read_site_names_from_file | 5 |
| _partition_sites_by_name | 5 |
| _print_site_ap_breakdown | 5 |
| _index_stats_by_device_id | 5 |

No violations found. This file complies with the guidelines.

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

No remediation tasks: every analyzed file complies with the guidelines.

