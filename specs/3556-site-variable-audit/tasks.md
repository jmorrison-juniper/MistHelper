# Tasks: Site Variable Audit

**Input**: Design documents from `specs/3556-site-variable-audit/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/report-contract.md`, and `quickstart.md`

**Tests**: Tests are required by issue #3556 and the feature specification.
Write each test before the implementation task that makes it pass.

**Organization**: Tasks are grouped so an implementer can commit after each
phase. Each user story remains independently testable with offline fixtures.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: This task can run in parallel with other ready tasks.
- **[Story]**: This label applies only to a user story task.
- Include exact file paths in every task.
- Tick a task only after you verify the delivered file. Add an evidence note
  in this form: `(delivered: path/to/file.py)`.
- If a task needs the integration pull request, keep the box unchecked and
  name the deferred integration condition in the task text.

## Deferred Integration Work

The integration pull request owns these shared files and generated references.
Do not edit them in the feature implementation pull request.

- `MistHelper.py` for Menu 275 registration.
- `src/foundation/support/utils/operation_registry.py` for the safe Menu 275 entry.
- `src/foundation/support/refactors/endpoint_primary_key_strategies.py` for report output keys.
- `README.md` for the operation table and operation count.
- `documentation/menu_reference.md` for generated menu documentation.
- Generated menu API map and generated reference files.
- `web_portal/` generated registry output, if the integration generator changes it.

Record the required values for these files in
`specs/3556-site-variable-audit/wiring.md`.

---

## Phase 1: Setup and Scaffolding

**Purpose**: Create the package and test package that all stories use.

- [X] T001 Create the report package marker in `src/mist/intelligence/reports/site_variable_audit/__init__.py` (delivered: src/mist/intelligence/reports/site_variable_audit/__init__.py)
- [X] T002 [P] Create the test package marker in `tests/unit/reports/site_variable_audit/__init__.py` (delivered: tests/unit/reports/site_variable_audit/__init__.py)
- [X] T003 [P] Create shared offline fixture builders in `tests/unit/reports/site_variable_audit/site_variable_audit_fixtures_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_fixtures_test.py)

**Commit checkpoint**: Commit the package scaffold and offline fixture scaffold.

---

## Phase 2: Foundational Model and Client Contracts

**Purpose**: Define the stable interfaces that block all story work.

**Critical**: No user story implementation can start until this phase is complete.

- [X] T004 Define `TemplateReference`, `VariableTokenUse`, `SiteVariableDefinition`, `MissingVariableFinding`, `SiteVariableSummary`, and `SiteVariableAuditResult` dataclasses in `src/mist/intelligence/reports/site_variable_audit/model.py` (delivered: src/mist/intelligence/reports/site_variable_audit/model.py)
- [X] T005 [P] Define `SiteVariableAuditClient` with injectable `mistapi` callables and paginated fetch reuse in `src/mist/intelligence/reports/site_variable_audit/client.py` (delivered: src/mist/intelligence/reports/site_variable_audit/client.py)
- [X] T006 [P] Define the `SiteVariableAudit` class and no-argument `run()` method seam in `src/mist/intelligence/reports/site_variable_audit/operation.py` (delivered: src/mist/intelligence/reports/site_variable_audit/operation.py)
- [X] T007 [P] Add contract tests for OpenAPI operation IDs and query parameters in `tests/unit/reports/site_variable_audit/site_variable_audit_contract_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_contract_test.py)
- [X] T008 Record the shared-file integration contract and all deferred files in `specs/3556-site-variable-audit/wiring.md` (delivered: specs/3556-site-variable-audit/wiring.md)

**Commit checkpoint**: Commit the dataclass contracts, client seam, operation seam, and wiring contract.

---

## Phase 3: User Story 1 - Find Sites With Missing Variables (Priority: P1)

**Goal**: Report each site and assigned template field that uses a variable not
defined for that site.

**Independent Test**: Run offline tests with a fixture site that lacks
`wan_interface`. Confirm that the operation writes both report datasets and
that the audit row names the site, template, variable, and field path.

### Tests for User Story 1

