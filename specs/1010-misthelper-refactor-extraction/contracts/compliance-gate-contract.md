# Contract: Compliance Gate

**Feature**: 1010-misthelper-refactor-extraction
**Producer**: `tools/compliance_analyzer/` (consumed as-is; not modified by this initiative)
**Consumer**: The extraction PR and CI branch protection
**Artifact**: Compliance grade per file and repo-wide aggregate; snapshot at `data/full_repo_compliance_current.md`

---

## The Two Non-Negotiables

Every extraction PR MUST satisfy BOTH:

1. **File gate**: The target module of the extraction MUST land at `A+/100`. (FR-012, SC-007.) `MistHelper.py`'s grade MUST NOT regress. Any file that was A+/100 pre-initiative MUST remain A+/100 post-extraction. (SC-005.)

2. **Baseline gate**: The repo-wide aggregate compliance score MUST remain at or above `99.6/A+` after the extraction. (FR-013, SC-004.) Sub-A file count MUST remain zero. (Baseline invariant from `data/full_repo_compliance_current.md`.)

Failure of EITHER gate blocks merge. Neither may be waived. `--admin` bypass MUST NOT be used to circumvent this contract (FR-011).

---

## Measurement Protocol

**Command**:

```bash
py -m tools.compliance_analyzer
```

**Cadence**:

- Locally before pushing the branch (Step 6 of `quickstart.md`).
- Automatically in CI as one of the 15 functional jobs.
- Optionally after merge to refresh `data/full_repo_compliance_current.md` (pattern seen in commits e50a524, da4ae90).

**Scope of measurement**:

- Per-file grade for every file in `src/`, `MistHelper.py`, and other tracked Python sources.
- Repo-wide aggregate as a weighted score (see `tools/compliance_analyzer/` for the exact formula; not modified here).

---

## Resolution Requirements

When the analyzer flags a candidate's extracted code with `guideline_flags` (per the refactor analyzer, not the compliance analyzer — they are separate tools with overlapping concerns), each flag MUST be resolved in the extraction PR before the compliance gate is evaluated. (FR-006, SC-012.)

The compliance analyzer measures conformance to:

- **Principle V** (Observability & Logging): ASCII-only logs, `safe_input()`, `pathlib.Path`.
- **Principle VI** (Inline Comments): every 5-10 lines. NON-NEGOTIABLE.
- **Principle VII** (Action Logging): before every non-trivial action. NON-NEGOTIABLE.
- Per-function LoC budget (`oversize_25_lines` flag correlate).
- Parameter-count budget (`too_many_params` flag correlate).
- Hardcoded-separator detection.

An A+/100 grade on the target module requires ZERO findings across these axes on the extracted code.

---

## Failure Modes and Responses

| Symptom | Interpretation | Response |
|---------|----------------|----------|
| New module scores < A+/100 | Extracted code has unresolved guideline debt | Fix in this PR; do NOT merge and defer |
| `MistHelper.py` regresses grade | Deletion diff exposed a latent comment-density gap or import churn | Fix in this PR; add comments as needed |
| A previously A+ file drops below A+ | Import churn or side effect from deletion | Investigate; likely a callsite-rewrite ripple; fix in this PR |
| Repo baseline drops below 99.6/A+ | Aggregate regression | Reject the PR; rework |
| Zero sub-A files invariant violated (a file drops to B or below) | Serious regression | Reject the PR; likely a deep issue with the extraction |

---

## Baseline Snapshot Update Protocol

`data/full_repo_compliance_current.md` is the canonical baseline snapshot. It may be updated in one of two ways during this initiative:

1. **Within an extraction PR**, when the extraction naturally improves the baseline (new A+ file added, existing files unaffected). The updated snapshot lands with the rest of the PR diff.
2. **Via a dedicated baseline-refresh commit** on `main` between extraction PRs (pattern in recent history: e50a524, da4ae90). These are separate from the 13 first-pass PRs and do not count against the FR-014 budget.

Snapshot updates MUST reflect a genuine analyzer run — never hand-edited.

---

## Interaction with the Refactor Analyzer

The compliance analyzer and the refactor analyzer are separate tools with overlapping vocabulary. The extraction workflow uses both:

- **Refactor analyzer** (`tools/refactor_analyzer/`): identifies WHAT to extract and WHERE it's called (`refactor_candidates.md`).
- **Compliance analyzer** (`tools/compliance_analyzer/`): grades HOW WELL the extracted code adheres to project non-negotiables (`data/full_repo_compliance_current.md`).

Both must be run at Step 6 of `quickstart.md`. Both must agree with the merge readiness of the PR:

- Refactor analyzer: candidate removed from its bucket.
- Compliance analyzer: target module A+/100, baseline preserved.

Neither is modified by this initiative (FR-018 for the refactor analyzer; analogous discipline for the compliance analyzer — it is treated as an infrastructure black box).

---

## Post-Initiative Verification (Aggregate, Not Per-PR)

At the end of the 13-PR first pass, the operator runs the compliance analyzer once more and verifies:

- Repo-wide score ≥ 99.6/A+ (SC-004).
- Zero A+ files regressed below A+ across the entire initiative (SC-005).
- Every new `src/refactors/*.py` file is A+/100 (SC-007).
- Zero sub-A files exist (baseline invariant).

These are cumulative outcomes; each is verifiable by diffing the initial and final `data/full_repo_compliance_current.md`. Any deviation is a spec-compliance failure and must be remediated before the initiative closes out.
