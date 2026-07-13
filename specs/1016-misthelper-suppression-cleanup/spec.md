# Feature Specification: MistHelper.py Suppression Cleanup

**Feature Branch**: `1016-misthelper-suppression-cleanup`

**Created**: 2026-07-13

**Status**: Draft

**Input**: User description: "MistHelper.py suppression cleanup — drive to zero the 8 issue clusters #895–#902 in MistHelper.py."

## User Scenarios & Testing *(mandatory)*

<!--
  Each user story below corresponds to one GitHub issue (#895–#902) and is delivered
  as one independent pull request. Stories are ordered by the required merge sequence:
  bootstrap-first, type-hardening middle, cleanup last. Each story is independently
  testable, reviewable, and revertable — landing any single story removes real
  suppressions from MistHelper.py and closes exactly one tracked issue.
-->

### User Story 1 - Bootstrap Re-Export Suppression Removal (#895) (Priority: P1)

Codebase maintainers need `MistHelper.py`'s bootstrap re-exports (the block that pulls names from `src/` modules for backward compatibility with external tools) to satisfy static-analysis import rules without per-line suppressions, so that unused-import detection produces trustworthy signal across the module.

**Why this priority**: This is the largest single cluster (~124 combined `F401` + `pylint:unused-import` sites) and it blocks accurate import analysis for every subsequent story. Landing it first removes cross-talk between clusters and shrinks the review surface of later PRs.

**Independent Test**: After merge, `ruff check MistHelper.py --select F401` and `pylint MistHelper.py --disable=all --enable=unused-import` both report zero findings, and `python -c "import MistHelper; print(len(MistHelper.__all__))"` succeeds. External tooling that imports names such as `from MistHelper import DeviceFetchConfig` continues to work unchanged.

**Acceptance Scenarios**:

1. **Given** MistHelper.py at HEAD of the PR branch, **When** ruff + pylint run under CI, **Then** zero `F401` and zero `unused-import` findings remain and no `# noqa: F401` or `# pylint: disable=unused-import` comments exist in the file.
2. **Given** the merged PR, **When** an external caller runs `from MistHelper import <any previously re-exported symbol>`, **Then** the import resolves to the same object it did before the PR.
3. **Given** the merged PR, **When** the audit script (`tools/refactor_analyzer/`) is re-run, **Then** the total count of MistHelper.py suppressions has dropped by at least 120.

---

### User Story 2 - Mypy Grab-Bag Suppression Removal (#899) (Priority: P2)

Codebase maintainers need the mixed mypy suppression cluster (`misc`, `assignment`, `no-any-return`, `arg-type`, `operator`) in MistHelper.py eliminated so that type checking produces honest results and unblocks the downstream typing PRs.

**Why this priority**: Fixing the `assignment` sites (typically `X: type[Foo] | None = None` at bootstrap-time) removes the Any-typed globals that cascade into the `no-untyped-call` findings addressed in Story 4. It must land before Story 4 to avoid re-work.

**Independent Test**: After merge, `mypy MistHelper.py --strict` (or the project's current mypy configuration) reports zero findings in categories `misc`, `assignment`, `no-any-return`, `arg-type`, and `operator`, and no `# type: ignore[misc|assignment|no-any-return|arg-type|operator]` comments remain in MistHelper.py.

**Acceptance Scenarios**:

1. **Given** MistHelper.py at HEAD of the PR branch, **When** mypy runs under CI, **Then** the five targeted error categories return zero findings in MistHelper.py.
2. **Given** the merged PR, **When** the file is grepped for `# type: ignore[misc`, `# type: ignore[assignment`, `# type: ignore[no-any-return`, `# type: ignore[arg-type`, `# type: ignore[operator`, **Then** zero matches are returned.
3. **Given** the merged PR, **When** downstream callers of MistHelper's public API run their existing test suites, **Then** all tests pass without modification.

---

### User Story 3 - Complexity Cluster Reduction (#901) (Priority: P3)

Codebase maintainers need the remaining `C901` (cyclomatic complexity) and `PLR0913` (too-many-arguments) findings on `GlobalImportManager`, `DeviceFetchConfig`, and `main()` removed by extracting narrow helper functions/methods, so those symbols become testable and readable without per-symbol suppressions.

**Why this priority**: Reducing surface area on these three symbols shrinks the code that later stories (typing, line-length, bandit) must edit, reducing merge conflicts and rework.

**Independent Test**: After merge, `ruff check MistHelper.py --select C901,PLR0913` returns zero findings, no `# noqa: C901` or `# noqa: PLR0913` comments remain, and each extracted helper has at least one unit test invoked from the existing test suite. The public signature of `GlobalImportManager`, `DeviceFetchConfig`, and `main()` is unchanged.

**Acceptance Scenarios**:

1. **Given** MistHelper.py at HEAD of the PR branch, **When** ruff runs under CI, **Then** zero `C901` and zero `PLR0913` findings remain in the file.
2. **Given** the merged PR, **When** external code calls `MistHelper.GlobalImportManager(...)`, `MistHelper.DeviceFetchConfig(...)`, or invokes `MistHelper.main()`, **Then** behavior and return values are identical to pre-PR HEAD.
3. **Given** the merged PR, **When** pytest runs, **Then** coverage on the extracted helpers is at least 90% and the overall project coverage gate (90%) still passes.

---

### User Story 4 - No-Untyped-Call Suppression Removal (#898) (Priority: P4)

Codebase maintainers need the `no-untyped-call` cluster removed by promoting the Any-typed facade globals in `src/utils/misthelper_facade.py` to `Protocol` classes, so mypy can resolve call sites through the facade without per-call suppressions.

**Why this priority**: This depends on Story 2's assignment fixes and is best done after Story 3's complexity extractions, since the extracted helpers may participate in facade calls.

**Independent Test**: After merge, `mypy MistHelper.py --strict` reports zero `no-untyped-call` findings, and no `# type: ignore[no-untyped-call]` comments remain in MistHelper.py. `src/utils/misthelper_facade.py` defines one or more `Protocol` classes covering the facade surface.

**Acceptance Scenarios**:

1. **Given** MistHelper.py at HEAD of the PR branch, **When** mypy runs under CI, **Then** zero `no-untyped-call` findings remain in the file.
2. **Given** the merged PR, **When** external code that reads or writes to the facade attributes runs, **Then** behavior is unchanged.
3. **Given** the merged PR, **When** the Protocol classes are inspected, **Then** they cover the exact call surface used by MistHelper.py (no unused methods, no missing methods).

---

### User Story 5 - Type-Arg Suppression Removal (#897) (Priority: P5)

Codebase maintainers need the `mypy:type-arg` cluster removed by providing concrete generic annotations (`dict[str, Any]`, `list[SomeType]`, etc.) at the call sites, so bare-generic warnings disappear without suppression.

**Why this priority**: Small, isolated cluster (3 sites). Runs after the larger typing PRs so the concrete types can reference stabilized Protocol classes and helper signatures from Stories 2–4.

**Independent Test**: After merge, `mypy MistHelper.py --strict` reports zero `type-arg` findings, and no `# type: ignore[type-arg]` comments remain in MistHelper.py.

**Acceptance Scenarios**:

1. **Given** MistHelper.py at HEAD of the PR branch, **When** mypy runs under CI, **Then** zero `type-arg` findings remain in the file.
2. **Given** the merged PR, **When** external callers pass through the newly-annotated parameters, **Then** they see no runtime behavior change.

---

### User Story 6 - Line-Length Suppression Removal (#896) (Priority: P6)

Codebase maintainers need the `E501` line-length findings in MistHelper.py eliminated by hand-wrapping the offending lines (or, where clearly warranted, extracting a small helper), so the file conforms to the project line-length gate without suppressions.

**Why this priority**: Line-wrapping frequently reflows lines that neighboring typing PRs also touch. Landing E501 after all typing/complexity PRs prevents merge conflicts and rewrites.

**Independent Test**: After merge, `ruff check MistHelper.py --select E501` returns zero findings and no `# noqa: E501` comments remain in the file.

**Acceptance Scenarios**:

1. **Given** MistHelper.py at HEAD of the PR branch, **When** ruff runs under CI, **Then** zero `E501` findings remain in the file.
2. **Given** the merged PR, **When** `black --check MistHelper.py` runs, **Then** it reports no diffs.
3. **Given** the merged PR, **When** the file is diffed against pre-PR HEAD, **Then** no logic changes are present — only whitespace, parenthesization, and narrow helper extractions.

---

### User Story 7 - Bandit Suppression Removal (#900) (Priority: P7)

Codebase maintainers need the `bandit` cluster (dominated by `B603` subprocess-without-shell-equals-true, plus `B404` and others) removed by performing an input-validation audit on each subprocess call site and centralizing invocation through a new `subprocess_runner` helper module where appropriate, so security suppressions are backed by verified safe usage rather than blanket `# nosec`.

**Why this priority**: Bandit-related work touches subprocess call sites, some of which are inside code paths reshaped by Stories 3 (complexity) and 4 (typing). Landing this after those changes ensures the security review lands on stable code.

**Independent Test**: After merge, `bandit -r MistHelper.py` reports zero findings, no `# nosec` comments remain in the file, and each affected subprocess call site is either (a) documented as safe with validated inputs or (b) refactored to route through `subprocess_runner`.

**Acceptance Scenarios**:

1. **Given** MistHelper.py at HEAD of the PR branch, **When** bandit runs under CI, **Then** zero findings remain in the file.
2. **Given** the merged PR, **When** subprocess invocations execute end-to-end (either via existing tests or the security audit checklist), **Then** all inputs are validated at or before invocation and no new attack surface is introduced.
3. **Given** the merged PR, **When** the `subprocess_runner` helper (if introduced) is unit tested, **Then** coverage is at least 90%.

---

### User Story 8 - Long-Tail Cleanup (#902) (Priority: P8)

Codebase maintainers need the residual long-tail suppressions in MistHelper.py (`PLC0415` late imports, `E402` module-level import order, remaining `mypy-misc`, `PLW0602` global-variable-not-assigned, structural/pragma tags) resolved as a final sweep, so the module reaches the zero-suppression success state.

**Why this priority**: This is the final sweep — it depends on all prior clusters being clean so that the residual set is well-defined and no new suppressions appear as side effects of earlier PRs.

**Independent Test**: After merge, MistHelper.py contains zero occurrences of `# noqa`, `# type: ignore`, `# nosec`, and `# pylint: disable`. Full lint stack (`ruff check`, `pylint`, `mypy --strict`, `bandit -r`, `black --check`) passes on the file with no suppressions.

**Acceptance Scenarios**:

1. **Given** MistHelper.py at HEAD of the PR branch, **When** all four lint tools run under CI, **Then** zero findings and zero suppression comments remain.
2. **Given** the merged PR, **When** the file is grepped for the suppression patterns listed above, **Then** the match count is exactly zero.
3. **Given** the merged PR, **When** `pyproject.toml` is diffed against the state at the start of the workflow, **Then** the only changes are per-file-ignore removals — no rule disables, no fail-under lowering.

---

### Edge Cases

- **Public API drift**: If a helper extraction (Story 3 or 7) is tempted to change a public class/function signature, the PR MUST be scoped down — public API is frozen by an FR below.
- **Merge conflict from CI**: If any PR fails to merge cleanly on main (e.g., because a peer PR landed first), the branch is rebased and re-tested; no `--admin` bypass is used and no merge proceeds unless `mergeStateStatus=CLEAN`.
- **New suppressions introduced by a PR**: The PR is rejected in review; the author must either resolve the root cause or split the change into a follow-up story. No new suppressions may be introduced anywhere in the repo.
- **Coverage regression on an extracted helper**: If Story 3 or 7 extracts a helper that lands below 90% coverage, the PR must add tests before merge; the project coverage gate must not drop.
- **CI stale audit**: If the audit numbers in the delivery ordering shift materially before a PR is opened (e.g., another workflow lands and touches MistHelper.py), the workflow lead refreshes the audit via `tools/refactor_analyzer/` and adjusts remaining stories.
- **Assumption mismatch on facade Protocol coverage (Story 4)**: If the Protocol classes cannot cover a call surface without altering signatures, that call site is documented and deferred to a follow-up issue rather than suppressed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workflow MUST deliver exactly 8 pull requests, one per GitHub issue in the set `{#895, #896, #897, #898, #899, #900, #901, #902}`, in the ordered sequence `[#895, #899, #901, #898, #897, #896, #900, #902]`.
- **FR-002**: Each pull request MUST fully close its target GitHub issue on merge, referenced via a `Closes #NNN` trailer in the PR description or squash commit body.
- **FR-003**: The workflow MUST use serial dispatch: pull request N+1 MUST NOT be opened until pull request N has landed cleanly on `main`.
- **FR-004**: Each pull request MUST originate from its own short-lived branch cut from the current `main` at the moment the PR is opened; the `1016-misthelper-suppression-cleanup` feature branch is used ONLY as the coordination home for spec/plan/tasks artifacts, not as the base for the 8 delivery PRs.
- **FR-005**: Each pull request MUST pass `black --check` and `ruff check` locally before being pushed to the remote branch.
- **FR-006**: No pull request MUST use administrative merge bypass; each PR MUST wait for `mergeStateStatus=CLEAN` before merging.
- **FR-007**: The public API surface of `MistHelper.py` (the set of names exported to external tools, including but not limited to those currently accessible via `from MistHelper import ...`) MUST remain unchanged across all 8 pull requests. Public API is defined by the set of module-level names accessible on the `MistHelper` module object at the start of this workflow.
- **FR-008**: No pull request MUST introduce a new `# noqa`, `# type: ignore`, `# nosec`, or `# pylint: disable` comment anywhere in the repository. A CI check or manual review step MUST enforce this.
- **FR-009**: The project's continuous-integration pipeline MUST remain green on every merged commit produced by this workflow.
- **FR-010**: Modifications to `pyproject.toml` (or equivalent lint tool configuration) MUST be restricted to per-file-ignore removals; no rule disables, no fail-under threshold changes, and no bulk rule suppressions are permitted.
- **FR-011**: The workflow MUST NOT extract further classes or functions from `MistHelper.py` beyond the narrow helper additions explicitly required to eliminate a suppression in the current story.
- **FR-012**: The workflow MUST NOT modify files under `src/` except to (a) add Protocol classes to `src/utils/misthelper_facade.py` (Story 4) or (b) add a `subprocess_runner` helper module (Story 7), and only when those additions are load-bearing for the current story's suppression fix.
- **FR-013**: On completion of all 8 pull requests, `MistHelper.py` MUST contain zero occurrences of `# noqa`, zero `# type: ignore`, zero `# nosec`, and zero `# pylint: disable` comments.
- **FR-014**: The workflow MUST adopt the fresh 2026-07-13 audit numbers (rerun through `tools/refactor_analyzer/`) as ground truth for story sizing; stale projections in issue bodies MUST NOT gate merge decisions.
- **FR-015**: Each pull request MUST include or link to an updated audit report showing the delta in suppression counts caused by that PR.
- **FR-016**: The project's coverage threshold of 90% and pylint fail-under threshold of 9.5 MUST both continue to hold on every merged commit.

### Key Entities *(include if feature involves data)*

- **Suppression Comment**: An inline directive of one of four forms (`# noqa`, `# type: ignore`, `# nosec`, `# pylint: disable`) that instructs a lint or type tool to skip a specific rule at a specific site. In `MistHelper.py`, each such comment is a work item; success is measured by driving the count to zero.
- **Issue Cluster**: A themed group of suppressions tracked by a single GitHub issue (`#895` through `#902`). Each cluster maps 1:1 to a User Story and 1:1 to a delivery pull request.
- **Bootstrap Re-Export Block**: The section of `MistHelper.py` that re-imports names from `src/` modules for backward compatibility. Owned by Story 1; requires an `__all__` declaration (optionally hoisted into `src/_bootstrap.py`) to satisfy import rules without suppressions.
- **Facade Global**: A module-level attribute in `MistHelper.py` (or `src/utils/misthelper_facade.py`) that currently has an implicit `Any` type, triggering `no-untyped-call` on downstream call sites. Owned by Story 4; requires a `Protocol` class describing its call surface.
- **Public API Symbol**: A module-level name of `MistHelper.py` that is (or may be) imported by external tools. The union of these names constitutes the frozen public API surface referenced by FR-007.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After all 8 pull requests are merged, `MistHelper.py` contains exactly zero occurrences of `# noqa`, zero `# type: ignore`, zero `# nosec`, and zero `# pylint: disable` comments (verified via automated grep).
- **SC-002**: All 8 GitHub issues in the set `{#895–#902}` are closed on the merge commit of their respective pull request, verified by GitHub's issue-linking status.
- **SC-003**: No new suppressions are introduced anywhere in the repository during the workflow (net delta of suppression count in files outside `MistHelper.py` is zero or negative).
- **SC-004**: CI pipeline is green on every merge commit produced by the workflow — no red builds bypassed, no `--admin` merges.
- **SC-005**: The project coverage threshold (90%) holds on every merged commit and is at least 90.0% on the final merge commit.
- **SC-006**: The pylint fail-under threshold (9.5) holds on every merged commit and is at least 9.5 on the final merge commit.
- **SC-007**: The public API surface of `MistHelper.py` (module-level names) is byte-identical between the start of Story 1 and the merge commit of Story 8, verified by a diff of `dir(MistHelper)` output.
- **SC-008**: Each of the 8 pull requests is reviewed and merged serially — no two PRs from this workflow are simultaneously open on the remote at any time.
- **SC-009**: The end-to-end elapsed time from opening Story 1's PR to merging Story 8's PR is within the team's target of one working month (4 calendar weeks), assuming standard review cadence.

## Assumptions

- The fresh 2026-07-13 audit (`tools/refactor_analyzer/` output referenced in the input) is authoritative and supersedes the stale projections still cited in issue bodies of `#895–#902`.
- The `#1014` hot-classes refactor is fully merged; no further class extractions from `MistHelper.py` are pending outside this workflow.
- External tools that consume `MistHelper.py` continue to import via the module's current public API (i.e., no consumer is relying on private/underscore-prefixed names).
- The project's lint stack (ruff, pylint, mypy, bandit, black) and their configured rule sets remain stable throughout the workflow; any upstream tool bump is handled outside this feature.
- Coverage and pylint thresholds (90%, 9.5) already hold on `main` at the start of Story 1; the workflow's job is to preserve them, not raise them.
- The `src/_bootstrap.py` module hoist mentioned as "optional" for Story 1 is genuinely optional — the `__all__` declaration alone suffices, and the hoist only happens if it materially simplifies the diff.
- GitHub issue numbering `#895–#902` is not re-used or reassigned during the workflow; the same issue numbers referenced here remain the correct closing targets.
- Reviewers have capacity to review 8 sequential PRs at roughly one PR per 2–3 working days, matching SC-009's target elapsed time.
- The `tools/refactor_analyzer/` tooling remains functional and can be re-run between stories to refresh audit deltas required by FR-015.
