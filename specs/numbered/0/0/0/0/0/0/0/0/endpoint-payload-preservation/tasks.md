---

description: "Implementation tasks for endpoint payload preservation"
---

# Tasks: Endpoint Payload Preservation

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/endpoint-payload-preservation.md`, and `quickstart.md` in this
feature directory.

**Issue**: #3699

**Implementation boundary**: Use only the parent manifest in `plan.md`.
Treat `src/foundation/support/refactors/endpoint_primary_key_strategies.py` as
read-only. Do not change dependencies, schemas, output contracts, or live
Mist Cloud data.

**Test policy**: Tests are required. Write the red regression proof before the
production repair.

## Phase 1: Setup

**Purpose**: Confirm the existing exporter, test, release-note, and validation
surfaces without changing production code.

- [ ] T001 Inspect `src/operations/exporting/export/endpoint_family_exporter.py` and record the current SDK response boundary for issue #3699.
- [ ] T002 [P] Inspect `tests/unit/export/test_endpoint_family_exporter.py` and identify the existing defect-encoding test and its fixture helpers.
- [ ] T003 [P] Inspect `tests/contract/test_mistapi_sdk_compatibility.py` and `tests/guardrails/test_endpoint_catalog.py` for unchanged compatibility and catalog selectors.
- [ ] T004 [P] Inspect `changelog.d/` naming rules and reserve a unique issue-3699 fragment path without editing `CHANGELOG.md`.
- [ ] T005 [P] Record the baseline content hash of `src/foundation/support/refactors/endpoint_primary_key_strategies.py` for the final read-only check.

## Phase 2: Foundational

**Purpose**: Define shared response-shape evidence, count evidence, and safe
logging rules before story work begins.

- [ ] T006 Create local response fixtures in `tests/unit/export/test_endpoint_family_exporter.py` for the literal summary trend object with `start`, `end`, `sle`, and `classifiers`.
- [ ] T007 Create local response fixtures in `tests/unit/export/test_endpoint_family_exporter.py` for the literal classifier trend object with `start`, `end`, `metric`, and `classifier`.
- [ ] T008 [P] Define assertions in `tests/unit/export/test_endpoint_family_exporter.py` for status, operation, endpoint identity, labels, filename, and `api_function_name`.
- [ ] T009 [P] Define safe logging assertions in `tests/unit/export/test_endpoint_family_exporter.py` that reject tokens, passwords, authorization headers, and full credentials.
- [ ] T010 [P] Define received-record and written-record count evidence in `tests/unit/export/test_endpoint_family_exporter.py`, including the incomplete result for a mismatch.

**Checkpoint**: Shared fixtures and evidence rules are ready. The first
production change is still prohibited.

## Phase 3: User Story 1 - Preserve Documented Object Exports (Priority: P1) 🎯 MVP

**Goal**: Preserve each documented SLE trend object as one received record and
write it through the existing normalization and output path.

**Independent Test**: Run the two documented-object tests with local transport
fixtures and verify one received record and one written record for each object.

### Tests for User Story 1

- [ ] T011 [US1] Add the red regression proof in `tests/unit/export/test_endpoint_family_exporter.py` for the summary trend object before changing `src/operations/exporting/export/endpoint_family_exporter.py`.
- [ ] T012 [US1] Add the red regression proof in `tests/unit/export/test_endpoint_family_exporter.py` for the classifier trend object before changing `src/operations/exporting/export/endpoint_family_exporter.py`.
- [ ] T013 [US1] Run `python -m pytest tests/unit/export/test_endpoint_family_exporter.py -k "documented or object or received or written" -q` and record the expected failure caused by `mistapi.get_all` returning zero records for objects without `results`.
- [ ] T014 [US1] Update the existing defect-encoding test in `tests/unit/export/test_endpoint_family_exporter.py` so the documented object loss remains encoded as a failing pre-repair proof and a passing post-repair regression.

### Implementation for User Story 1

- [ ] T015 [US1] Implement the smallest proven-shape branch in `src/operations/exporting/export/endpoint_family_exporter.py` for the documented summary and classifier object shapes only.
- [ ] T016 [US1] Preserve existing normalization, flattening, multiline escaping, output selection, filenames, labels, and `api_function_name` behavior in `src/operations/exporting/export/endpoint_family_exporter.py`.
- [ ] T017 [US1] Verify the two SLE trend operations remain available when deprecated SDK attributes are absent in `tests/unit/export/test_endpoint_family_exporter.py`.
- [ ] T018 [US1] Verify the summary and classifier object paths use existing SDK methods and authentication evidence in `tests/unit/export/test_endpoint_family_exporter.py`.

**Checkpoint**: User Story 1 is independently testable and produces one
written record for each documented non-empty object.

## Phase 4: User Story 2 - Preserve Existing Paginated Exports (Priority: P2)

**Goal**: Keep top-level list and `results` envelope behavior, including valid
following pages, order, request arguments, and endpoint metadata.

**Independent Test**: Run list and `results` fixtures with following pages and
compare received records, order, and writer calls with the existing contract.

### Tests for User Story 2

- [ ] T019 [P] [US2] Extend list pagination coverage in `tests/unit/export/test_endpoint_family_exporter.py` to assert every record and its order across a valid following page.
- [ ] T020 [P] [US2] Extend `results` pagination coverage in `tests/unit/export/test_endpoint_family_exporter.py` to assert every record and its order across a valid following page.
- [ ] T021 [US2] Assert unchanged request arguments, labels, filenames, endpoint URLs, and `api_function_name` in `tests/unit/export/test_endpoint_family_exporter.py`.

### Implementation for User Story 2

- [ ] T022 [US2] Keep list and `results` pagination dispatch unchanged in `src/operations/exporting/export/endpoint_family_exporter.py`.
- [ ] T023 [US2] Keep operation registration and endpoint metadata unchanged in `src/foundation/support/utils/operation_registry.py` and `MistHelper.py`.
- [ ] T024 [US2] Run the full exporter unit selector `python -m pytest tests/unit/export/test_endpoint_family_exporter.py -q` and repair only issue-3699 regressions in `src/operations/exporting/export/endpoint_family_exporter.py`.

**Checkpoint**: User Stories 1 and 2 retain documented object exports and
existing paginated exports independently.

## Phase 5: User Story 3 - Distinguish Empty and Discarded Results (Priority: P2)

**Goal**: Keep true empty responses empty, reject unproven objects, log every
discarded non-empty payload loudly, and expose received-versus-written
mismatches.

**Independent Test**: Run empty, unknown-object, malformed, unsuccessful, log,
and count fixtures and verify the resulting evidence.

### Tests for User Story 3

- [ ] T025 [P] [US3] Add empty list, empty `results`, and empty object assertions in `tests/unit/export/test_endpoint_family_exporter.py` with zero received and zero written records.
- [ ] T026 [P] [US3] Add unknown non-empty object assertions in `tests/unit/export/test_endpoint_family_exporter.py` that reject assumption-based support.
- [ ] T027 [P] [US3] Add unsuccessful and malformed response assertions in `tests/unit/export/test_endpoint_family_exporter.py` that preserve non-raising safe handling.
- [ ] T028 [P] [US3] Add loud discarded-payload assertions in `tests/unit/export/test_endpoint_family_exporter.py` for operation, status, shape, discarded count, and safe reason.
- [ ] T029 [P] [US3] Add received-versus-written count mismatch assertions in `tests/unit/export/test_endpoint_family_exporter.py` that mark the export incomplete.

### Implementation for User Story 3

- [ ] T030 [US3] Limit object preservation to proven response shapes in `src/operations/exporting/export/endpoint_family_exporter.py` and leave unknown non-empty objects discarded.
- [ ] T031 [US3] Add loud ASCII logging for each discarded non-empty payload in `src/operations/exporting/export/endpoint_family_exporter.py` with operation, status, shape class, count, and safe reason.
- [ ] T032 [US3] Add received-record and written-record count checks to the validation path in `src/operations/exporting/export/endpoint_family_exporter.py`, and report a mismatch as incomplete output.
- [ ] T033 [US3] Preserve error handling and secret redaction in `src/operations/exporting/export/endpoint_family_exporter.py` without logging credentials or full payload secrets.
- [ ] T034 [US3] Verify the read-only content hash of `src/foundation/support/refactors/endpoint_primary_key_strategies.py` and leave that file unchanged.

**Checkpoint**: All three user stories distinguish true empty results from
discarded payloads and incomplete writes.

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Record the release note and execute the complete applicable
validation set without changing files outside the requested task surface.

- [ ] T035 [P] Add the issue #3699 changelog fragment in `changelog.d/` using the repository naming and release-note rules.
- [ ] T036 [P] Run `python -m pytest tests/unit/export/test_endpoint_family_exporter.py -q` and record the result for the changed exporter tests.
- [ ] T037 [P] Run `python -m pytest tests/unit/test_pk_strategies.py -q` and record the unchanged key-strategy regression result.
- [ ] T038 [P] Run `python -m pytest tests/guardrails/test_endpoint_catalog.py -q` and record the endpoint catalog result.
- [ ] T039 [P] Run `python -m pytest tests/contract/test_mistapi_sdk_compatibility.py -q` and record the SDK compatibility result.
- [ ] T040 [P] Run `python -m py_compile MistHelper.py` and record the syntax result.
- [ ] T041 [P] Run `python -m ruff check .` for `pyproject.toml` and record the lint result.
- [ ] T042 [P] Run `python -m black --check .` for `pyproject.toml` and record the format result.
- [ ] T043 [P] Run `mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` and record the type result.
- [ ] T044 [P] Run `bandit -c pyproject.toml -r . -q` and `bandit-exclude-check`, then record both security results.
- [ ] T045 [P] Run `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` and record the gate guidance result.
- [ ] T046 [P] Run `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/0/0/0/0/0/0/endpoint-payload-preservation/*.md specs/numbered/0/0/0/0/0/0/0/0/endpoint-payload-preservation/contracts/*.md` and record the documentation result.
- [ ] T047 Verify `git status --short --untracked-files=all` shows only the intended implementation files and the issue #3699 changelog fragment, with no change to `src/foundation/support/refactors/endpoint_primary_key_strategies.py`.
- [ ] T048 Record validation evidence in `specs/numbered/0/0/0/0/0/0/0/0/endpoint-payload-preservation/quickstart.md` only if the implementation run owns that document. Do not change planning documents during task execution without explicit scope.

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1** has no task dependency and identifies the existing file surfaces.
- **Phase 2** depends on Phase 1 and blocks all user story work.
- **User Story 1** depends on Phase 2 and is the MVP.
- **User Story 2** depends on Phase 2 and can run in parallel with User Story 1
  after shared fixtures are ready.
- **User Story 3** depends on Phase 2 and can run in parallel with User Story 2
  after shared count and logging assertions are ready.
- **Phase 6** depends on the completed user stories and the final implementation
  file set.

### User Story Dependencies

- **US1** has no dependency on another user story.
- **US2** has no behavioral dependency on US1. It shares the exporter file and
  must preserve the US1 response boundary.
- **US3** has no behavioral dependency on US1 or US2. Its count and logging
  checks cover all response shapes.

### Critical Ordering

1. Complete T001 through T010.
2. Complete T011 and T012 before T015.
3. Complete T013 and record the red failure before any production repair.
4. Complete T014 before T015.
5. Complete T015 through T018.
6. Complete T019 through T024.
7. Complete T025 through T034.
8. Complete T035 through T048 and record every command result.

## Parallel Opportunities

- Run T002, T003, T004, and T005 in parallel because they inspect different
  files and do not modify them.
- Run T006, T007, T008, T009, and T010 in parallel because they define
  independent fixture and evidence assertions in one owned test file.
- Run T019 and T020 in parallel because they cover separate pagination shapes.
- Run T025, T026, T027, T028, and T029 in parallel because they cover separate
  empty, discard, error, logging, and count cases.
- Run T035 through T046 in parallel after implementation changes stabilize,
  except when a repository gate requires a prior generated environment.

## Parallel Example: User Story 1

```text
Task T011: Add the summary trend red proof in tests/unit/export/test_endpoint_family_exporter.py.
Task T012: Add the classifier trend red proof in tests/unit/export/test_endpoint_family_exporter.py.
Task T013: Run the focused selector and record the expected red result.
Task T014: Update the existing defect-encoding test in tests/unit/export/test_endpoint_family_exporter.py.
```

## Parallel Example: User Story 2

```text
Task T019: Extend top-level list pagination coverage in tests/unit/export/test_endpoint_family_exporter.py.
Task T020: Extend results pagination coverage in tests/unit/export/test_endpoint_family_exporter.py.
Task T021: Assert unchanged dispatch metadata in tests/unit/export/test_endpoint_family_exporter.py.
```

## Parallel Example: User Story 3

```text
Task T025: Test empty response forms in tests/unit/export/test_endpoint_family_exporter.py.
Task T026: Test rejection of unknown objects in tests/unit/export/test_endpoint_family_exporter.py.
Task T028: Test loud discarded-payload logging in tests/unit/export/test_endpoint_family_exporter.py.
Task T029: Test received-versus-written mismatch evidence in tests/unit/export/test_endpoint_family_exporter.py.
```

## Implementation Strategy

### MVP First

1. Complete setup and foundational evidence tasks.
2. Add and run the red summary and classifier object proofs.
3. Repair only the proven object response branch.
4. Run the independent User Story 1 tests.
5. Stop for review if the MVP passes and no pagination or empty-result
   behavior changed.

### Incremental Delivery

1. Add User Story 2 pagination regression coverage and implementation checks.
2. Add User Story 3 empty, discard, logging, and count validation.
3. Add the changelog fragment.
4. Run all targeted selectors and repository gates.
5. Verify the protected key-strategy file and the final file set.

### Completion Criteria

- The first focused object test run records a red regression proof before the
  production repair.
- Both documented object shapes produce one received and one written record.
- The existing defect-encoding test covers the issue regression.
- Unknown object behavior remains evidence-limited.
- Discarded non-empty payloads produce loud safe logs.
- Received and written counts match before completion is reported.
- The changelog fragment exists under `changelog.d/`.
- All listed validation commands have recorded results.
- `src/foundation/support/refactors/endpoint_primary_key_strategies.py` is
  unchanged.
- Every task uses the required checkbox, sequential ID, optional `[P]` marker,
  required story label in story phases, and a file path.
