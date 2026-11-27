# Feature Specification: Merge queue rollout and acceptance

**Feature Branch**: `docs/3071-merge-queue-rollout` (planned for the pull request). This record reuses the folder `3071-merge-queue-support`.

**Created**: 2026-10-20

**Revised**: 2026-11-26

**Status**: Specified

**Input**: Issue #3071. A pull request cannot land because `main` moves faster than one CI run. The preparation merged as PR #4362 on 2026-10-20. Define the remaining rollout work and its acceptance evidence.

## Clarifications

### Session 2026-11-26

- Q: Does this change reuse the legacy record folder? A: Yes. Legacy tasks T012 and T013 stay in one record for issue #3071.
- Q: Does the pull request close issue #3071? A: No. It uses `Refs #3071`. Operational acceptance is incomplete, and the owner keeps the issue open. Decision D-5 records the conflict with the constitution.
- Q: Does this change edit a workflow file? A: No. `ci.yml` and `codeql.yml` already declare `merge_group`. A workflow file edit also blocks auto-merge.
- Q: Does this change activate the merge queue? A: No. Owner activation needs separate owner approval.
- Q: Which file holds the merge rule? A: `.github/copilot-instructions.md` and `documentation/quality-gates.md`. The historical path `.github/instructions/git-flow-multi-agent.instructions.md` is absent on `main`. The owner approved the substitution.
- Q: Does this change need a release-note fragment? A: Yes. The constitution requires one fragment for each change. Decision D-6 records the conflict with the changelog README.
- Q: Which Python version applies? A: Python 3.15 or newer. `pyproject.toml` requires `>=3.15`. The legacy plan named Python 3.13, which is stale.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the serial merge slot until owner activation (Priority: P1)

A maintainer merges one pull request at a time. The merge queue stays inactive until the owner activates it. Strict up-to-date protection stays on during the whole rollout.

**Why this priority**: An early merge queue can stall every merge. Strict protection blocks a merge against a stale base.

**Independent Test**: Read branch protection, rulesets, and the merge queue state with read-only API calls. Confirm strict protection, 15 required contexts, zero rulesets, and no merge queue.

**Acceptance Scenarios**:

1. **Given** this change has merged, **When** an operator reads branch protection, **Then** `strict` is true and the 15 required context names are unchanged.
2. **Given** the owner has not activated the merge queue, **When** a maintainer merges a pull request, **Then** the maintainer uses the serial merge slot and does not treat auto-merge as a queue.
3. **Given** a pull request edits a file under `.github/workflows/`, **When** its checks pass, **Then** a maintainer merges it by hand, because the shared auto-merge workflow refuses that edit.

---

### User Story 2 - Test each queue candidate on its own commit (Priority: P1)

The owner needs each queue candidate to run the 15 required contexts on the candidate commit. Each queue candidate needs its own concurrency group. One queue run must never cancel another queue run.

**Why this priority**: A required context that does not report blocks the queue. A canceled queue run can leave the queue waiting.

**Independent Test**: Run `tests/guardrails/test_ci_gate_triggers.py`. Read the `merge_group` triggers, concurrency groups, and checkout references in `ci.yml` and `codeql.yml`.

**Acceptance Scenarios**:

1. **Given** a queue candidate, **When** GitHub requests checks, **Then** `ci.yml` and `codeql.yml` start, because each declares `merge_group` with `checks_requested`.
2. **Given** two queue candidates, **When** the second one starts, **Then** each candidate has its own group, and no run cancels the other.
3. **Given** a removed `merge_group` trigger or a renamed required context, **When** the guard runs, **Then** the guard fails and names the rejected contract.

---

### User Story 3 - Record owner evidence before retiring serial merging (Priority: P2)

After owner activation, the owner verifies two low-risk queue candidates. The owner records each queue commit, each required context result, each merge commit, and each main run on issue #3071. Serial merging continues until both candidates succeed.

**Why this priority**: The acceptance criteria of issue #3071 need live evidence. Local tests cannot prove queue operation.

**Independent Test**: Read the owner evidence comment on issue #3071. Confirm that it contains each field that `documentation/quality-gates.md` names.

**Acceptance Scenarios**:

1. **Given** owner activation, **When** a verification candidate enters the queue, **Then** a `merge_group` run starts for the queue commit.
2. **Given** a required context result is canceled, timed out, stale, or skipped, **When** the owner reads it, **Then** the owner treats the result as unresolved.
3. **Given** two successful queued merges, **When** the owner records the evidence, **Then** a later documentation pull request may retire the serial merge slot text.

---

### User Story 4 - Keep the merge rule accurate and guarded (Priority: P2)

A contributor reads the workflow table and the merge queue procedure. Each text matches the workflows. A guard test fails when the workflow table or the procedure heading drifts.

**Why this priority**: The workflow table omitted merge queue candidates on 2026-11-26. A contributor who reads that table gets an incorrect trigger list.

**Independent Test**: Run the new guard method, the STE gate on the changed Markdown files, and the markdown link check.

**Acceptance Scenarios**:

1. **Given** the workflow table, **When** the guard reads the `ci.yml` and `codeql.yml` rows, **Then** each row names merge queue candidates.
2. **Given** the link in `.github/copilot-instructions.md`, **When** the link target loads, **Then** the heading `## Merge queue preparation and activation` exists in `documentation/quality-gates.md`.
3. **Given** a changed Markdown file, **When** the STE gate grades it, **Then** the score is 80 or above.

