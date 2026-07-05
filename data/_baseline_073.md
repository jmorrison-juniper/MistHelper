# Coding Guideline Compliance Report

- **Generated**: 2026-07-05 15:56:00 UTC
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
| src\websocket\polling\result_combiner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |

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
      "path": "src\\websocket\\polling\\result_combiner.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    }
  ]
}
```

## File: src\websocket\polling\result_combiner.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 117 |
| Executable code lines | 77 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 3 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _emit_debug_trailer | 3 |
| _merge_segments | 3 |
| _absorb_raw_chunk | 3 |
| _absorb_extras | 3 |
| combine_segments | 2 |

No violations found. This file complies with the guidelines.

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

No remediation tasks: every analyzed file complies with the guidelines.

