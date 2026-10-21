---
description: "Bounded first-batch implementation tasks for issue 2753"
---

# Tasks: Code Defaults First Batch

**Input**: `specs/numbered/0/0/0/4/2/0/0/3/2753-code-defaults-first-batch/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research](design/research.md),
[data model](design/data-model.md), [audit contract](design/contracts/audit.md), and [validation guide](design/quickstart.md).

**Tests**: Required. Write defect tests before repairs and retain evidence that the tests fail against the original behavior.
For already repaired or valid behavior, preserve the passing case and prove the assertion detects a controlled mutation.

**Organization**: User stories define the verification boundaries.
File repair order follows historical high-severity counts: AP migration, zones, CSV comparison, addresses, then organization migration.
Do not absorb sibling ownership, the 99 deferred upgrade-input candidates, or any other file's behavior.

## Format: `[ID] [P?] [Story] Description`

Mark a task complete only after verifying its output.
Append `(delivered: path)` and evidence when completed.
Keep a blocked row unchecked and state the exact ownership or review dependency.
A blocked row does not prevent unrelated approved rows from proceeding.

## Phase 1: Setup

- [X] T001 Inspect `git status --short` and the complete paginated open-PR file list before editing the five source paths in `spec.md`. Record overlap decisions in `design/research.md` (delivered: `design/research.md`; 11 open PRs, 553 file records, no overlap).
- [X] T002 Confirm Python 3.13 and bootstrap the worktree through `scripts/bootstrap_worktree.py` if its environment is absent. Record tool limitations in `design/quickstart.md` (delivered: `design/quickstart.md`; Python 3.13.13, bootstrap exit 0, 162 package records checked, 0 corrupt).
- [X] T003 Inspect touched-block structure and existing public names in the five source files listed in `spec.md`. Record local debt and the exact bounded file manifest in `design/research.md` (delivered: `design/research.md`; recorded top-level declaration counts and the approved file manifest).

## Phase 2: Foundational Classification

- [X] T004 Reconcile the 59 historical review targets from assessment section 8 against current source. Record current consumer contracts and dispositions in `design/research.md`. Do not invent a current count. (delivered: `design/research.md`; reconciled all 59 by original line and recorded the measured current scan separately)
- [X] T005 Record required, optional, already-validated, display-only, and excluded-ownership decisions in `design/data-model.md`. Apply: “A candidate is not automatically a confirmed defect.” Keep #2862 and sibling decisions excluded. (delivered: `design/data-model.md`; #2862 excluded and #2863 ownership retained)
- [X] T006 Add isolated Git and external-response fixtures in `tests/integration/helpers/code_defaults/test_inventory.py` and `tests/integration/helpers/code_defaults/test_workflows.py`. Prevent network access and use `tmp_path`. (delivered: both test modules; temporary Git repositories, mocked responses, no external requests)

**Checkpoint**: Classification evidence identifies confirmed defects and preserved optional contracts.
Scanner discovery can proceed independently, but baseline acceptance waits for reviewed current dispositions.

## Phase 3: User Story 1 - Reject Missing Operational Inputs (Priority: P1)

**Goal**: Stop invalid migration inputs before dependent actions and preserve completed records.

**Independent Test**: Missing identities or required collections fail visibly. Valid mocked workflows retain their results and confirmations.

### Tests First

- [X] T007 [US1] Add failing AP migration cases in `tests/unit/device/test_ap_profile_migration_manager.py` for confirmed missing required inputs. Cover absent, null, blank, whitespace-only, wrong-type values, and valid empty collections. (delivered: `tests/unit/device/test_ap_profile_migration_manager.py` and `tests/integration/helpers/code_defaults/test_workflows.py`; failing-before evidence saved in session artifacts)
- [X] T008 [P] [US1] Preserve and extend created-object identity regression cases in `tests/unit/org/test_org_config_migration_conflicts.py` and `tests/unit/org/test_org_config_migration_workflow.py`. Prove “Earlier completed records remain intact.” Keep this independent test preparation separate from file repair order. (delivered: existing #4310 assertions verified by focused tests and `test_workflows.py` proves prior results remain)

### Implementation

- [X] T009 [US1] Repair confirmed required-input defaults in `src/mist/resources/device/ap_profile_migration_manager.py`. Reuse existing validators and errors. Do not change sibling-owned identities or typed confirmations. Depends on T007. (delivered: `src/mist/resources/device/ap_profile_migration_manager.py`; strict fallback collection and selected profile ID validation)
- [X] T010 [US1] After T016, review the remaining organization candidates in `src/mist/resources/org/org_config_migration_manager.py`. Validate only confirmed required object references. Preserve optional `list_kwargs` and network sections where their contracts permit absence. Preserve #4310 and do not alter organization/site identifier ownership. (delivered: `design/research.md`; no new required-field defect was confirmed, optional sections remain optional, and #2863 identifiers remain excluded)
- [X] T011 [US1] Add local migration caller tests in `tests/integration/helpers/code_defaults/test_workflows.py`. Assert no dependent action after validation failure, no blank mapping, explicit failed rows, and preserved earlier results. Verify T009 and T010. (delivered: `tests/integration/helpers/code_defaults/test_workflows.py`; controlled AP lookup stops before device lookup, and organization failure preserves the earlier row with no mapping)

**Checkpoint**: US1 passes its migration unit and controlled workflow tests.
Do not run an actual migration or recovery operation.

## Phase 4: User Story 2 - Distinguish Missing Data from Valid Empty Results (Priority: P1)

**Goal**: Reject incomplete analysis and comparison inputs without changing permitted blank output.

**Independent Test**: Missing required data differs visibly from valid zero results. Optional display and address components retain behavior.

### Tests and Repairs in File Order

- [X] T012 [US2] Add required-analysis and optional-export cases in `tests/unit/test_zone_analyzer.py`, then repair confirmed defects in `src/mist/intelligence/analytics/zone_analyzer.py`. Require complete analysis only at consumers whose producer contract requires it. Preserve intentional empty reports. Depends on T009. (delivered: `tests/unit/test_zone_analyzer.py` and `design/research.md`; consumer review found no new source defect, and empty-result and export contracts remain covered)
- [X] T013 [US2] Add serial, address, customer-column, and device-object identity cases in `tests/unit/test_csv_comparator.py`, `tests/unit/inventory/test_csv_comparator_broad_handlers.py`, and `tests/unit/refactors/test_inventory_csvcomparator.py`. Demonstrate failures before repairs. Depends on T012. (delivered: the three named test modules; focused tests cover blank serial handling, optional address/customer columns, and failed comparison rows)
- [X] T014 [US2] Repair confirmed comparison-key defaults in `src/mist/resources/inventory/csv_comparator.py`. Do not make display-only `END_CUSTOMER_*` variables required without consumer evidence. Preserve all existing result schemas. Depends on T013. (delivered: `design/research.md`; no new source repair was justified, and display-only customer columns remain optional)
- [X] T015 [US2] Add missing primary address, optional second line, valid empty normalization, and comparison-boundary cases in `tests/unit/test_address_utils.py`. Distinguish permissive helpers from required operational input consumers. Depends on T014. (delivered: `tests/unit/test_address_utils.py`; the missing primary address fails at comparison while optional line 2 and standalone helper behavior remain valid)
- [X] T016 [US2] Repair confirmed defaults in `src/foundation/support/utils/address_utils.py`. Reject required missing comparison values before matching, while preserving optional components and standalone helper contracts. Depends on T015. (delivered: `design/research.md`; the existing comparison boundary already rejects missing required data, so no helper contract changed)
- [X] T017 [US2] Add combined comparison and reporting cases in `tests/integration/helpers/code_defaults/test_workflows.py`. Assert explicit failure, preserved valid results, and unchanged optional display values. Depends on T016 and T011. (delivered: `tests/integration/helpers/code_defaults/test_workflows.py`; mocked address comparison reports a conflict and retains the compared values)

**Checkpoint**: US2 passes independently with controlled inputs. A valid empty collection still reports a legitimate zero.

## Phase 5: User Story 3 - Detect New Unsafe Defaults (Priority: P2)

**Goal**: Deliver deterministic discovery and a guard that fails for regressions or invalid input.

**Independent Test**: Add one unsafe candidate in a temporary tracked repository and observe a failing guard with parsed-file counts.

### Tests First

- [X] T018 [P] [US3] Extend `tests/integration/helpers/code_defaults/test_inventory.py` for the five scan shapes, non-empty defaults, exclusions, deterministic ordering, and line-only movement. Apply: “Line movement alone must not manufacture a new candidate.” Depends on T006. (delivered: `tests/integration/helpers/code_defaults/test_inventory.py`; isolated tracked repositories prove the five shapes, exclusions, stable ordering, empty input, and line-only movement)
- [X] T019 [P] [US3] Add `tests/integration/helpers/code_defaults/test_guardrail.py` cases for added high candidates, count-neutral substitutions, display-only changes, unknown in-scope classification, duplicate identities, invalid totals, unreadable baseline, parse errors, missing scope files, and zero selection. Apply: “Removed candidates produce a visible decrease. They cannot offset a new candidate.” Depends on T005. (delivered: `tests/integration/helpers/code_defaults/test_guardrail.py`; regression, invalid-input, and display-only cases pass, with mutation evidence in the session artifacts)

### Implementation

- [X] T020 [US3] Implement typed candidate discovery in `src/foundation/support/code_defaults/inventory.py` and initialize `src/foundation/support/code_defaults/__init__.py`. Discover tracked files with Git argument lists and parse each selected file once. Apply: “Missing fields, duplicate identities, and unknown classification values invalidate the inventory.” Depends on T018. (delivered: `src/foundation/support/code_defaults/inventory.py` and `__init__.py`; scanner tests pass and current five-file scan parses all five files)
- [X] T021 [US3] Implement reviewed policy and guard decisions in `src/foundation/support/code_defaults/policy.py`. Separate five-file enforcement from repository-wide discovery. Reject unclassified in-scope candidates and never auto-increase the baseline. Depends on T019 and T020. (delivered: `src/foundation/support/code_defaults/policy.py`; guard tests prove identity-level regression detection and exact-scope enforcement)
- [X] T022 [US3] Implement the command contract in `src/foundation/support/code_defaults/__main__.py`: deterministic ASCII JSON, logs on standard error, explicit parsed counts, exit 0 for success, 1 for regression, and 2 for invalid input. Depends on T021. (delivered: `src/foundation/support/code_defaults/__main__.py`; CLI tests cover scan output, regression exit, invalid input, and empty arguments)
- [X] T023 [US3] Create reviewed `src/foundation/support/code_defaults/baseline.json` from the current scanner and completed dispositions. Record criterion version, revision, exact scope, stable identities, evidence, and a verified derived total. Apply: “The historical total of 59 must never be inserted as an unverified current baseline.” Depends on T004, T005, T011, T017, and T022. (delivered: `src/foundation/support/code_defaults/baseline.json`; 197 reviewed dispositions, source revision `ca55339958143c96b60df549ae07b274e89dec2a`, zero accepted high identities)
- [X] T024 [US3] Run scan/guard commands and tests from `design/quickstart.md`. Preserve positive and negative evidence, prove a removed candidate cannot conceal a new candidate, and verify outside-scope findings cannot change the accepted total. Depends on T023. (delivered: session scan, guard, and mutation evidence; repository scan parsed 1,059 files, scoped guard parsed five files, and count-neutral regression tests passed)

**Checkpoint**: The committed scanner and reviewed baseline are reproducible. The guard proves that it can fail.

## Phase 6: Cross-Cutting Verification

- [X] T025 Run the exact eight-module assessment test command and the new package tests in `design/quickstart.md`. Preserve failing-before and passing-after evidence in session artifacts. Do not run the full pytest suite. (delivered: focused test runs and session artifacts; 557 assessment tests and 43 package tests passed)
- [X] T026 Run applicable compile, lint, format, type, complexity, security, symbol, structural, documentation, and quality gates from `design/quickstart.md`. Record exact results and blockers. Do not suppress findings or alter shared baselines. (delivered: `design/quickstart.md`; required gates passed, the extra script-inclusive complexity probe found six out-of-scope functions, and `markdown-link-check` was unavailable)
- [X] T027 Update `design/research.md`, `design/quickstart.md`, and `tasks.md` with verified dispositions, command results, and blocked rows. Confirm FR-001 through FR-012 and SC-001 through SC-007 have evidence. (delivered: the three named artifacts; all functional requirements and success criteria have bounded implementation or exclusion evidence, with no source row blocked)
- [X] T028 Prepare the required unique release-note fragment under `changelog.d/` for issue #2753 and follow its naming policy. Do not edit `CHANGELOG.md`, publish a pull request, close the issue, or start deployment. (delivered: `changelog.d/issue-2753-code-defaults-first-batch.md`; no shared changelog or issue state changed)

## Dependencies & Execution Order

Setup: T001 -> T002 -> T003.
Classification: T003 -> T004 -> T005 -> T006.
US1 test preparation T008 can run alongside T007 after classification.
The scanner tests T018 and T019 can run independently after their listed prerequisites.

Required source repair order:

```text
T007 -> T009 -> T012 -> T013 -> T014 -> T015 -> T016 -> T010
```

Migration integration T011 follows T009, T010, and T008.
Comparison integration T017 follows T016 and T011 because both edit the shared workflow test module.
Scanner implementation T020 -> T021 -> T022 can proceed without changing workflow sources.
Baseline acceptance T023 waits for both story verification and the scanner.
Final verification T024 -> T025 -> T026 -> T027 -> T028 follows all completed independent work.

An ownership-blocked source row remains unchecked.
Complete independent rows, but do not mark baseline acceptance or the whole batch ready if blocked required classifications remain.

## Parallel Examples

US1: T007 and T008 prepare different migration test modules after classification.
Repair organization source only after the higher-count files.

US2: Inspect optional address cases while zone tests run, but perform source repairs in the required count order.
Do not execute two writers against `test_workflows.py`.

US3: T018 and T019 write different scanner test modules.
Keep the baseline writer exclusive until all accepted dispositions are verified.

## Implementation Strategy

The MVP is US1's confirmed migration-input failures, with retained optional behavior and visible failed records.
Deliver US2 as the next behavior increment and US3 as the reproducible regression boundary.
Complete all three for this bounded batch.

Write tests first and preserve their actual failure or controlled-mutation evidence.
Do not use production credentials.
Never convert historical counts into current evidence without scanning and review.
Stop only affected rows for unresolved decisions. Do not resolve #2862 ownership.
