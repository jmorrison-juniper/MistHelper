# Feature Specification: Test Quality Analysis Engine

**Feature Branch**: `1019-test-quality-analyzer`

**Created**: 2026-07-14

**Status**: Draft

**Input**: User description: "Test Quality Analysis Engine — a static + AST-based analyzer that programmatically audits this repo's Python test suite and produces a prioritized, machine-readable report of what's missing, what needs expanding, and what needs fixing."

## Clarifications

### Session 2026-07-14

- Q: Where should the engine's code live in the repo? → A: `tools/test_quality_analyzer/`
- Q: What format should the baseline file use (the file that pins pre-existing findings so newly-introduced weak tests fail CI but the pre-existing backlog does not block merges)? → A: **JSON matching the report schema (subset — findings array only, no run metadata).** The baseline is a JSON document whose top-level payload is the findings array from a full engine run, canonicalized (deterministically sorted, no run metadata like timestamps or commit SHAs). This eliminates a second parser, guarantees round-trip fidelity with the report, and keeps the baseline diff-friendly per finding. Run metadata (task id, capture timestamp, commit SHA) MUST NOT appear inside the baseline payload — that context lives in Git provenance and PR descriptions.
- Q: How should the analyzer be wired into CI? → A: **No CI gate initially — manual invocation only.** Ship the engine, ship the baseline, but do NOT wire it into any GitHub Actions workflow, pre-commit hook, or `pyproject.toml` quality gate as part of this initiative. The engine is invoked by the maintainer on demand to drive remediation work. Rationale: the engine's detection rules are heuristic (especially FR-006 edge-case heuristics) and their false-positive rate is unknown until the engine has been run against the real repo repeatedly. Gating on unproven rules would either force noisy PR failures or force the baseline to swallow the noise. A follow-up initiative will add CI gating after the engine's accuracy has been validated against multiple weeks of real repo evolution. FR-012's gate-mode exit codes remain in scope so the engine is *ready* for CI wiring, just not *wired* by this feature.
- Q: Where should the engine write its JSON report and Markdown summary on disk? → A: **`tools/test_quality_analyzer/output/`, git-ignored.** Default output paths are `tools/test_quality_analyzer/output/report.json` and `tools/test_quality_analyzer/output/summary.md`. The `output/` directory MUST be added to `.gitignore` so generated artifacts are not committed. Colocating output with the tool keeps all tool-owned filesystem state in one place, mirrors the pattern used elsewhere for repo-internal utilities, and avoids polluting a top-level `build/` directory that other tooling may want to own. CLI flags MAY override the default paths for ad-hoc use, but the defaults are the paths documented for maintainer workflows and follow-up CI wiring.
- Q: Where and in what format should the engine's configuration (rule toggles, severity map, exclusion predicates) live? → A: **`tools/test_quality_analyzer/config.toml`, committed to git.** Configuration is a single TOML file colocated with the tool with three top-level tables: `[rules]` (per-rule enable/disable booleans, keyed by rule id), `[severity]` (rule-id → `critical`/`high`/`medium`/`low` overrides), and `[exclusions]` (path globs plus the Mist-API predicate parameters from FR-002). The file is committed so tuning decisions are reviewable in Git. TOML was chosen over YAML (no extra dependency, deterministic key ordering, matches `pyproject.toml` idiom already used in this repo) and over `[tool.test_quality_analyzer]` inside `pyproject.toml` (keeps unrelated repo config out of the analyzer's blast radius when the analyzer's schema evolves). Defaults for every key MUST be documented in the file itself as comments so the committed config is self-describing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline audit of the current test suite (Priority: P1)

A maintainer runs the engine against the repo and receives a prioritized report of every test-quality problem in the suite: which source modules are untested, which tests contain weak assertions, which HTTP/SSH-touching modules lack failure-mode coverage, which tests are tautological (mock the very thing under test), and which functions with string/list/dict inputs lack edge-case exercises. The report is emitted as both a stable machine-readable JSON document and a human-readable Markdown summary grouped by risk priority. This first run establishes the truth about the current suite — the maintainer no longer has to trust the 90% line-coverage number in isolation.