- [X] T009 [P] [US1] Add a failing test for a missing gateway template variable in `tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py)
- [X] T010 [P] [US1] Add a failing test for `SiteVariableAudit.run()` fixture output with no prompt in `tests/unit/reports/site_variable_audit/site_variable_audit_operation_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_operation_test.py)
- [X] T011 [P] [US1] Add a failing test that the console summary counts distinct sites with findings in `tests/unit/reports/site_variable_audit/site_variable_audit_operation_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_operation_test.py)

### Implementation for User Story 1

- [X] T012 [US1] Implement site and template normalization for assigned gateway templates, network templates, templates, WLANs, and device profiles in `src/mist/intelligence/reports/site_variable_audit/model.py` (delivered: src/mist/intelligence/reports/site_variable_audit/model.py)
- [X] T013 [US1] Implement missing-variable finding creation with deterministic ordering in `src/mist/intelligence/reports/site_variable_audit/model.py` (delivered: src/mist/intelligence/reports/site_variable_audit/model.py)
- [X] T014 [US1] Implement organization reads for sites, templates, WLANs, device profiles, and site variables through installed `mistapi` functions in `src/mist/intelligence/reports/site_variable_audit/client.py` (delivered: src/mist/intelligence/reports/site_variable_audit/client.py)
- [X] T015 [US1] Implement `DataExporter.write_with_format_selection` calls for `SiteVariableAudit.csv` and `SiteVariableSummary.csv` in `src/mist/intelligence/reports/site_variable_audit/operation.py` (delivered: src/mist/intelligence/reports/site_variable_audit/operation.py)
- [X] T016 [US1] Implement the console summary for the distinct missing-site count in `src/mist/intelligence/reports/site_variable_audit/operation.py` (delivered: src/mist/intelligence/reports/site_variable_audit/operation.py)

**Commit checkpoint**: Commit the MVP missing-variable report and its proof tests.

---

## Phase 4: User Story 2 - Trace Variable Use in Templates (Priority: P2)

**Goal**: Find each valid `{{name}}` token at any depth and report the JSON
field path for the string that contains it.

**Independent Test**: Run scanner tests with tokens in nested mappings, lists,
multiple fields, and malformed brace text.

### Tests for User Story 2

- [X] T017 [P] [US2] Add failing tests for nested mapping paths and list index paths in `tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py)
- [X] T018 [P] [US2] Add failing tests for multiple tokens in one string and repeated variable evidence in `tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py)
- [X] T019 [P] [US2] Add failing tests for `{{ name }}` normalization and malformed brace rejection in `tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py)

### Implementation for User Story 2

- [X] T020 [US2] Implement recursive token scanning for dictionaries, lists, and strings in `src/mist/intelligence/reports/site_variable_audit/model.py` (delivered: src/mist/intelligence/reports/site_variable_audit/model.py)
- [X] T021 [US2] Implement variable-name normalization, empty-token rejection, and token names with underscores in `src/mist/intelligence/reports/site_variable_audit/model.py` (delivered: src/mist/intelligence/reports/site_variable_audit/model.py)
- [X] T022 [US2] Implement stable JSON field path formatting with list indexes in `src/mist/intelligence/reports/site_variable_audit/model.py` (delivered: src/mist/intelligence/reports/site_variable_audit/model.py)

**Commit checkpoint**: Commit the token scanner and path evidence tests.

---

## Phase 5: User Story 3 - Summarize Required, Defined, Missing, and Unused Variables (Priority: P3)

**Goal**: Produce one summary row per site with required, defined, missing, and
unused variable counts and names.

**Independent Test**: Run summary tests with a site that has unused variables,
a site with all variables defined, and a site with no assigned templates.

### Tests for User Story 3

