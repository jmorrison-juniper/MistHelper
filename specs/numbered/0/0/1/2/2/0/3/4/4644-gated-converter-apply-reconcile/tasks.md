# Tasks: Gated Converter Apply and Reconciliation

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/0/3/4/4644-gated-converter-apply-reconcile/`. Parent tasks T021 and T022 map to the tasks in this file. The IDs in this file belong to issue 4644.

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, and the contracts in `design/contracts/`.

**Rules for this list**: Each task names exact paths and one verification command from the local gates table. The gate `ste-linter` covers each Markdown file. Status values are `open`, `verified-present`, `partial`, or `absent`. `[P]` marks a task that can run in parallel with its neighbors.

## Phase 1: Evidence and prerequisites

- **T001** Record the gate evidence for G1 to G5. Requirements: FR-004, FR-014. Decisions: D-5, D-17, D-21. Files: `specs/numbered/0/0/1/2/2/0/3/4/4644-gated-converter-apply-reconcile/design/research.md`. Acceptance: Each gate row names its owner, its issue, and its current state. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/3/4/4644-gated-converter-apply-reconcile/design/research.md`. Status: partial. The table exists in draft form.
- **T002** Record amendments X-1 to X-4 in the issue 4636 record before its T004. Requirements: FR-025. Decision: D-14. Files: `specs/numbered/0/0/1/2/2/0/2/1/4636-converter-package-state-model/plan.md`. Acceptance: The 4636 plan moves `intake.py` and `proposal.py` under `state/records/`, adds `not-applied`, adds the cancel edge, and extends the scope digest. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/1/4636-converter-package-state-model/plan.md`. Status: absent. Issue 4636 is not on `main`.
- **T003** [P] Record the field evidence for families F-01 to F-08. Requirements: FR-011. Decision: D-2. Files: `specs/numbered/0/0/1/2/2/0/3/4/4644-gated-converter-apply-reconcile/design/contracts/mist-write-families.md`. Acceptance: Each family row names its OpenAPI line, its SDK line, and its allow-list. Each list states its evidence source. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/3/4/4644-gated-converter-apply-reconcile/design/contracts/mist-write-families.md`. Status: partial. The contract exists in draft form. Field evidence waits for issue 4634.

## Phase 2: State records and gates

- **T004** [P] Add `ChangeSet` to `src/interfaces/portals/cisco_config_converter/state/records/proposal.py`. Requirements: FR-001, FR-011. Tests: TST-11. Acceptance: `ChangeSet` lists each change item in fixed order, and its digest covers the family, object ID, and payload digest. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_executor.py`. Status: absent. Depends on T002.
- **T005** [P] Add `ApprovalGate` to `src/interfaces/portals/cisco_config_converter/state/lifecycle/approval.py`. Requirements: FR-002 to FR-005, FR-008, FR-022. Tests: TST-01 to TST-05, TST-07, TST-08. Acceptance: The gate refuses every case in its test list and makes no SDK call. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_gates.py`. Status: absent. Depends on T002.
- **T006** [P] Add `BackupGate` to `src/interfaces/portals/cisco_config_converter/state/lifecycle/backup.py`. Requirements: FR-006. Tests: TST-06. Acceptance: The gate refuses a manifest with incomplete pagination, a count mismatch, a checksum mismatch, a wrong organization, or a wrong family. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_gates.py`. Status: absent. Depends on T002.

## Phase 3: Executor and adapter

- **T007** Add `MistWriteAdapter` to `src/interfaces/portals/cisco_config_converter/state/execution.py`. The class attribute `FAMILIES` holds the default-disabled registry. Requirements: FR-011, FR-013, FR-014, FR-015, FR-016. Tests: TST-09, TST-12, TST-14, TST-16. Acceptance: The adapter calls each SDK method with explicit arguments, applies each bound, and never repeats a write. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_executor.py`. Status: absent. Depends on T004.
- **T008** Add `OutcomeClassifier` to `src/interfaces/portals/cisco_config_converter/state/execution.py`. Requirements: FR-017, FR-021. Tests: TST-13, TST-15, TST-17. Acceptance: The classifier maps each status class to one outcome, as `design/contracts/reconciliation.md` defines. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_executor.py`. Status: absent. Depends on T007.
- **T009** Add `ApplyExecutor` to `src/interfaces/portals/cisco_config_converter/state/execution.py`. Requirements: FR-007 to FR-010, FR-012, FR-018. Tests: TST-10, TST-19, TST-27. Acceptance: The executor runs preflight, takes the lock, consumes the approval, writes in order, and stops after the first non-verified outcome. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_gates.py tests/integration/web_portal/cisco_config_converter/apply/test_apply_executor.py`. Status: absent. Depends on T005, T006, T008.
- **T010** Add `ReconciliationReader` to `src/interfaces/portals/cisco_config_converter/state/execution.py`. Requirements: FR-019, FR-020. Tests: TST-20 to TST-23. Acceptance: The reader calls read methods only and marks an object verified only when both comparisons match. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_reconcile.py`. Status: absent. Depends on T008.
- **T011** [P] Add the logging and redaction checks at each action. Requirements: FR-023, FR-024. Tests: TST-18. Files: `src/interfaces/portals/cisco_config_converter/state/execution.py`. Acceptance: Each action logs an info line before and a debug line after. No log line contains a payload value, a token, or a secret. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_executor.py`. Status: absent. Depends on T009.