---

### Edge Cases

- A later edit removes `merge_group` from `ci.yml` or `codeql.yml`. The guard fails. Caution: queue activation stays blocked until the trigger returns.
- The owner activates the merge queue before `merge_group` reaches `main`. Warning: required checks can stay absent and prevent every merge.
- `ste-lint.yml` becomes a required context without a `merge_group` trigger. Caution: every queue candidate waits for a context that never reports.
- Three branch protection reads disagree about the review rule. The owner confirms the rule before activation.
- The `CodeQL` context does not report on a queue commit. The owner records the result and disables the queue rule if the context stays absent.
- A queue candidate fails a required context. The merge queue removes it. The author repairs the pull request and adds it to the queue again.
- A pull request edits a file under `.github/workflows/`. The shared auto-merge workflow posts a manual merge notice. A maintainer merges the pull request by hand.
- Another open pull request changes `ci.yml` or `codeql.yml`. Each change waits for the other pull request to land, or the owner assigns a handover.
- The historical instruction path is absent. The owner approved `documentation/quality-gates.md` as the documentation location.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `ci.yml` and `codeql.yml` MUST declare `merge_group` with `types: [checks_requested]`.
- **FR-002**: The 14 `ci.yml` job names and the `CodeQL` required context MUST keep their current names.
- **FR-003**: Each queue candidate MUST run every required context on the candidate commit.
- **FR-004**: Each queue candidate MUST use its own concurrency group. A queue run MUST NOT be canceled by another run.
- **FR-005**: Pull request runs and `main` runs MUST keep their current triggers and concurrency behavior.
- **FR-006**: The workflow table in `.github/copilot-instructions.md` MUST name merge queue candidates for `ci.yml` and `codeql.yml`.
- **FR-007**: `documentation/quality-gates.md` MUST describe preparation, owner activation, evidence, constraints, and recovery under the heading `## Merge queue preparation and activation`.
- **FR-008**: A guard test MUST fail when the workflow table or the procedure heading drifts.
- **FR-009**: This change MUST NOT change branch protection, rulesets, required contexts, or the merge queue.
- **FR-010**: This change MUST NOT edit any file under `.github/workflows/`.
- **FR-011**: The pull request for this change MUST use `Refs #3071` and MUST NOT close issue #3071.
- **FR-012**: The owner MUST record two verified queued merges on issue #3071 before the serial merge slot text is retired.
- **FR-013**: Each verification candidate MUST be a documentation-only pull request with no workflow file change. The owner MUST add each candidate to the merge queue by hand, with a batch size of one.
- **FR-014**: Before owner activation, the owner MUST confirm the review rule, because three API reads conflict.

### Key Entities

- **Queue candidate**: A pull request in the merge queue. GitHub tests it on a temporary branch whose name starts with `gh-readonly-queue/main/pr-`.
- **Required context**: A status name that branch protection requires before a merge. The set holds 14 `ci.yml` job names and the `CodeQL` context.
- **Serial merge slot**: The rule that one pull request at a time lands on `main` until owner activation.
- **Activation evidence**: The owner record on issue #3071. It holds the queue commit, each required context result, the merge commit, and the main run ID.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the change, branch protection shows the same `strict` value and the same 15 required context names as before the change.
- **SC-002**: The new guard method fails before the workflow table fix and passes after it.
- **SC-003**: The STE gate, the changelog policy guard, the process folder guard, and the spec route guard pass.
- **SC-004**: After owner activation, two verification candidates merge. Each required context succeeds on each queue commit.
- **SC-005**: Issue #3071 stays open until the owner records the evidence from SC-004.

## Out of Scope

- Activating, changing, or disabling the merge queue, rulesets, branch protection, or required contexts.
- Editing `ci.yml`, `codeql.yml`, `ste-lint.yml`, `auto-merge.yml`, or any shared workflow in `misthelper-devtools`.
- Creating `.github/instructions/git-flow-multi-agent.instructions.md`.
- Editing `AGENTS.md`. Its canonical copy is in `misthelper-devtools`.
- Adding `merge_group` to `ste-lint.yml`.
- Changing how the shared auto-merge workflow handles canceled results.
- Repairing the failed non-required `ops-portal` job on PR #4483.

## Assumptions

- The owner activates the merge queue after this change merges.
- Strict up-to-date protection stays on during the whole rollout.
- The public GitHub merge queue documentation describes the behavior that the repository uses.
- The shared auto-merge workflow keeps `gh pr merge --auto` at its pinned commit `d63a120487cecf750184cb178387cdc25c0a7635`.
- Each verification candidate changes no product code and no workflow file.

## Dependencies

- PR #4362 merged on 2026-10-20. It supplies the `merge_group` triggers and the guard contracts.
- PR #4483 merged on 2026-10-26. It supplies the serial merge text in `.github/copilot-instructions.md`.
- Issue #3070 closed. The serial merge slot is free.
- The rules that this rollout keeps are recorded in issues #1851 (merges by `GITHUB_TOKEN` start no push run), #1952 (no branch filter on required workflows), #1954 (workflow file merges need a manual merge), #1960 (orphan pushes), and #3926 (`always()` conditions ignore a cancel).
