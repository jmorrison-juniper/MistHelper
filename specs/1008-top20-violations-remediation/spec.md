# Feature Specification: Top-20 Compliance Violations Remediation

**Feature Branch**: `1008-top20-violations-remediation`
**Created**: 2026-07-02
**Status**: Draft
**Input**: User description: "Bring the 20 files with the highest total compliance-violation counts (identified by `tools.compliance_analyzer`, per `compliance_report.md` regenerated 2026-07-02) to grade A+ / >=95.0 via real refactoring. One PR per file, sequential merges, no suppressions, no threshold relaxation, no functional regressions."

## User Scenarios & Testing *(mandatory)*

<!--
  Each user story below is a single-file remediation slice: it can be
  developed, tested, merged, and demonstrated independently of the other 19
  slices. Priorities (P1..P3) are assigned by remediation impact - files with
  the most violations are P1, mid-tier are P2, tail is P3. Any PR from any
  priority group produces an independently valuable improvement to the
  compliance score.
-->

### User Story 1 - Remediate the top-5 worst-graded files (Priority: P1)

As a maintainer of MistHelper, I need the five files carrying the largest violation debt (ranks 1-5, 445 violations combined) refactored to grade A+ so that the repository's dominant sources of technical-debt noise disappear from the compliance report and future contributors are not asked to imitate low-quality patterns from these files.

**Files in this slice** (rank / current grade+score / total violations / path):

1. F / 54.0 / 149 / `src/maps/maps_manager.py`
2. F / 57.0 / 96  / `src/maps/launcher/viewer_callbacks.py`
3. F / 54.0 / 68  / `src/capture/packet_capture.py`
4. F / 54.0 / 67  / `src/network/routing_utils.py`
5. F / 54.0 / 65  / `src/device/utility_commands.py`

**Why this priority**: These five files account for roughly 46% of the total violation count across the top-20 list. Fixing them yields the largest single-slice improvement to the repo-wide compliance score and removes the worst offenders from the "Files needing improvement" list surfaced by the analyzer.

**Independent Test**: Each of the five files, in isolation, can be re-analyzed with `python -m tools.compliance_analyzer <path>` after its PR merges. The slice is complete when all five files independently score >=95.0 / A+ and no other files regressed.

**Acceptance Scenarios**:

1. **Given** the current F-graded state of `src/maps/maps_manager.py`, **When** the file's remediation PR is merged, **Then** `python -m tools.compliance_analyzer src/maps/maps_manager.py` reports score >=95.0 and grade A+.
2. **Given** any of the five files, **When** its remediation PR is opened, **Then** the PR body includes the pre- and post-refactor analyzer output showing the score transition, and no `# noqa`, `# type: ignore`, `# pragma: no cover`, or `# pylint: disable` markers appear anywhere in the diff.
3. **Given** the five refactor PRs are merged sequentially, **When** the last one completes, **Then** external callers (import sites, downstream modules, tests) require no changes because every public function/method/class name, signature, and observable behavior is preserved.
4. **Given** any of the five refactor PRs, **When** required CI runs, **Then** all 234+ required checks pass on the first successful pipeline (retries permitted only for known-flaky infrastructure jobs, never to mask a genuine failure).

---

### User Story 2 - Remediate mid-tier F/D- files (Priority: P2)

As a maintainer, I need the next tier of high-debt files (ranks 6-13, ~299 violations combined) refactored so that the compliance dashboard's "worst files" list continues shrinking after the P1 slice lands and no F-graded file remains in the top-20.

**Files in this slice**:

6. F  / 55.0 / 53 / `src/ssid_consolidation/ssid_template_consolidation.py`
7. F  / 54.0 / 46 / `scripts/mist_ideas_analyzer.py`
8. D- / 62.0 / 39 / `tests/unit/test_arango_writer.py`
9. F  / 54.0 / 34 / `scripts/mist_ideas_distiller_v2.py`
10. D- / 62.0 / 32 / `src/gateway/wan2_variable.py`
11. D- / 62.0 / 29 / `src/audit/renderer.py`
12. D  / 66.0 / 29 / `src/site/site_config_manager.py`
13. D  / 64.0 / 28 / `starlink_dashboard.py`