## Phase 4: Route and tests

- **T012** Add `ConverterInput.apply_action` and one `add_url_rule` line for `/apply` in `src/interfaces/portals/cisco_config_converter/routes.py`. Requirements: FR-001, FR-003, FR-022, FR-025. Tests: TST-24 to TST-26. Acceptance: The route accepts `submit`, `cancel`, and `status` actions. Each response carries `Cache-Control: no-store` and no payload value. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_routes.py`. Status: absent. Depends on T009.
- **T013** [P] Create the apply test package at `tests/integration/web_portal/cisco_config_converter/apply/__init__.py`. Requirements: SC-007. Acceptance: The folder holds five children or fewer. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply`. Status: absent.
- **T014** [P] Update the unit test import after X-1 in `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`. Requirements: FR-025. Acceptance: The import names `state.records.intake`, and the test passes. Verification: `python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`. Status: open. Depends on T002.
- **T015** Verify that preview, review, and export behavior does not change, in `tests/integration/web_portal/cisco_config_converter/test_routes.py`. Requirements: FR-025. Acceptance: The existing route tests pass without edits. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`. Status: open.
- **T016** Coordinate the browser controls with issue 4647. Requirements: FR-001. Decision: D-16. Files: `src/interfaces/portals/cisco_config_converter/presentation/converter.js` (issue 4647 edits this file). Acceptance: This record edits no presentation file. Issue 4647 calls the `/apply` contract after T012 lands. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_routes.py`. Status: open.
- **T017** Record amendments X-5, X-7, X-8, and X-9 in the drafts for issues 4646 and 4648. Requirements: FR-025. Decision: D-16. Files: `specs/numbered/0/0/1/2/2/0/3/4/4644-gated-converter-apply-reconcile/analysis.md` (lists the amendments) and the draft plans of issues 4646 and 4648. Acceptance: Each amendment names its owner and its target line. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/3/4/4644-gated-converter-apply-reconcile/analysis.md`. Status: absent.
- **T018** Check the folder capacity and the module symbols. Requirements: FR-025, SC-007. Acceptance: Each touched folder holds five children or fewer, and no module-level name is lost. Verification: `symbol-diff --base origin/main src/interfaces/portals/cisco_config_converter/routes.py`. Status: absent. Depends on T012.
- **T019** Run the full refusal and outcome matrix against the recording SDK double. Requirements: SC-001, SC-002, SC-003. Acceptance: Each refusal test proves zero SDK write calls, and each ambiguous write has zero automatic repeats. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/apply`. Status: absent. Depends on T009.

## Phase 5: Final gates and delivery

- **T-LOCAL-GATES** Run each gate in the local gates table that applies to the changed files. Requirements: FR-025. Acceptance: Each gate reports its own result. Each skipped gate states its reason. Status: absent. Depends on T018 and T019. Verification, in this order:
  - `python -m py_compile src/interfaces/portals/cisco_config_converter/state/execution.py`
  - `python -m ruff check src/interfaces/portals/cisco_config_converter tests/integration/web_portal/cisco_config_converter/apply`
  - `python -m black --check src/interfaces/portals/cisco_config_converter tests/integration/web_portal/cisco_config_converter/apply`
  - `python -m mypy $MYPY_PATHS --config-file pyproject.toml`
  - `radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10`
  - `bandit -c pyproject.toml -r src/interfaces/portals/cisco_config_converter -q`
