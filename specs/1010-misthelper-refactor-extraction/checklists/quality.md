# Quality Checklist: MistHelper Refactor Extraction

**Purpose**: Validate requirements quality (completeness, clarity, consistency, measurability, coverage) for the refactor extraction feature. Unit tests for the English spec — NOT verification of implementation behavior.
**Created**: 2026-07-05
**Feature**: specs/1010-misthelper-refactor-extraction/
**Scope**: Complements checklists/requirements.md (spec-quality) with domain-specific quality gates for extraction mechanics, CI posture, and safety invariants.

## Destination File Compliance Targets

- [ ] CHK001 - Are the exact 13 first-pass extraction destinations enumerated by absolute path in the spec? [Completeness, Spec §FR-002]
- [ ] CHK002 - Is the A+/100.0 compliance target for every destination file stated in measurable terms (score threshold, letter grade)? [Measurability, Spec §FR-002]
- [ ] CHK003 - Are the tools and command invocation used to compute the compliance score for each destination documented? [Clarity, Spec §FR-002]
- [ ] CHK004 - Is the ordering/sequencing across the 13 destinations defined (which lands first, which last)? [Completeness, Gap]
- [ ] CHK005 - Are per-destination acceptance criteria distinguished from repo-wide compliance criteria? [Consistency]

## Wrapper-Shim Absence (FR-003)

- [ ] CHK006 - Is "wrapper shim" defined with concrete syntactic examples (e.g., `from src.X import Y as Z` re-exports in MistHelper.py)? [Clarity, Spec §FR-003]
- [ ] CHK007 - Are the grep/AST patterns that would detect a residual shim specified as an automated check? [Measurability, Spec §FR-003]
- [ ] CHK008 - Is the zero-shim invariant asserted for both directions (MistHelper.py re-exporting src.*, and src.* re-exporting MistHelper.*)? [Coverage]
- [ ] CHK009 - Are legitimate cross-module imports (non-shim) distinguished from prohibited re-export shims? [Ambiguity, Spec §FR-003]

## Callsite Rewrite Completeness (FR-006)

- [ ] CHK010 - Is "same PR" as the deadline for callsite rewrites unambiguously specified (no follow-up PR permitted)? [Clarity, Spec §FR-006]
- [ ] CHK011 - Are the discovery mechanics for finding all callsites of an extracted symbol documented (grep, LSP, analyzer)? [Completeness]
- [ ] CHK012 - Is dynamic/reflective reference handling addressed (getattr, importlib, string-based lookups)? [Coverage, Edge Case]
- [ ] CHK013 - Is test-file callsite rewriting included in the scope of FR-006? [Ambiguity, Spec §FR-006]

## Class-Body Landing (FR-005)

- [ ] CHK014 - Is "class-body landing" defined with a concrete before/after AST shape (method on class vs. module-level function taking `self`)? [Clarity, Spec §FR-005]
- [ ] CHK015 - Are `@classmethod`, `@staticmethod`, and `@property` decorators addressed in the landing rules? [Coverage, Edge Case]
- [ ] CHK016 - Is the treatment of methods that must cross class boundaries during extraction defined? [Gap]

## CI Gate Posture

- [ ] CHK017 - Is the count "15 functional jobs" verifiable against a specific ci.yml revision (SHA or path pin)? [Traceability]
- [ ] CHK018 - Is line 420 of ci.yml identified by content (job name/step), not just by line number, in case the file shifts? [Clarity]
- [ ] CHK019 - Is the SKIPPED-vs-FAILED distinction specified with the exact mergeStateStatus/check-conclusion values that count as passing? [Measurability, Spec §FR-011]
- [ ] CHK020 - Are the acceptable reasons for a job to appear SKIPPED enumerated (conditional predicates)? [Completeness]

## Compliance Regression Bounds

- [ ] CHK021 - Is the baseline 99.6/A+ captured with a source-of-truth artifact (analyzer output file, commit SHA)? [Traceability]
- [ ] CHK022 - Is the "0 sub-A files must remain 0" invariant stated as a hard gate, not an aspirational target? [Clarity]
- [ ] CHK023 - Is the tolerance for a temporary in-PR dip in compliance (if any) specified, or is monotonic non-regression required? [Ambiguity]
- [ ] CHK024 - Are the fields the CI compliance check reads (score, grade, sub-A count) named explicitly? [Completeness]

## No `--admin` Merge Bypass (FR-011)