**Why this priority**: This tier finishes off every remaining F grade in the top-20 and also clears the D- tier. It is second-priority because each file has lower absolute violation debt than the P1 five, but the aggregate improvement is still material.

**Independent Test**: Each file is verified individually via `python -m tools.compliance_analyzer <path>`. The slice succeeds when all eight files score >=95.0 / A+.

**Acceptance Scenarios**:

1. **Given** the current mid-tier grades, **When** each remediation PR merges, **Then** the target file scores >=95.0 / A+ on the analyzer.
2. **Given** the test file `tests/unit/test_arango_writer.py`, **When** it is refactored, **Then** the same test cases still execute (same test IDs) and the pytest exit status is 0 - refactoring may only reorganize/split test structure, not delete coverage.
3. **Given** the `starlink_dashboard.py` root-level script, **When** it is refactored, **Then** its CLI entry point (module `__main__` behavior) and any documented command-line flags behave identically.

---

### User Story 3 - Remediate tail D/C-graded files (Priority: P3)

As a maintainer, I need the remaining seven files in the top-20 (ranks 14-20) refactored so the top-20 list is fully resolved and every file on the "worst files" list has reached A+.

**Files in this slice**:

14. D / 65.0 / 26 / `src/analytics/zone_analyzer.py`
15. D / 64.0 / 26 / `src/inventory/csv_comparator.py`
16. D / 66.0 / 25 / `src/device/prompt_utils.py`
17. D / 65.0 / 25 / `src/gateway/template_config.py`
18. D- / 60.0 / 23 / `tools/codemod_logging_lazy.py`
19. D / 65.0 / 23 / `src/reports/e911_bssid.py`
20. C / 73.0 / 22 / `scripts/menu_regroup.py`

**Why this priority**: These files carry the smallest absolute violation debt of the twenty, so their remediation delivers the smallest per-file score bump; they are still in scope because the initiative's goal is to close out the entire top-20 list, not just the F/D- tier.

**Independent Test**: Each file is verified individually via `python -m tools.compliance_analyzer <path>`.

**Acceptance Scenarios**:

1. **Given** the current D/C grades, **When** each PR merges, **Then** the file scores >=95.0 / A+.
2. **Given** `tools/codemod_logging_lazy.py` is itself a codemod tool that transforms other files, **When** it is refactored, **Then** running it against a corpus of pre-refactor logging call sites produces byte-identical output to the pre-refactor version of the codemod (round-trip regression test).

---

### Edge Cases