- **T-PR** Commit, rebase, push, and open the pull request. Acceptance: The commit uses a Conventional Commits subject such as `feat(converter): add gated apply and reconciliation`. The branch is `feat/4644-gated-converter-apply`. The body contains `Closes #4644`. Verification: `gh pr view --json title,body,headRefName`. Status: absent. Depends on T-LOCAL-GATES.
- **T-REMOTE-CI** Watch the required checks on the pull request. Acceptance: Each required check reports success on the latest commit. Verification: `gh pr checks --watch`. Status: absent. Depends on T-PR.
- **T-MERGE** Enable auto-merge only after remote checks pass and the orchestrator authorizes the merge. Acceptance: The pull request carries the `auto-merge` label only after each check is green. A pull request with a destructive operation needs a human review first. Verification: `gh pr checks --watch`. Status: absent. Depends on T-REMOTE-CI.

## Dependencies & Execution Order

- T002 blocks T004, T005, T006, and T014.
- T004 blocks T007. T007 blocks T008. T008 blocks T009 and T010.
- T005 and T006 block T009. T009 blocks T011, T012, and T019.
- T012 blocks T018. T018 and T019 block T-LOCAL-GATES.
- T001 and T003 run before T004. They do not block T002.

## Test Plan Summary

| ID | File | Scope |
| --- | --- | --- |
| TST-01 | `apply/test_apply_gates.py` | Missing approval refused with zero writes. |
| TST-02 | `apply/test_apply_gates.py` | Wrong typed word refused. Lowercase, trailing space, and the word `CONFIRM` each fail. |
| TST-03 | `apply/test_apply_gates.py` | Unverified operator refused. |
| TST-04 | `apply/test_apply_gates.py` | Approval at exactly 15 minutes refused. |
| TST-05 | `apply/test_apply_gates.py` | Changed proposal or scope digest refused. |
| TST-06 | `apply/test_apply_gates.py` | Incomplete backup manifest refused. |
| TST-07 | `apply/test_apply_gates.py` | Second use of one approval refused. |
| TST-08 | `apply/test_apply_gates.py` | Cancel voids the approval and keeps the operation in `reviewed`. |
| TST-09 | `apply/test_apply_executor.py` | Disabled family makes zero SDK write calls. |
| TST-10 | `apply/test_apply_executor.py` | Preflight digest mismatch stops before the first write. |
| TST-11 | `apply/test_apply_executor.py` | Allow-list enforced. Unrelated fields preserved. |
| TST-12 | `apply/test_apply_executor.py` | Explicit SDK arguments only. Endpoint path matches the OpenAPI path. |
| TST-13 | `apply/test_apply_executor.py` | HTTP 400, 401, 403, and 404 classify as failed and stop later writes. |
| TST-14 | `apply/test_apply_executor.py` | Final HTTP 429 classifies as indeterminate. The mocked transport counts the SDK attempts. |
| TST-15 | `apply/test_apply_executor.py` | HTTP 500 and a malformed success classify as indeterminate. |
| TST-16 | `apply/test_apply_executor.py` | A timeout bounds the wait and records indeterminate. |
| TST-17 | `apply/test_apply_executor.py` | A create without a natural ID classifies as indeterminate. |
| TST-18 | `apply/test_apply_executor.py` | Each action logs an info line before and a debug line after. Logs hold no payload value and no secret. |
| TST-19 | `apply/test_apply_executor.py` | The operation record passes a read-back before success is reported. |
| TST-20 | `apply/test_apply_reconcile.py` | Verified only when approved fields and unrelated fields match. |
| TST-21 | `apply/test_apply_reconcile.py` | A partial operation reconciles with read calls only. |
| TST-22 | `apply/test_apply_reconcile.py` | An indeterminate create reconciles to one natural ID. |
| TST-23 | `apply/test_apply_reconcile.py` | Objects after a stop receive the outcome `not-applied`. |
| TST-24 | `apply/test_apply_routes.py` | Missing or wrong `APPLY` returns HTTP 400 and makes zero writes. |
| TST-25 | `apply/test_apply_routes.py` | A stale approval returns HTTP 409. |
| TST-26 | `apply/test_apply_routes.py` | Responses carry `Cache-Control: no-store`, the scope summary for a draft, and no payload value. |
| TST-27 | `apply/test_apply_gates.py` | A second run for one scope is refused while the scope lock is held. |