- [ ] CHK025 - Is `mergeStateStatus` named as the authoritative signal, and `gh pr checks` display explicitly deprecated for gate evaluation? [Clarity, Spec §FR-011]
- [ ] CHK026 - Are the enumerated `mergeStateStatus` values that permit merge (e.g., CLEAN) and those that block it (e.g., BLOCKED, BEHIND) listed? [Completeness]
- [ ] CHK027 - Is the interaction between SKIPPED conditional jobs and `mergeStateStatus` documented (does SKIPPED still yield CLEAN)? [Coverage]

## SKIP_ALWAYS Immunity (FR-008)

- [ ] CHK028 - Is the `refactor_analyzer` SKIP_ALWAYS frozenset identified by absolute path and symbol name? [Traceability, Spec §FR-008]
- [ ] CHK029 - Is "never touch definitions" defined operationally (no move, no rename, no signature change, no decompose)? [Clarity]
- [ ] CHK030 - Is the process for proposing an addition/removal to SKIP_ALWAYS specified (or explicitly out of scope)? [Gap]

## Hot Bucket Immunity (FR-009)

- [ ] CHK031 - Is the "4+ references" threshold defined precisely (call-sites, imports, both; test files counted or excluded)? [Clarity, Spec §FR-009]
- [ ] CHK032 - Is the reference-counting tool and its exact command output field named? [Measurability]
- [ ] CHK033 - Are ties at the boundary (exactly 4 vs. 3 references) unambiguously classified? [Edge Case]

## Analyzer-First Cadence (FR-010, SC-011)

- [ ] CHK034 - Is "refresh between each PR" defined as pre-PR, post-merge, or both, with a specific command? [Clarity, Spec §FR-010]
- [ ] CHK035 - Is the `refactor_candidates.md` artifact required to be committed alongside code changes in each PR? [Completeness]
- [ ] CHK036 - Is stale-candidate detection (candidate list unchanged for N PRs) addressed? [Coverage, Gap]

## Decompose-While-Moving (FR-006)

- [ ] CHK037 - Is "guideline_flags" defined with the enumerated flag names the analyzer emits? [Clarity, Spec §FR-006]
- [ ] CHK038 - Is the prohibition on deferred decomposition ("fix during motion, not after") stated as a merge-blocking criterion? [Measurability]
- [ ] CHK039 - Are the acceptable decomposition patterns (extract helper, split responsibility, inline collapse) enumerated? [Completeness]

## ASCII-Only Logs / safe_input() / pathlib.Path (Constitution VI/VII)

- [ ] CHK040 - Is the ASCII-only constraint scoped (log strings only, or all string literals, or both)? [Clarity]
- [ ] CHK041 - Is `safe_input()` identified by absolute import path with the semantics that distinguish it from built-in `input()`? [Traceability]
- [ ] CHK042 - Is the `pathlib.Path` requirement stated as prohibition of `os.path`, or coexistence permitted? [Ambiguity]
- [ ] CHK043 - Are the linter/checker rules (or regex) that enforce these three constraints referenced? [Measurability]

## AddressComparisonCounters Special Case (FR-015)

- [ ] CHK044 - Is the destination `src/inventory/csv_comparator.py` named as the sole landing point, with any `src/refactors/*.py` explicitly prohibited? [Clarity, Spec §FR-015]
- [ ] CHK045 - Is the rationale for the special-case folding documented (why this class differs from the other 12)? [Completeness]
- [ ] CHK046 - Are other analogous "fold into existing module" candidates identified, or is this special case one-off? [Coverage]

## Serial PR Workflow (FR-013)

- [ ] CHK047 - Is "no cross-PR parallelism" defined operationally (single open PR, or single in-flight refactor across N open PRs)? [Ambiguity, Spec §FR-013]
- [ ] CHK048 - Is the "15/15 green before next dispatched" criterion tied to `mergeStateStatus=CLEAN` on the merged PR? [Consistency, Spec §FR-011]
- [ ] CHK049 - Is the dispatch trigger for the next PR named (human, script, hook) and is any automated dispatch documented? [Gap]
- [ ] CHK050 - Are hotfix / non-refactor PRs excluded from the serial constraint, or subject to it? [Coverage, Edge Case]

## Cross-Cutting

- [ ] CHK051 - Are all 18 functional requirements (FR-001..FR-018) traceable to at least one measurable acceptance criterion in the spec? [Traceability]
- [ ] CHK052 - Are terms "extraction", "motion", "landing", "decompose", "shim" defined in a shared glossary within the spec? [Clarity]
- [ ] CHK053 - Are rollback requirements defined for a partially-merged extraction PR whose follow-up CI later fails? [Recovery, Gap]