**Why this priority**: The user does not currently trust the test suite. Without an authoritative, reproducible finding list, every subsequent improvement is guesswork. This story alone delivers value: even without CI integration or baselines, the report unblocks targeted remediation work.

**Independent Test**: Can be fully tested by invoking the engine's CLI against the current repo checkout, verifying that the JSON report is well-formed and that known-bad tests (documented in the golden test set below) appear in the output at the expected file:line locations with the expected categories.

**Acceptance Scenarios**:

1. **Given** a fresh checkout of the repo, **When** the maintainer runs the engine CLI with no arguments, **Then** a JSON report and a Markdown summary are produced within 60 seconds, both files are deterministically sorted, and the JSON validates against the tool's published schema.
2. **Given** the golden test set of known findings (untested `src/api/api_data_fetcher.py`, weak `assert_called()` at `tests/unit/ssh/test_shell_executor.py:110`, weak assertion at `tests/maps/test_viewer_callbacks_wave_b_c.py:526`, plus at least one representative each of tautological-test and missing-failure-mode findings), **When** the engine runs, **Then** every golden finding appears in the JSON report with the correct file, line, category, and severity.
3. **Given** a test file that imports `mistapi` at module scope OR whose subject-under-test resides in `src/api/`, **When** the engine analyzes it, **Then** the file is recorded in the report with status `skipped: mist_api_excluded` and is NOT flagged for weak-assertion, edge-case, or failure-mode issues.
4. **Given** the engine performs its analysis, **When** any phase runs, **Then** no network sockets are opened and no test modules are imported at runtime — analysis is purely AST + filesystem.

---

### User Story 2 - CI gate that blocks NEW weak tests without blocking the backlog (Priority: P2)

A contributor opens a pull request that adds a new test containing `assert result is not None` (a weak assertion). CI runs the engine, compares findings against a committed baseline file, and fails the build because a new finding was introduced. Meanwhile, the pre-existing weak-test backlog — already recorded in the baseline — does not block the PR. When the contributor fixes the assertion, CI passes. This mirrors the pattern already established in the repo by `.suppression-baseline.txt` and `.coverage-baseline.txt`, so the mental model is familiar.

**Why this priority**: Regression prevention is the second-most valuable outcome. Without a gate, the backlog identified in P1 will grow faster than it shrinks. This depends on P1 (must have findings to compare against), which is why it's P2.

**Independent Test**: Given a committed baseline and a synthetic PR-like diff that introduces exactly one new weak-assertion test, the engine's CLI must exit with code 1 and identify the specific new finding in its output. Reverting the diff must yield exit code 0.

**Acceptance Scenarios**:

1. **Given** a committed baseline file and a working tree with zero new findings vs the baseline, **When** the engine runs in gate mode, **Then** exit code is 0 and the output states "no new findings vs baseline".
2. **Given** a committed baseline and a working tree that introduces one new weak-assertion finding, **When** the engine runs in gate mode, **Then** exit code is 1 and the new finding is listed distinctly from any pre-existing baseline findings.
3. **Given** the engine cannot parse a test file (syntax error), **When** it runs in gate mode, **Then** exit code is 2 (engine error), the failing file is reported with the parse error, and the run does not silently pass.
4. **Given** the baseline is stale (contains entries for files that no longer exist), **When** the engine runs, **Then** stale entries are reported as advisories and the operator is offered a mechanism to prune them without failing the gate.

---

### User Story 3 - Meta-tested engine that itself does not regress (Priority: P3)

A maintainer changing the engine's rules must be confident that they haven't broken the engine's own accuracy. The engine ships with a fixture-based meta-test suite: a directory of synthetic "bad test" files (each demonstrating exactly one finding category) that the engine must classify correctly, plus a directory of synthetic "good test" files that must yield zero findings. Any change to a detection rule surfaces immediately as a fixture regression.

**Why this priority**: This is a durability property. Without it, the engine drifts and its output becomes untrusted — replaying the problem the engine was built to solve, one level up. It is P3 because P1 and P2 can be delivered first with a smaller meta-test, and the fixture library can grow over time.

