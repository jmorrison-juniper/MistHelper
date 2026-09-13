# Contract: Compliance Analyzer Rule Set (Frozen)

**Feature**: Top-20 Compliance Violations Remediation
**Contract type**: Quality gate specification (not a runtime API)
**Source of truth**:
- `tools/compliance_analyzer/scoring.py` (scoring/grading logic)
- `tools/compliance_analyzer/models.py` (severity weights, grade thresholds, entities)
- `tools/compliance_analyzer/analyzers.py` (per-rule detectors)
- `tools/compliance_analyzer/engine.py` (orchestration and per-file report assembly)

**Status for this initiative**: **READ-ONLY**. FR-005 and SC-004 forbid any modification
to these files during the initiative. This document describes the contract every
remediation PR is scored against; the plan does not license anyone to change it.

## Scoring model (verbatim from `models.py` + `scoring.py`)

Every violation carries a severity, and the severity determines the penalty subtracted
from a perfect 100.0 score.

### Severity weights

| Severity   | Penalty per violation |
|------------|-----------------------|
| `CRITICAL` | 10                    |
| `HIGH`     | 6                     |
| `MEDIUM`   | 3                     |
| `LOW`      | 1                     |

### Category penalty cap

Any single **category** (e.g., "Architecture", "Complexity", "Comments") can contribute
at most **20 points** of penalty to the total. This prevents one bad area from tanking
the whole score alone and keeps grades comparable across files.

### Score formula

```text
per_category_penalty[c] = sum(severity_weight(v) for v in violations if v.category == c)
capped_penalty[c]       = min(per_category_penalty[c], 20)
score                   = max(0.0, 100.0 - sum(capped_penalty[c] for c in categories))
```

### Grade thresholds (worst -> best)

| Threshold | Grade |
|-----------|-------|
| >= 97.0   | A+    |
| >= 93.0   | A     |
| >= 90.0   | A-    |
| >= 87.0   | B+    |
| >= 83.0   | B     |
| >= 80.0   | B-    |
| >= 77.0   | C+    |
| >= 73.0   | C     |
| >= 70.0   | C-    |
| >= 67.0   | D+    |
| >= 63.0   | D     |
| >= 60.0   | D-    |
| >= 0.0    | F     |

### Contract bar for this initiative

- **Required post-refactor score**: `>= 95.0`
- **Required post-refactor grade**: `A+`
- **Practical implication**: post-refactor total capped penalty must be `<= 5.0` across
  all categories combined.

To land at 95.0, a file may retain at most **5 LOW violations** (5 * 1 = 5) OR **1
MEDIUM + 2 LOW** (3 + 2 = 5) OR similar low-severity slack. Any single MEDIUM plus a
single HIGH already costs 9 points (below the 95.0 bar). CRITICAL violations MUST be
zero; a single one costs 10 points (grade drops below A immediately).

## Rule categories (as emitted by `analyzers.py`)

Each violation carries a `rule_id` (stable identifier) and a `category` (human-readable
grouping). The primary rule families this campaign targets:

### Structural (`STRUCT-*`) - encodes the Five-Item Rule (Constitution I)

- `STRUCT-PARAMS`: function has more than 5 parameters. Fix: config object or split.
- `STRUCT-BLOCKS`: function body exceeds 5 logical blocks. Fix: extract helpers.
- `STRUCT-LINES`: function exceeds 25 lines. Fix: extract cohesive helpers.
- `STRUCT-DEPTH`: nested block depth exceeds project cap. Fix: early-return guards.

### Architecture (`ARCH-*`) - encodes Class-Based Architecture (Constitution II)

- `ARCH-DELEGATE`: standalone function that merely forwards to a class method. Fix:
  move the function to be a method on the class, update callers.
- `ARCH-WRAPPER`: thin wrapper preserved for backward compat. Fix: inline at callsite,
  remove the wrapper.

### Comments (`COMMENT-*`) - encodes Inline Comments (Constitution VI)

- `COMMENT-MISSING`: executable line lacks an inline comment. Fix: write a WHY
  comment explaining intent.
- `COMMENT-RESTATE`: comment merely restates the code. Fix: rewrite comment to
  explain purpose, not mechanics.

### Logging (`LOG-*`) - encodes Observability & Action Logging (Constitutions V, VII)

- `LOG-LAZY`: log call uses f-string / .format() instead of `%s` formatting. Fix:
  convert to lazy `%` form.
- `LOG-MISSING-BEFORE`: action lacks `logging.info` before it. Fix: add pre-action
  log.
- `LOG-MISSING-AFTER`: action lacks `logging.debug` after it. Fix: add post-action
  summary log.

### Safety (`SAFE-*`) - encodes Safety-First (Constitution III)

- `SAFE-INPUT`: `input()` call not wrapped in `safe_input()`. Fix: adopt
  `safe_input(prompt, context=...)`.
- `SAFE-DESTRUCTIVE`: destructive operation lacks typed confirmation. Fix: NASA/JPL
  pattern with `if confirmation != "UPGRADE": return`.
- `SAFE-PATH`: hard-coded `/` or `\\` separator. Fix: adopt `pathlib.Path` or
  `os.path.join`.

### Complexity (`COMPLEX-*`)

- `COMPLEX-CYCLO`: cyclomatic complexity exceeds cap. Fix: extract early returns,
  flatten nested conditionals, use dispatch tables.
- `COMPLEX-COGNITIVE`: cognitive complexity exceeds cap. Fix: same as cyclo but with
  extra weight on nesting depth.

## Frozen files

The following files are **read-only** for this initiative. Any diff that touches them
breaks the contract and blocks the PR:

- `tools/compliance_analyzer/__init__.py`
- `tools/compliance_analyzer/__main__.py`
- `tools/compliance_analyzer/analyzers.py`
- `tools/compliance_analyzer/engine.py`
- `tools/compliance_analyzer/models.py`
- `tools/compliance_analyzer/reporting.py`
- `tools/compliance_analyzer/scoring.py`
- `tools/check_compliance.py`
- Any `[tool.compliance*]` section in `pyproject.toml`
- Any `.compliance.yml`-equivalent config file

**Exception**: rank 18 in the campaign is `tools/codemod_logging_lazy.py`. This is a
codemod tool - it is NOT part of the analyzer package listed above. It IS a legitimate
refactor target. See `research.md` decision D-009 for its round-trip test requirement.

## Verification commands

```powershell
# Per-file analyzer invocation used by every PR.
python -m tools.compliance_analyzer <path>

# Repo-wide analyzer invocation used by SC-002 verification.
python -m tools.compliance_analyzer .

# Diff-wide grep for suppression markers (used by SC-003 verification).
git diff main -- . `
  | Select-String -Pattern "# noqa|# type: ignore|# pragma: no cover|# pylint: disable|# ruff: noqa|# mypy: ignore|# flake8: noqa|# nosec"
# Expected output: empty.

# Frozen-config verification (used by SC-004 verification).
git diff main -- tools/compliance_analyzer/ tools/check_compliance.py pyproject.toml
# Expected output: empty (no changes to any of these paths across the initiative).
```