- **A refactor cannot reach 95.0 without behavioral change.** If the analyzer's rules are structurally impossible to satisfy for a specific construct (for example, an unavoidably long generated data literal, or a public API surface whose signature is contractually fixed by upstream consumers), the remediation PR must document the specific rule and construct in the PR body and route to a human decision (defer the file, split the module, or accept a documented deviation) rather than adding a suppression or lowering thresholds.
- **A file gains new violations mid-initiative.** If someone lands unrelated changes on `main` that push new violations into an in-flight target file after this spec was written, the remediation PR for that file must still land it at >=95.0 / A+ against the state of `main` at the time the PR opens, not the state on 2026-07-02.
- **The compliance analyzer's rules change during the initiative.** If `tools/compliance_analyzer/` itself is updated between PRs (new checks added, or existing check thresholds tightened), each still-open PR must be re-verified against the newest analyzer version before it merges. Analyzer configuration is out of scope for this initiative and must not be relaxed.
- **A per-file PR fails required CI on a check unrelated to compliance.** The PR does not merge until the failure is diagnosed and either fixed in-PR (if the refactor caused it) or documented as a pre-existing flake with evidence (repeated runs, main-branch reproducibility). No CI check is skipped or marked non-required to unblock the PR.
- **A refactor accidentally regresses another file's score.** If verification of the target file passes but a repo-wide analyzer run shows another file dropped in grade, the PR does not merge until the collateral regression is understood and either reversed or included in the same PR with an explanation.
- **Sequential merge order stalls.** If a PR earlier in the queue is blocked (design review, external dependency), later PRs may proceed only if they have no code overlap with the blocked file; any overlap forces the later PR to wait or rebase.
- **A "refactor" would require a wrapper/delegator/alias/shim.** These are explicitly forbidden by the governing directive. If the natural fix reads as a wrapper, the underlying design must be refactored instead (extract the real work into a new home; update callers to hit the real home directly). Do not preserve the old symbol as a thin forwarder.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each of the 20 target files listed in this specification MUST, after its remediation PR merges to `main`, be reported by `python -m tools.compliance_analyzer <path>` as score >=95.0 with grade A+.
- **FR-002**: The initiative MUST produce exactly one pull request per target file (20 PRs total). No PR may modify more than one target file's compliance state, and no target file's remediation may be split across multiple PRs.
- **FR-003**: PRs MUST be merged sequentially into `main`. The next PR in the queue may not merge until the previous PR has been squash-merged and its required CI is green on `main`.
- **FR-004**: Each remediation PR MUST NOT introduce any of the following suppressions or ignore markers to any file it touches: `# noqa`, `# type: ignore`, `# pragma: no cover`, `# pylint: disable`, `# ruff: noqa`, `# mypy: ignore`, `# flake8: noqa`, or any equivalent linter/analyzer bypass.
- **FR-005**: Each remediation PR MUST NOT modify the compliance analyzer's thresholds, weights, rule set, or configuration. In particular, `tools/compliance_analyzer/scoring.py`, `tools/check_compliance.py`, and any related configuration files (`pyproject.toml` compliance sections, `.compliance.yml`-equivalents, etc.) are read-only for the duration of the initiative.
- **FR-006**: Each remediation PR MUST preserve the observable behavior of the target file: identical public API surface (module-level names, function/method/class signatures, exception types raised, return-value shapes), identical CLI behavior for entry-point scripts, and identical test outcomes for any tests that exercised the file pre-refactor.
- **FR-007**: Any callsite of the target file that was untouched by the refactor MUST remain byte-identical in the PR diff. Callsites that must change MUST change to invoke the new real destination directly - not a wrapper, delegator, alias, or shim in the old location.
- **FR-008**: The refactor MUST resolve the underlying violations flagged by the analyzer, not merely shuffle them: 5-Item Rule violations resolved by real decomposition; complexity violations resolved by extracting cohesive helpers with clear responsibilities; missing-comment violations resolved by writing genuine inline explanations of non-obvious logic (not restating what the code plainly does); safe-input-handling violations resolved by validating/normalizing at real trust boundaries; portable-file-path violations resolved by adopting `pathlib`/`os.path.join` in place of hard-coded separators.
- **FR-009**: Each remediation PR body MUST include (a) the pre-refactor analyzer output for the target file, (b) the post-refactor analyzer output for the target file, and (c) a short prose description of the structural change (which helpers were extracted, which module boundaries moved, etc.).
- **FR-010**: Each remediation PR MUST pass all 234+ required CI checks before merge. No required check may be marked optional, skipped, or bypassed to unblock a PR.
- **FR-011**: The initiative MUST NOT add new features, new user-facing capabilities, or new external dependencies to any of the 20 target files. It is a pure quality/compliance refactor.
- **FR-012**: The initiative MUST NOT introduce any CVEs or known-vulnerable dependency versions. Any dependency touched by the refactor MUST remain at or move to a version with no open CVEs.
- **FR-013**: The system MUST use the SpecKit workflow for this initiative: this specification (`/speckit.specify`) feeds `/speckit.plan`, which feeds `/speckit.tasks`, which feeds `/speckit.implement`.
- **FR-014**: The feature branch for this initiative MUST be named to reflect a "top20-violations-remediation" theme (this specification is filed under `specs/1008-top20-violations-remediation/`).
- **FR-015**: Files ranked 21 and lower by the compliance analyzer MUST NOT be modified as part of this initiative except when a callsite update inside such a file is strictly required by FR-007 (public API preservation) - and even then, the change MUST be limited to the minimum necessary lines and MUST NOT lower that file's compliance grade.

### Key Entities