- [X] T023 [P] [US3] Add failing tests for unused variable counts and names in `tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py)
- [X] T024 [P] [US3] Add failing tests for a site with all variables defined and zero audit rows in `tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py)
- [X] T025 [P] [US3] Add failing tests for a site with no assigned templates and all defined variables unused in `tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py)

### Implementation for User Story 3

- [X] T026 [US3] Implement `SiteVariableSummary` row creation with deterministic ordering in `src/mist/intelligence/reports/site_variable_audit/model.py` (delivered: src/mist/intelligence/reports/site_variable_audit/model.py)
- [X] T027 [US3] Implement required, defined, missing, and unused variable count logic in `src/mist/intelligence/reports/site_variable_audit/model.py` (delivered: src/mist/intelligence/reports/site_variable_audit/model.py)
- [X] T028 [US3] Implement sorted assigned-template display names and unused variable names in `src/mist/intelligence/reports/site_variable_audit/model.py` (delivered: src/mist/intelligence/reports/site_variable_audit/model.py)
- [X] T029 [US3] Connect summary rows to the operation export path in `src/mist/intelligence/reports/site_variable_audit/operation.py` (delivered: src/mist/intelligence/reports/site_variable_audit/operation.py)

**Commit checkpoint**: Commit the summary report and its proof tests.

---

## Phase 6: Safety, Performance, and Error Behavior

**Purpose**: Prove the operation is read-only, bounded, observable, and clear
when required data is unavailable.

- [X] T030 [P] Add a failing client test that each unique template source is read one time per run in `tests/unit/reports/site_variable_audit/site_variable_audit_client_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_client_test.py)
- [X] T031 [P] Add a failing client test that no `getSiteSetting` or per-site settings callable is used in `tests/unit/reports/site_variable_audit/site_variable_audit_client_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_client_test.py)
- [X] T032 [P] Add failing operation tests for missing organization data and failed Mist reads in `tests/unit/reports/site_variable_audit/site_variable_audit_operation_test.py` (delivered: tests/unit/reports/site_variable_audit/site_variable_audit_operation_test.py)
- [X] T033 Implement one-read-per-endpoint behavior and no per-site settings retrieval in `src/mist/intelligence/reports/site_variable_audit/client.py` (delivered: src/mist/intelligence/reports/site_variable_audit/client.py)
- [X] T034 Implement clear user-facing errors for missing organization data and failed Mist reads in `src/mist/intelligence/reports/site_variable_audit/operation.py` (delivered: src/mist/intelligence/reports/site_variable_audit/operation.py)
- [X] T035 Add ASCII-only `%s` formatted logging before and after each API read, transform, and export in `src/mist/intelligence/reports/site_variable_audit/client.py` (delivered: src/mist/intelligence/reports/site_variable_audit/client.py)
- [X] T036 Add ASCII-only `%s` formatted logging before and after each resolver read, model transform, and export in `src/mist/intelligence/reports/site_variable_audit/operation.py` (delivered: src/mist/intelligence/reports/site_variable_audit/operation.py)

**Commit checkpoint**: Commit the safety, performance, and error behavior proofs.

---

## Phase 7: Documentation and Release Artifacts

**Purpose**: Add the non-shared artifacts that issue #3556 requires on this
branch.

- [X] T037 Update the final wiring manifest with source files, test files, Menu 275 registration values, OperationRegistry values, endpoint primary key strategy values, generated reference commands, validation commands, and deferred integration status in `specs/3556-site-variable-audit/wiring.md` (delivered: specs/3556-site-variable-audit/wiring.md)
- [X] T038 Add the release note fragment for issue #3556 in `changelog.d/issue-3556-site-variable-audit.md` (delivered: changelog.d/issue-3556-site-variable-audit.md)

**Commit checkpoint**: Commit the wiring manifest and release note fragment.

---

## Phase 8: Validation and Acceptance Proof

**Purpose**: Run the smallest gates that prove issue #3556 and the feature
specification. Use only the worktree virtual environment.

- [X] T039 Run syntax validation for the new package with `C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m py_compile src\mist\intelligence\reports\site_variable_audit\client.py src\mist\intelligence\reports\site_variable_audit\model.py src\mist\intelligence\reports\site_variable_audit\operation.py` (passed)
- [X] T040 Run unit tests with `C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m pytest tests\unit\reports\site_variable_audit` (13 passed)
- [X] T041 Run Ruff with `C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m ruff check src\mist\intelligence\reports\site_variable_audit tests\unit\reports\site_variable_audit` (passed)
- [X] T042 Run Black check with `C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m black --check src\mist\intelligence\reports\site_variable_audit tests\unit\reports\site_variable_audit` (passed)
- [X] T043 Run mypy for the new package with `C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m mypy src\mist\intelligence\reports\site_variable_audit --config-file pyproject.toml` (passed)
- [X] T044 Run pydocstyle for the new package with `C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m pydocstyle src\mist\intelligence\reports\site_variable_audit` (passed)
- [X] T045 Prove no per-site settings retrieval by searching for `getSiteSetting` in `src/mist/intelligence/reports/site_variable_audit` and `tests/unit/reports/site_variable_audit` (passed: no `getSiteSetting(` call)
- [X] T046 Prove the spec directory contains `spec.md`, `plan.md`, `tasks.md`, and `wiring.md` in `specs/3556-site-variable-audit/` (delivered)
- [X] T047 Record that the live `MistHelper.py --test` Menu 275 proof is deferred to the integration pull request in `specs/3556-site-variable-audit/wiring.md` (delivered: specs/3556-site-variable-audit/wiring.md)

**Commit checkpoint**: Commit only after all applicable validation tasks pass.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1. It blocks all stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2 and delivers the MVP.
- **User Story 2 (Phase 4)**: Depends on Phase 2. It can proceed after the model seam exists.
- **User Story 3 (Phase 5)**: Depends on Phase 2. It can proceed after summary dataclasses exist.
- **Safety and Performance (Phase 6)**: Depends on User Stories 1 through 3.
- **Documentation and Release Artifacts (Phase 7)**: Depends on the implementation shape from Phases 3 through 6.
- **Validation (Phase 8)**: Depends on all selected implementation and artifact tasks.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational. It is the MVP.
- **User Story 2 (P2)**: Can start after Foundational. It expands scanner proof.
- **User Story 3 (P3)**: Can start after Foundational. It expands summary proof.

### Acceptance Criteria Coverage

- `--test` no prompt and both files under `data/`: T010, T015, T040, T047.
- Token at any depth and inside a list with JSON path: T017, T020, T022, T040.
- Missing site appears in `SiteVariableAudit.csv`: T009, T013, T015, T040.
- Unused variable count and names in summary: T023, T027, T028, T040.
- Templates read one time and no `getSiteSetting`: T030, T031, T033, T045.
- Spec directory holds `spec.md`, `plan.md`, `tasks.md`, and `wiring.md`: T037, T046.
- Ruff, Black, mypy, pydocstyle, and unit tests pass: T040, T041, T042, T043, T044.
- Release note fragment exists: T038.

---

## Parallel Opportunities

- T002 and T003 can run in parallel after T001.
- T005, T006, T007, and T008 can run in parallel after T004 defines shared names.
- T009, T010, and T011 can run in parallel before US1 implementation.
- T017, T018, and T019 can run in parallel before US2 implementation.
- T023, T024, and T025 can run in parallel before US3 implementation.
- T030, T031, and T032 can run in parallel after the client and operation exist.
- T041, T042, T043, and T044 can run in parallel after T039 and T040 pass.

## Parallel Example: User Story 1

```text
Task: "T009 [P] [US1] Add a failing test for a missing gateway template variable in tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py"
Task: "T010 [P] [US1] Add a failing test for SiteVariableAudit.run() fixture output with no prompt in tests/unit/reports/site_variable_audit/site_variable_audit_operation_test.py"
Task: "T011 [P] [US1] Add a failing test that the console summary counts distinct sites with findings in tests/unit/reports/site_variable_audit/site_variable_audit_operation_test.py"
```

## Parallel Example: User Story 2

```text
Task: "T017 [P] [US2] Add failing tests for nested mapping paths and list index paths in tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py"
Task: "T018 [P] [US2] Add failing tests for multiple tokens in one string and repeated variable evidence in tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py"
Task: "T019 [P] [US2] Add failing tests for {{ name }} normalization and malformed brace rejection in tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py"
```

## Parallel Example: User Story 3

```text
Task: "T023 [P] [US3] Add failing tests for unused variable counts and names in tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py"
Task: "T024 [P] [US3] Add failing tests for a site with all variables defined and zero audit rows in tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py"
Task: "T025 [P] [US3] Add failing tests for a site with no assigned templates and all defined variables unused in tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py"
```

---

## Implementation Strategy

### MVP First

Complete Phases 1 through 3 first. This delivers User Story 1 and proves the
operator can find sites with missing variables.

### Incremental Delivery

1. Complete Phase 1 and commit the scaffold.
2. Complete Phase 2 and commit stable contracts.
3. Complete Phase 3 and commit the MVP.
4. Complete Phase 4 and commit scanner evidence.
5. Complete Phase 5 and commit summary evidence.
6. Complete Phase 6 and commit safety and performance proof.
7. Complete Phase 7 and commit the required artifacts.
8. Complete Phase 8 and record validation evidence in the pull request.

### Team Strategy

One implementer can work sequentially by phase. With multiple implementers,
split by story after Phase 2, because each story uses different test cases but
the same model and operation seams.