**Independent Test**: Given the shipped fixture directories, the engine's meta-test suite runs standalone (independent of the main repo) and produces exit code 0 when every bad fixture is caught and every good fixture is silent.

**Acceptance Scenarios**:

1. **Given** the bad-fixture directory containing at least one file per detection category (untested, weak-assertion, missing-failure-mode, missing-edge-case, tautological), **When** the meta-test suite runs, **Then** every fixture file yields the exact category, severity, and file:line the fixture claims.
2. **Given** the good-fixture directory of tests known to be well-formed, **When** the meta-test suite runs, **Then** zero findings are produced. Any false positive is a meta-test failure.
3. **Given** a maintainer disables a detection rule via configuration, **When** the meta-test suite runs, **Then** only fixtures for that rule change status; all other rules remain green.

---

### Edge Cases

- What happens when a test file has been deleted but still appears in the baseline? Report as a stale-baseline advisory; do not fail the gate; offer a documented prune path.
- What happens when a test file cannot be AST-parsed (syntax error)? Emit an engine-error finding with exit code 2; never silently skip.
- What happens when a source module lives at `src/api/...` (excluded surface) but its logic is exercised indirectly through a non-`src/api/` wrapper module? The wrapper's tests are analyzed normally; the `src/api/` module is skipped and marked `mist_api_excluded`. The engine does not attempt to reason about transitive exercise.
- What happens when a test contains both a weak assertion and a strong assertion? The test is flagged for the weak assertion but severity is downgraded because at least one strong assertion exists on the same code path.
- What happens if `coverage.py` output is not present? The engine still runs; it degrades gracefully with a note that coverage-informed heuristics are disabled.
- What happens with parametrized tests (`@pytest.mark.parametrize`)? Each parameter set is treated as an independent test for edge-case analysis; a parametrized test that already covers empty/None/oversized values is credited accordingly.
- What happens if the engine is run against a subdirectory (e.g., `tests/unit/ssh/`)? Analysis is scoped to that subdirectory; the baseline comparison is scoped identically to avoid spurious "missing" findings.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The engine MUST discover all Python test files under a configurable set of test roots (default: `tests/`) and classify each file as `analyzed` or `skipped: mist_api_excluded` before running any detection rule.
- **FR-002**: The Mist-API exclusion rule MUST be applied to any test file where EITHER (a) `mistapi` is imported at module scope, OR (b) the primary subject-under-test (inferred from imports of `src.*` modules) resides under `src/api/`. The rule MUST be configurable so future scope changes do not require code edits.
- **FR-003**: The engine MUST detect and report untested public source modules and functions — defined as any function whose name does not start with `_`, declared in a `src/*.py` file, for which no analyzed test file imports the containing module and references the function name.
- **FR-004**: The engine MUST detect weak assertions, at minimum: bare `assert result` / `assert x` on non-boolean expressions; `assert x is not None`; `mock.assert_called()` with no argument check; `pytest.raises(Exception)` (over-broad base type); test functions containing zero assertions; test functions whose only assertion inspects a value returned by a mock configured in the same test.
- **FR-005**: The engine MUST detect missing failure-mode coverage for source modules that make HTTP calls (`requests.*`, `httpx.*`, `urllib.*`) or SSH/socket calls, verifying that at least one analyzed test exists for each of: connection timeout, connection error, HTTP 4xx (401 OR 403 OR 404), HTTP 5xx, malformed JSON response, and empty response body.
- **FR-006**: The engine MUST detect missing edge-case coverage for public functions whose signatures accept `str`, `list`, `dict`, or `Optional[...]` parameters, checking whether analyzed tests exercise: empty value (`""`, `[]`, `{}`), `None`, oversized value, and Unicode/control-character values. Findings in this category MUST be tagged as heuristic so false-positive tolerance is explicit.
- **FR-007**: The engine MUST detect tautological tests — tests that configure a mock (e.g., `foo.bar = Mock(return_value=X)`) and then assert against that same mock's return value (`assert foo.bar() == X`) as the sole verification.
- **FR-008**: Every finding MUST include: absolute repo-relative file path, 1-based line number, category identifier, severity (see FR-009), a short human explanation (one to two sentences), and a suggested remediation (one sentence).
- **FR-009**: The engine MUST assign a severity to every finding using the taxonomy: `critical`, `high`, `medium`, `low`. Rule-to-severity mapping MUST be configurable; defaults MUST be documented alongside the tool.
- **FR-010**: The engine MUST emit two output artifacts per run: a JSON report suitable for CI diffing, and a Markdown summary grouped by severity descending. Both MUST be deterministically ordered so byte-identical inputs produce byte-identical outputs. Default output paths are `tools/test_quality_analyzer/output/report.json` and `tools/test_quality_analyzer/output/summary.md` (see Clarifications Q4). The `tools/test_quality_analyzer/output/` directory MUST be listed in `.gitignore`. CLI flags MAY override the default paths.
- **FR-011**: The engine MUST publish a JSON schema for its report format in the same directory as the tool, and every JSON run MUST validate against that schema.
- **FR-012**: The engine MUST support a committed baseline file whose on-disk format is **JSON matching the report schema (findings array only, no run metadata)** — the same shape used for the JSON report per FR-010, canonicalized (deterministically sorted, no timestamps or commit SHAs embedded). When run in gate mode against a baseline, exit code MUST be 0 if no new findings vs baseline, 1 if new findings exist, and 2 if the engine itself errored (parse failure, IO error, invalid config).
- **FR-013**: The engine MUST provide a CLI entry point invokable both locally by developers and inside CI. The CLI MUST accept flags to select test roots, override the exclusion rule, point at an alternate baseline path, and toggle output format.
- **FR-014**: The engine MUST NOT open any network sockets and MUST NOT `import` any test module at runtime. All analysis MUST be pure AST + filesystem.
- **FR-015**: The engine MUST complete a full analysis of the current repo (~190 test files) in under 60 seconds on a developer laptop.
- **FR-016**: The engine MUST ship with a golden test set derived from the manual audit — at minimum: `src/api/api_data_fetcher.py` classified as untested, `tests/unit/ssh/test_shell_executor.py:110` flagged weak-assertion, `tests/maps/test_viewer_callbacks_wave_b_c.py:526` flagged weak-assertion. These findings act as regression tests for the engine's accuracy on the real repo.
- **FR-017**: The engine MUST ship with meta-tests using synthetic fixtures — one bad-fixture file per detection category and one good-fixture file per category — such that fixture regressions surface immediately when detection rules change.
- **FR-018**: When the engine encounters a test file it cannot AST-parse, it MUST emit a distinct `parse_error` finding rather than silently omitting the file, and MUST cause exit code 2 in gate mode.
- **FR-019**: The engine MUST handle stale baseline entries (entries referencing files that no longer exist) by emitting a `stale_baseline` advisory without failing the gate, and MUST provide a documented mechanism to prune them.
- **FR-020**: The engine MUST live under `tools/test_quality_analyzer/` so it sits alongside the other repo-internal utilities and does not clutter `src/`.
- **FR-021**: The engine's configuration MUST live at `tools/test_quality_analyzer/config.toml`, committed to git, with three top-level tables: `[rules]` (per-rule enable/disable booleans), `[severity]` (rule-id → severity overrides constrained to the FR-009 taxonomy), and `[exclusions]` (path globs plus Mist-API predicate parameters from FR-002). Every key MUST have a documented default so the committed config is self-describing. The engine MUST fail-fast with exit code 2 if the config file is malformed or references an unknown rule id.

