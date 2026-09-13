# Implementation Plan: Top-20 Compliance Violations Remediation

**Branch**: `1008-top20-violations-remediation` | **Date**: 2026-07-02 | **Spec**: [specs/1008-top20-violations-remediation/spec.md](./spec.md)
**Input**: Feature specification from `specs/1008-top20-violations-remediation/spec.md`

## Summary

Twenty files currently drag the repo-wide compliance score to 89.8/100 (B+). This plan
sequences a **worst-first, one-PR-per-file refactor campaign** that lifts every one of the
twenty files to A+/>=95.0 without adding suppressions, without relaxing analyzer
thresholds, and without changing observable behavior.

The approach follows the exact pattern proven by PRs #578-#583 (`bulk_ap_upgrader`,
`firmware_manager`, `org_ap_upgrader`, `site_auto_upgrade`,
`export_org_license_async_claim_status`): analyzer-driven decomposition into small
cohesive helpers, inline WHY comments on every line, lazy `%` logging, no wrappers.

**Technical approach**: For each target file the executor (a) captures a baseline analyzer
report, (b) applies the class-of-fix template appropriate to the file's dominant violation
categories, (c) re-runs the analyzer until score >= 95.0, (d) opens a PR with pre/post
analyzer output pasted into the body, (e) waits for all 234+ required CI checks to go
green, (f) squash-merges, (g) then starts the next file. PRs run in rank order 1 -> 20 so
the largest-impact refactors land earliest.

## Technical Context

**Language/Version**: Python 3.13+ (per `Technology & Compatibility Constraints` in
`.specify/memory/constitution.md`)
**Primary Dependencies**: `mistapi` 0.59+, `structlog`, `pathlib`, stdlib only where
possible. No new external deps introduced by this initiative (FR-011, FR-012).
**Storage**: N/A - refactor initiative touches no data schemas.
**Testing**: `pytest` (unit + integration), `python -m tools.compliance_analyzer <path>`
(scoring gate), `ruff check`, `black --check`, `mypy --strict` where the file is under
strict.
**Target Platform**: Cross-platform (Windows 11 dev, Linux containers). File paths MUST
use `pathlib` / `os.path.join` per constitution.
**Project Type**: Single-project Python monorepo. All target files live under `src/`,
`scripts/`, `tools/`, `tests/`, or repo root.
**Performance Goals**: No performance regressions. Refactored functions must retain
call-site big-O and observable latency.
**Constraints**:
- No suppressions (`# noqa`, `# type: ignore`, `# pragma: no cover`, `# pylint: disable`,
  `# ruff: noqa`, `# mypy: ignore`, `# flake8: noqa`, `# nosec`).
- No analyzer threshold or configuration changes (`tools/compliance_analyzer/scoring.py`,
  `tools/compliance_analyzer/models.py`, and any pyproject compliance sections are
  read-only).
- No behavior changes: public API surface, CLI flags, exception types, return shapes
  preserved byte-for-byte at call sites.
- One PR per file, sequential squash-merge, worst-first (rank 1 -> rank 20).
**Scale/Scope**: 20 files, 20 PRs, ~16.5k LOC in the top-5 alone, ~30k LOC estimated
across all twenty. Repo total 554 analyzed files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.4.0 (2026-05-15). All seven
principles apply to every remediation PR:

| Principle | Applies? | How this plan complies |
|-----------|----------|------------------------|
| I. Five-Item Rule | YES | Decomposition into <=25-line, <=5-block, <=5-param helpers is the primary refactor lever. Analyzer's `STRUCT-*` rules encode the Five-Item Rule; passing the analyzer at A+ is passing the rule. |
| II. Class-Based Architecture (No Wrappers) | YES | Extracted logic goes into semantically named methods on existing or new classes, not standalone functions that forward to a class. FR-007 forbids leaving old symbols as thin forwarders; when a callsite must move, it moves to the real new home. |
| III. Safety-First | YES | Where refactored files handle interactive input, `safe_input()` wrapping and typed-confirmation patterns for destructive ops are preserved or added. No refactor removes an existing safety guard. |
| IV. Full Deployment Pipeline | YES | Each PR runs `python -m py_compile` locally, then relies on the 234+ CI checks to enforce the full pipeline. Squash-merge to `main` is the only merge strategy (matches recent history). |
| V. Observability & Logging | YES | ASCII-only log strings, structured levels, no secrets. Any log call touched during the refactor is converted to lazy `%` formatting (fixes `LOG-LAZY` violations). |
| VI. Inline Comments (NON-NEGOTIABLE) | YES | Every touched line gets a same-line WHY comment. Adjacent uncommented lines in touched blocks also receive comments (constitution VI explicit). Missing-comment violations are resolved by writing genuine intent explanations, never by restating code. |
| VII. Action Logging (NON-NEGOTIABLE) | YES | Every touched action gets `logging.info` before and `logging.debug` after. Existing under-logged blocks touched during refactor have logging added end-to-end. |

**Result**: PASS. No Constitution violations require justification. The initiative is
itself a Constitution-enforcement activity: the analyzer is a mechanized subset of the
constitution, and A+/>=95.0 is the operational proxy for full principle compliance.

*Re-evaluated post-Phase 1*: Design does not introduce complexity that violates any
principle. No entry required in the Complexity Tracking table.

## Project Structure

### Documentation (this feature)

```text
specs/1008-top20-violations-remediation/
├── plan.md              # This file (/speckit.plan output)
├── spec.md              # Feature specification (already exists)
├── research.md          # Phase 0 output - per-file refactor pattern research
├── data-model.md        # Phase 1 output - Target File / Remediation PR / Violation entities
├── quickstart.md        # Phase 1 output - how to execute one PR end-to-end
├── contracts/
│   ├── analyzer-rules.md   # The compliance analyzer's rule set (frozen for this initiative)
│   └── required-ci-checks.md  # The 234+ required CI checks each PR must pass
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created here)
```

### Source Code (repository root)

This initiative touches **only** existing files - no new module trees are created except
for helper modules extracted from files >500 LOC. The twenty target paths are exactly:

```text
# P1 (ranks 1-5, 445 violations combined) - worst-first, merged first
src/maps/maps_manager.py                        # rank 1: F/54.0/149  (7243 LOC)
src/maps/launcher/viewer_callbacks.py           # rank 2: F/57.0/96   (3221 LOC)
src/capture/packet_capture.py                   # rank 3: F/54.0/68   (2389 LOC)
src/network/routing_utils.py                    # rank 4: F/54.0/67   (1888 LOC)
src/device/utility_commands.py                  # rank 5: F/54.0/65   (1803 LOC)

# P2 (ranks 6-13, ~299 violations combined)
src/ssid_consolidation/ssid_template_consolidation.py   # rank 6:  F/55.0/53
scripts/mist_ideas_analyzer.py                          # rank 7:  F/54.0/46
tests/unit/test_arango_writer.py                        # rank 8:  D-/62.0/39
scripts/mist_ideas_distiller_v2.py                      # rank 9:  F/54.0/34
src/gateway/wan2_variable.py                            # rank 10: D-/62.0/32
src/audit/renderer.py                                   # rank 11: D-/62.0/29
src/site/site_config_manager.py                         # rank 12: D/66.0/29
starlink_dashboard.py                                   # rank 13: D/64.0/28

# P3 (ranks 14-20)
src/analytics/zone_analyzer.py                          # rank 14: D/65.0/26
src/inventory/csv_comparator.py                         # rank 15: D/64.0/26
src/device/prompt_utils.py                              # rank 16: D/66.0/25
src/gateway/template_config.py                          # rank 17: D/65.0/25
tools/codemod_logging_lazy.py                           # rank 18: D-/60.0/23
src/reports/e911_bssid.py                               # rank 19: D/65.0/23
scripts/menu_regroup.py                                 # rank 20: C/73.0/22
```

New helper modules (only when a target file exceeds ~500 LOC after decomposition) land in
the same package as the parent file. Example: `src/maps/maps_manager.py` (7243 LOC) is
expected to spawn siblings such as `src/maps/floorplan_operations.py`,
`src/maps/heatmap_orchestration.py`, etc., named for the real responsibility being
extracted - never `maps_manager_helpers.py` or similar generic dumping grounds.