- **Target file**: One of the twenty source files listed in the priority tables above, identified by its repo-relative path. Attributes tracked per file: current grade, current score, current violation breakdown (Critical/High/Medium/Low), post-refactor grade, post-refactor score.
- **Remediation PR**: A single pull request whose scope is exactly one target file's compliance remediation. Attributes: target file, pre-refactor analyzer output, post-refactor analyzer output, list of extracted helpers or moved symbols, required-CI status.
- **Compliance analyzer**: The tool at `tools/compliance_analyzer/` invoked as `python -m tools.compliance_analyzer <path>`. Read-only for this initiative; its configuration, thresholds, and rule set are frozen.
- **Compliance report**: `compliance_report.md` at the repo root, regenerated 2026-07-02, which supplies the authoritative ranking of the twenty target files by total violation count.
- **Violation category**: One of `Critical`, `High`, `Medium`, `Low` as emitted by the analyzer. All four categories must be resolved to reach A+; the initiative does not treat any category as optional.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 20 target files independently score >=95.0 with grade A+ when re-analyzed by `python -m tools.compliance_analyzer <path>` on `main` after their respective remediation PRs have merged.
- **SC-002**: The repository-wide compliance score, as reported by a full-repo run of the compliance analyzer, improves by at least 2.0 points from its 2026-07-02 baseline of 89.8/100 (B+), moving toward or into the A- band.
- **SC-003**: Zero suppressions of the forbidden kinds (`# noqa`, `# type: ignore`, `# pragma: no cover`, `# pylint: disable`, and equivalents in FR-004) are added anywhere in the repository by any of the 20 PRs. Verified by a diff-wide grep of every merged PR's changes.
- **SC-004**: Zero changes are made to the compliance analyzer configuration during the initiative. Verified by `git diff` of `tools/compliance_analyzer/scoring.py`, `tools/check_compliance.py`, and related config across the 2026-07-02 baseline commit and the initiative's final merge commit showing no lines changed.
- **SC-005**: All 20 remediation PRs merge to `main`, each with all 234+ required CI checks green on the merge commit. Verified by inspecting each PR's final CI run.
- **SC-006**: Zero new CVE-flagged dependencies are introduced. Verified by the repository's dependency-audit CI check passing on every merge and by no new advisories appearing in `pip-audit`/`safety`/equivalent tooling output.
- **SC-007**: Zero functional regressions are observed. Verified by (a) the full unit-test suite passing on `main` after each merge, (b) any integration-test suite that ran pre-initiative continuing to pass, and (c) no rollback PRs being filed against any of the 20 merges within 14 days of merge.
- **SC-008**: The "worst files" section of `compliance_report.md`, regenerated on `main` after the last remediation PR merges, contains none of the 20 target files.

## Assumptions

- The compliance analyzer at `tools/compliance_analyzer/` is stable and its scoring formula, rule set, and thresholds will not be intentionally changed during the initiative. If maintenance changes are unavoidable, in-flight PRs will be re-verified against the new version.
- The 2026-07-02 regeneration of `compliance_report.md` is accurate and reflects the true state of `main` on that date. The twenty file paths and their rankings are taken from that report verbatim.
- The 234+ required CI check count reflects the current required-checks configuration on the `main` branch protection rules. If additional required checks are added mid-initiative, remaining PRs must satisfy them; if any are removed, remaining PRs are held to the stricter (original) set.
- Squash-merge is the merge strategy for every PR in this initiative, matching the recent commit history on `main` where every merge appears as a single squash commit.
- Public API surface of each target file is defined as: every module-level name not prefixed with a single underscore, plus any single-underscore name explicitly documented or imported by another module. Private-by-convention names (single underscore, not imported elsewhere) may be renamed, moved, or removed as part of a refactor without violating FR-006.
- Test files in the list (`tests/unit/test_arango_writer.py`) are refactored by restructuring the test code itself - splitting large parametrizations, extracting fixtures, deleting genuinely redundant assertions - not by weakening the coverage. Test IDs and the set of scenarios exercised remain a superset of the pre-refactor set.
- Root-level scripts (`starlink_dashboard.py`) and `scripts/*.py` entrypoints are refactored by extracting their business logic into properly namespaced modules under `src/` and leaving a minimal `__main__`-only shim only if genuinely required by external tooling; if no external tooling calls them, they are moved wholesale.
- The initiative's PR queue is worked in priority order (P1 stories first, then P2, then P3) but PRs within a priority tier may be worked in any order and may run in parallel up to the point of merge, at which point sequential merge (FR-003) reasserts.
- No file in the top-20 list is subject to a concurrent, unrelated large refactor that would create irreconcilable merge conflicts. If one is discovered, that file's remediation is deferred within the initiative rather than forced through.