### Key Entities *(include if feature involves data)*

- **Finding**: A single detected quality issue. Attributes: category, severity, file path, line number, explanation, suggested remediation, optional heuristic flag, optional related-source reference. Findings are the atomic unit of the JSON report and the row unit of the Markdown summary.
- **Baseline**: An immutable-until-explicitly-updated snapshot of findings that pre-existed at a chosen point in time. Used by gate mode to distinguish "old backlog" from "newly introduced". On-disk format is JSON matching the report schema (findings array only, no run metadata) per Clarifications Q2 and FR-012 — canonicalized and deterministically sorted so byte-identical inputs produce byte-identical baselines.
- **Report**: The full output of one engine run. Contains: engine version, run timestamp, scanned root(s), configuration snapshot, findings array, skipped-files array, engine-error array. Emitted as JSON and rendered secondarily as Markdown.
- **Exclusion Rule**: A configurable predicate that decides whether a test file participates in analysis. Default predicate covers the Mist Cloud API surface (imports `mistapi` OR subject-under-test lives in `src/api/`). Additional predicates can be layered without touching engine core.
- **Detection Rule**: One of the categories above (untested, weak-assertion, missing-failure-mode, missing-edge-case, tautological). Each rule is independently toggleable and has its own severity mapping.
- **Golden Test Set**: A curated list of known findings on the real repo, checked into the engine's meta-tests. Regressions in engine accuracy against the real repo are caught here.
- **Fixture Set**: Synthetic Python test files under the engine's own test tree, half of them deliberately bad and half deliberately good, used to catch rule regressions in isolation from the main repo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a fresh checkout of the current repo, the engine completes a full analysis in under 60 seconds on a developer laptop.
- **SC-002**: The engine's report identifies 100% of the golden-set findings (`src/api/api_data_fetcher.py` untested, `tests/unit/ssh/test_shell_executor.py:110` weak, `tests/maps/test_viewer_callbacks_wave_b_c.py:526` weak, plus one representative each of tautological and missing-failure-mode) at the correct file:line with the correct category.
- **SC-003**: Against the synthetic bad-fixture set, the engine achieves 100% true-positive detection with the correct category assigned; against the synthetic good-fixture set, the engine produces zero false positives.
- **SC-004**: In gate mode, introducing exactly one new weak-assertion test to the working tree produces exit code 1 and lists exactly one new finding; reverting the change produces exit code 0.
- **SC-005**: Two independent runs of the engine against a byte-identical repo checkout produce byte-identical JSON and byte-identical Markdown outputs.
- **SC-006**: The engine performs zero network operations during a run (verified by socket-level observation).
- **SC-007**: The JSON report validates against the tool's published JSON schema on every run.
- **SC-008**: Within one month of adoption, the count of new weak-assertion findings introduced in merged PRs (as observed by the engine's own history) drops by at least 80% compared to the pre-adoption baseline. This is the outcome that justifies the engine's existence: fewer weak tests reaching main.
- **SC-009**: A maintainer can locate any specific finding in the Markdown summary in under 30 seconds, because findings are grouped by severity descending and sorted deterministically within each group.

## Assumptions

- The Mist Cloud API surface is precisely identifiable by the two-part rule (`import mistapi` at module scope OR subject-under-test located under `src/api/`). If future refactoring blurs this boundary, the exclusion rule is intentionally configurable.
- The current line-coverage number of 90% is real but shallow; the engine's job is depth-of-behavior, not coverage. It complements `coverage.py` rather than replacing it.
- Python 3.11+ is the target runtime, matching the rest of the project. Analysis relies on the standard-library `ast` module; no third-party parsers.
- The AST-only constraint is a hard requirement — the engine must be safely runnable in CI even if the tests-under-analysis have side-effectful import time.
- Baselines are checked into the repo, reviewed like any other file, and updated deliberately (never auto-regenerated by CI).
- False positives are acceptable for the edge-case heuristic detector so long as they are flagged as heuristic in the report; they are not acceptable for weak-assertion or tautological detection.
- Mutation testing is a natural future extension but explicitly out of scope for this engine's first delivery.
- CI wiring is explicitly **out of scope** for this feature (see Clarifications Q3). The engine ships with gate-mode exit codes (FR-012) so it is *ready* for CI wiring, but no GitHub Actions workflow, pre-commit hook, or `pyproject.toml` quality-gate entry is added by this initiative. A follow-up feature will wire CI after the engine's rules have been validated against real repo evolution.