**Structure Decision**: Keep the existing single-project layout. This is a
quality-refactor initiative, not a structural reorganization. New modules are added only
when a target file's post-refactor size still exceeds ~500 LOC, and only within the
existing package.

## Phased Execution Sequence

The initiative is executed strictly worst-first, one PR at a time.

### Ordering strategy

- **Rank 1 -> Rank 20** in order (P1 -> P2 -> P3, ties broken by absolute violation count
  descending).
- A PR does not start until the previous PR has squash-merged and CI is green on `main`.
- Within a priority tier, PRs may be *drafted* in parallel (analysis, exploration), but
  only one PR is *open for merge* at any time to keep the queue linear.
- Rationale: highest-impact files land first, which yields the largest repo-wide score
  improvement as early as possible (SC-002) and prevents late-initiative merge conflict
  cascades from stalled early PRs.

### Per-file refactor pattern

For every target file, apply the class-of-fix that the analyzer's per-severity breakdown
indicates. Prior top-file refactors (see `git log --oneline` PRs #578-#583) establish the
templates:

1. **Decompose long functions** (>25 LOC, >5 blocks, >5 params) into focused helpers on a
   semantically-named class. See `research.md` for the recipe used on
   `firmware_manager.py` and `bulk_ap_upgrader.py`.
2. **Reduce cyclomatic complexity** by extracting early-return guards and flattening
   nested conditionals. Deep `if/elif` chains become dictionary dispatch or a `match`
   statement when the ranges are enumerable.
3. **Add inline WHY comments** on every line of touched code. Adjacent uncommented lines
   in touched blocks also get comments (Constitution VI). Comments explain intent /
   context / non-obvious behavior, never restate the code.
4. **Replace f-string logging** with lazy `%` formatting (`logging.info("count=%d",
   count)` instead of `logging.info(f"count={count}")`). Fixes `LOG-LAZY` violations and
   Constitution VII conformance.
5. **Remove wrappers/delegators/aliases/shims**. When a callsite must move because the
   real work moved, update the callsite to hit the new home directly. Leaving a
   one-line forwarder violates FR-007 and Constitution II.
6. **Add action logging** (`logging.info` before, `logging.debug` after, `logging.error`
   with context on exception) around every meaningful action in a touched function.
7. **Split modules >500 LOC** when the file naturally partitions along responsibility
   lines. Split only if it does not create new wrappers; otherwise keep the file whole
   and rely on internal decomposition.

`research.md` documents the specific class-of-fix mix predicted per target file based on
the analyzer's violation breakdown.

### Verification protocol per PR

Every PR MUST follow this exact protocol before merge:

```powershell
# 1. Pre-refactor baseline (captured in PR body)
python -m tools.compliance_analyzer <path> > pre.txt

# 2. Refactor happens on branch refactor/compliance-<rank>-<slug>

# 3. Local gates
python -m py_compile <path>
ruff check <path>
black --check <path>
mypy --strict <path>  # only if the file is under strict mode
python -m tools.compliance_analyzer <path> > post.txt

# 4. Behavior verification
pytest tests/  # full suite - no regressions
# CLI files also get a manual smoke via `--help` and one representative invocation

# 5. PR body contains pre.txt AND post.txt AND a prose diff description

# 6. All 234+ required CI checks must go green before squash-merge
gh pr checks <pr>       # all "pass"
gh pr merge <pr> --squash
```

Post-refactor score MUST be >=95.0 (grade A+). Nothing merges below that bar.

### Branch naming

`refactor/compliance-<rank>-<slug>` where `<rank>` is the two-digit rank from the top-20
list and `<slug>` is the file's basename minus `.py`, kebab-cased.

Examples:
- `refactor/compliance-01-maps-manager`
- `refactor/compliance-02-viewer-callbacks`
- `refactor/compliance-13-starlink-dashboard`
- `refactor/compliance-20-menu-regroup`

### Commit / PR message format

Every squash-merge commit follows the exact pattern established by PRs #578-#583:

```
refactor: <file-slug> compliance <old-grade>/<old-score> -> A+/<new-score> (#<pr>)
```

Concrete examples visible in `git log`:
- `refactor: firmware_manager compliance F/51.0 -> A+/100.0 (#580)`
- `refactor: bulk_ap_upgrader compliance F/50.0 -> A+/100.0 (#579)`
- `refactor: site_auto_upgrade compliance D/63.0 -> A+/100.0 (#582)`

Deviations from this format break the searchability of the campaign in `git log` and are
not permitted.

### Rollback / failure handling

If a file cannot reach 95.0 without introducing a wrapper/delegator/alias/shim, or
without changing behavior:

1. **Do not add a suppression** to unblock the merge (FR-004, Constitution III).
2. **Do not lower the analyzer threshold** or reweight severities (FR-005, SC-004).
3. **Do not preserve the old symbol as a thin forwarder** (FR-007, Constitution II).
4. Instead: pause the PR, document the specific rule + construct in the PR body,
   escalate to the human maintainer, and either:
   - Defer that file within the initiative (accept it stays on the top-20 list).
   - Split the file into two PRs when a natural boundary exists (still one file's
     compliance state per PR).
   - Accept a documented deviation captured in `research.md` and the PR body.

The Edge Cases section of `spec.md` reserves this option; the plan does not pre-commit to
any workaround.

### Dependencies between files

Some target files import from other target files. When this occurs:

- If file B (later in the queue) imports a helper extracted during file A's refactor
  (earlier in the queue), sequential merge ensures B rebases on A's merge before B opens
  its PR. No conflict.
- If two target files import from *each other*, they are treated as a coupled pair;
  refactor them together only if the file that lands second inherits the first's
  helpers cleanly. `research.md` enumerates the known import-graph edges among the
  twenty files.

Sequential-only merges (FR-003) are the primary mitigation. No parallel merges are
permitted.

## Phase 0: Outline & Research

See `research.md` for:

1. Per-file predicted class-of-fix mix (derived from the current violation category
   breakdown in `compliance_report.md`).
2. Known-tricky patterns already surfaced by PRs #578-#583 that are likely to recur
   (e.g., `mistapi` session lifecycle in `firmware_manager`, event-loop tangles in
   Plotly callback files, threaded packet capture teardown).
3. Import-graph edges among the twenty target files.
4. Decisions captured for open unknowns:
   - Decision: worst-first rank order (versus alphabetical, versus category-clustered).
   - Decision: hard >=95.0 gate versus "best effort" (>=95.0 is contractually required
     by FR-001 and SC-001).
   - Decision: `pathlib` over `os.path.join` for new code (per Constitution Technology
     Constraints, both are allowed; `pathlib` preferred for new helpers).
   - Decision: split modules >500 LOC (yes, when a natural boundary exists and does not
     require a wrapper).

## Phase 1: Design & Contracts

### Data model

See `data-model.md`. Entities: `TargetFile`, `RemediationPR`, `Violation`, `AnalyzerRun`,
`RequiredCICheck`. No persistent storage - these are workflow entities materialized as
GitHub artifacts (PRs, CI runs) and repo artifacts (analyzer output).

### Contracts

This initiative's "external interface" is not a runtime API - it is the pair of
**quality gates** every PR must satisfy:

1. `contracts/analyzer-rules.md` documents the frozen rule set from
   `tools/compliance_analyzer/analyzers.py` + scoring model from
   `tools/compliance_analyzer/scoring.py` + models from
   `tools/compliance_analyzer/models.py`. This is the contract every PR is scored
   against; the initiative treats it as read-only.
2. `contracts/required-ci-checks.md` lists the 234+ required checks that must be green
   on the merge commit of every PR.

### Quickstart

See `quickstart.md` for the end-to-end sequence to execute one remediation PR - from
branch creation through squash-merge - reproduced from the pattern used in PRs
#578-#583.

### Agent context update

The plan reference between `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` markers
in `.github/copilot-instructions.md` is updated to point to this plan file
(`specs/1008-top20-violations-remediation/plan.md`).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| (none)    | (n/a)      | (n/a)                                |
