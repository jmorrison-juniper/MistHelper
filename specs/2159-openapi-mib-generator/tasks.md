---

description: "Task list for the OpenAPI MIB Generator"
---

# Tasks: OpenAPI MIB Generator

**Input**: Design documents from `specs/2159-openapi-mib-generator/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/cli.md`

**Tests**: The specification asks for tests. Each code task therefore carries a test task beside it.
The repository gate in `pyproject.toml` is `fail_under = 90`, so the test task is not optional.

**Organization**: The tasks are grouped by user story. Each story is a complete increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task shares no file with another task that can run at the same time.
- **[Story]**: The user story the task serves.
- Each task names the exact file it creates or changes.

## Repository rules that bind every task

- Class-based design. No wrapper function.
- At most 5 parameters, 5 blocks, and 25 lines in a function.
- An inline comment on every executable line.
- One log line before an action and one log line after it, under the prefix `MIB_GENERATOR:`.
- Simplified Technical English in every docstring, comment, and Markdown file.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Make the package skeleton and the data folder that every later task writes into.

- [X] T001 Create the package folder and the package docstring in `src/mib_generator/__init__.py`. The docstring names the five modules and it exports the nine class names.
- [X] T002 [P] Create the empty data folder marker `data/mib_generator/.gitkeep`, so the two JSON files have a home before they exist.
- [X] T003 [P] Create the test package marker `tests/unit/mib_generator/__init__.py`.
- [X] T004 [P] Add the coverage source path `src/mib_generator` to the `[tool.coverage.run]` section of `pyproject.toml`, so the 90 percent gate counts the new package.
- [X] T005 [P] Create the hand-written 60-line OpenAPI fixture at `tests/unit/mib_generator/fixtures/mini_openapi.json`. It holds one GET operation, one `allOf` schema, one `oneOf` schema with a discriminator, one `anyOf` schema, one nullable field, one self `$ref`, and one empty schema.

**Checkpoint**: The package imports and the fixture is ready.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The document reader and the schema walker. Every user story reads through these two
modules, so no story can start before this phase ends.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Implement the `OpenApiDocument` class in `src/mib_generator/document.py`, with the methods `load`, `get_operation`, `response_schema`, and `resolve`. `load` reads the JSON in one `json.load` call (research R1), it raises on invalid JSON with the path and the error position, and it raises when the `openapi` field is not `3.1.x` (FR-006).
- [X] T007 Add the `$ref` depth limit of 12 to `OpenApiDocument.resolve` in `src/mib_generator/document.py`. At the limit the walk stops, it logs the reference chain it cut, and it returns the partial schema (FR-003, research R4).
- [X] T008 Write the unit tests for T006 and T007 in `tests/unit/mib_generator/test_document.py`. The tests cover a good parse against `fixtures/mini_openapi.json`, a rejected bad JSON file, a rejected non-3.1 version, a missing `operationId`, and a self `$ref` that stops at the limit and writes the log line.
- [X] T009 Implement the frozen `FieldRecord` dataclass with slots in `src/mib_generator/schema.py`, with the six fields of data-model 1.1 and the validation that `path` is non-empty and `json_type` is one of the four names.
- [X] T010 Implement the `SchemaFlattener` class with the method `flatten` in `src/mib_generator/schema.py`. It joins `allOf`, `oneOf`, and `anyOf` as a union of property sets in branch order, it records the branch on each record, it logs a second definition of a property, it reads the 3.1 nullable form as the first non-null type, and it emits no record for an object or an array (FR-004, FR-005, FR-031, research R2, R3).
- [X] T011 Write the unit tests for T009 and T010 in `tests/unit/mib_generator/test_schema.py`. The tests cover `allOf`, `oneOf` with a discriminator, `anyOf`, the empty schema of the `stats_device` shape, the nullable form, a skipped array of objects, a skipped nested object, and the branch name on each record.

**Checkpoint**: The document reads and the schema flattens. The user stories can start.

---

## Phase 3: User Story 1 - Generate the MIB from the OpenAPI file (Priority: P1) 🎯 MVP

**Goal**: A run against the repository OpenAPI file writes an SMIv2 MIB that Net-SNMP loads without
an error.

**Independent Test**: Run `python MistHelper.py --mib-generate`. Load the output with
`snmptranslate -Tp -m <file>`. The command exits 0 and it prints the object names.

### Implementation for User Story 1

- [X] T012 [US1] Implement the `AllowList` class with the methods `load`, `entries`, and `validate` in `src/mib_generator/assignment.py`. `validate` stops the run when an `operationId` is missing from the document or when the operation is not a GET, and the message names the offender (FR-011).
- [X] T013 [P] [US1] Create the default allow list at `data/mib_generator/allowlist.json`, with the three entries `getOrgStats`, `listOrgSiteStats`, and `listOrgDevicesStats` of data-model section 2 (FR-009).
- [X] T014 [P] [US1] Create the JSON Schema of the allow list at `specs/2159-openapi-mib-generator/contracts/allowlist.schema.json`, so a review can validate the file.
- [X] T015 [US1] Write the unit tests for T012 and T013 in `tests/unit/mib_generator/test_assignment.py`. The tests cover a good load of the default file, a missing `operationId`, and a non-GET operation.
- [X] T016 [US1] Implement the `SnmpTypeMapper` class with the methods `syntax_for` and `units_for` in `src/mib_generator/mib.py`, following the eight rows of the data-model type table in the stated order. The catalog `MetricDefinition` wins over the `FieldRecord` on every conflict (FR-026 to FR-030).
- [X] T017 [US1] Write the unit tests for T016 in `tests/unit/mib_generator/test_mib.py`. Each JSON type gives the stated SNMP type, a counter gives `Counter64`, a ratio at scale 10000 gives `Gauge32` with the unit `ten-thousandths`, and a duration at scale 1000 gives `Gauge32` with the unit `milliseconds`.
- [X] T018 [US1] Implement the `MibWriter` class with the method `render` in `src/mib_generator/mib.py`. It writes the `MODULE-IDENTITY`, the four subtrees, a scalar at `<base>.<subtree>.<column>.0`, a table cell at `<base>.<subtree>.1.<column>.<row>` with no extra level, the `INDEX` clause of each table, the row identity column 99, and a `DESCRIPTION` on every object (FR-018, FR-019, FR-035, FR-036, FR-037).
- [X] T019 [US1] Add the `STATUS obsolete` branch and the scale sentence of the `DESCRIPTION` to `MibWriter.render` in `src/mib_generator/mib.py`. The sentence reads `SNMP reports ten-thousandths.` for a ratio (data-model 4.1, FR-023).
- [X] T020 [US1] Extend `tests/unit/mib_generator/test_mib.py` for T018 and T019. The tests read the rendered text and assert the table depth, the `INDEX` clause, the identity column, the obsolete status, and the scale sentence.
- [X] T021 [US1] Implement the `MibGeneratorRunner` class with the method `generate` in `src/mib_generator/runner.py`. It takes the four paths of `contracts/cli.md`, it reads no file in the constructor, it orders the steps, it logs one line before and one line after each step, and it returns the object count. `dry_run` writes no file (FR-041).
- [X] T022 [US1] Write the unit tests for T021 in `tests/unit/mib_generator/test_runner.py`. The tests cover the object count, the log lines, and that `--dry-run` leaves the output path untouched.
- [X] T023 [US1] Add the three flags `--mib-generate`, `--mib-dry-run`, and `--mib-output` to the service flag group of `MistHelper.py`, in the pattern that `--metrics-snmp` already uses.
- [X] T024 [US1] Add the handler `_run_mib_generator_mode` to `MistHelper.py` and add its row to the `mode_table` tuple of `_dispatch_main_mode`, placed after `--metrics-snmp`.
- [X] T025 [US1] Add menu entry `243` to the menu dict of `MistHelper.py`, through `lambda: _run_mib_generator_menu()`, with the label of `contracts/cli.md` section 3.
- [X] T026 [P] [US1] Add the registry row `"243": {"category": "safe"}` to `OperationRegistry._REGISTRY` in `src/utils/operation_registry.py`.
- [X] T027 [US1] Write the unit test of the operator interface in `tests/unit/mib_generator/test_cli_wiring.py`. It asserts the three flags parse, the mode table holds the row after `--metrics-snmp`, the menu holds entry 243, and the registry holds the safe category.
- [X] T028 [US1] Add the contract test `tests/contract/test_mib_parses_with_snmptranslate.py`. It calls `snmptranslate -Tp -m` on the generated MIB and it carries `@pytest.mark.skipif(shutil.which("snmptranslate") is None, ...)`, so the Windows gate stays green (research R9).

**Checkpoint**: A run writes a MIB and Net-SNMP loads it. This is the MVP.

---

## Phase 4: User Story 2 - Keep every OID stable across runs (Priority: P1)

**Goal**: A field that stays keeps its number across every run. A removed field keeps its number
reserved.

**Independent Test**: Run the module twice, with one field added and one field removed between the
runs. Every kept object holds its first number.

### Implementation for User Story 2

- [X] T029 [US2] Implement the `DescriptorMaker` class with the method `make` in `src/mib_generator/assignment.py`, following the eight steps of data-model section 5 and the collision rule of section 5.1. A 100th collision stops the run (FR-032, FR-034).
- [X] T030 [US2] Extend `tests/unit/mib_generator/test_assignment.py` with the Hypothesis property tests for T029. The strategy feeds random text, Unicode, a digit at the front, and a name past 64 characters. The tests assert the three SMIv2 rules and that no two names collide across a random field set.
- [X] T031 [US2] Implement the `OidLedger` class with the methods `load`, `validate`, `claim`, `entries`, and `save` in `src/mib_generator/assignment.py`. The key is `<scope>/<path>` and never the descriptor. `claim` hands out the lowest free column in the band 1 to 89 and it never enters the reserved band 90 to 98 (FR-021, FR-022, research R7).
- [X] T032 [US2] Add the six stop conditions of data-model 3.2 to `OidLedger.validate` in `src/mib_generator/assignment.py`. The check that `base_oid` equals `DEFAULT_BASE_OID` of `src/metrics_gateway/snmp.py` is one of them (FR-017, FR-024).
- [X] T033 [US2] Extend `tests/unit/mib_generator/test_assignment.py` for T031 and T032. A Hypothesis test adds and removes fields in a random order across 100 runs and asserts that no kept field changes its number (SC-005). Unit tests cover each of the six stop conditions.
- [X] T034 [US2] **Seed the OID ledger** at `data/mib_generator/oid_assignments.json` from `src/metrics_gateway/catalog.py`. Copy the subtree and the column of each of the 35 live readings, and copy the descriptor of each one from `documentation/mibs/MISTHELPER-MIB.mib`. Sort the file by subtree and then by column.

  **Proof that no number moved**: add the check to `tests/contract/test_mib_matches_catalog.py`. The check reads the 35 `OBJECT-TYPE` names and their full OIDs from the hand-written MIB that git holds at `HEAD`, it reads the same pairs from the seeded ledger joined with `DEFAULT_BASE_OID`, and it asserts the two sets are equal, name for name and number for number. A single difference fails the test and names the offending pair. The task is not done until this check passes on all 35.

- [X] T035 [P] [US2] Create the JSON Schema of the ledger at `specs/2159-openapi-mib-generator/contracts/oid-assignments.schema.json`.
- [X] T036 [US2] Add the obsolete branch to `MibGeneratorRunner.generate` in `src/mib_generator/runner.py`. A ledger entry that the catalog no longer names is emitted with `STATUS obsolete`, and its number is never given away.
- [X] T037 [US2] Extend `tests/unit/mib_generator/test_runner.py` for T036 and FR-025. Two runs on one input give the same bytes, except the `LAST-UPDATED` value, and a removed field appears with the obsolete status and its old number.

**Checkpoint**: Every OID is stable and the ledger holds the promise.

---

## Phase 5: User Story 3 - Change the endpoint selection without a code change (Priority: P2)

**Goal**: An operator adds an endpoint by editing the allow list only.

**Independent Test**: Add one `operationId` to `data/mib_generator/allowlist.json`. Run the module.
The MIB holds the objects of that endpoint, and no source file changed.

### Implementation for User Story 3

- [X] T038 [US3] Implement the `report` method of `MibGeneratorRunner` in `src/mib_generator/runner.py`. It finds a candidate by `/stats` in the path or `Stats` in a tag, it counts the columns each one would add, it sorts by that count, it marks a selected candidate, and it writes no file (FR-010).
- [X] T039 [US3] Extend `tests/unit/mib_generator/test_runner.py` for T038. The test asserts the sort order, the selected marker, the summary line, and that no file was written.
- [X] T040 [US3] Add the `--mib-report` flag to `MistHelper.py` and route it through `_run_mib_generator_mode`.
- [X] T041 [US3] Extend `tests/unit/mib_generator/test_cli_wiring.py` for T040. The test asserts the flag parses and it reaches the `report` method.

**Checkpoint**: An operator can change the selection with no code change.

---

## Phase 6: User Story 4 - Move from the hand-written MIB (Priority: P2)

**Goal**: The generated MIB replaces the hand-written MIB, and every live poller keeps working.

**Independent Test**: Compare the object list of the hand-written MIB with the object list of the
generated MIB. Each of the 35 names and each of the 35 OIDs matches.

### Implementation for User Story 4

- [X] T042 [US4] Implement the `check` method of `MibGeneratorRunner` in `src/mib_generator/runner.py`. It joins the OpenAPI file, the catalog, and the MIB three ways, it stops on a catalog field that the schema lost, it reports an OpenAPI field the catalog lacks without emitting it, it skips the check for a catalog entry with an empty `source`, and it returns the drift lines (FR-015, FR-016, research R5).
- [X] T043 [US4] Extend `tests/unit/mib_generator/test_runner.py` for T042. The tests cover a clean check that returns an empty tuple, a lost catalog field that stops the run and names the metric and the path, an extra OpenAPI field that is reported and not emitted, and a derived reading with an empty `source` that is emitted from `help_text`.
- [X] T044 [US4] Add the `--mib-check` flag to `MistHelper.py`, route it through `_run_mib_generator_mode`, and exit non-zero on a drift.
- [X] T045 [US4] **Move** `tests/unit/metrics_gateway/test_mib_matches_catalog.py` to `tests/contract/test_mib_matches_catalog.py` with `git mv`, so the history follows the file. Leave the assertions unchanged. Fix only the import path and the fixture path that the new location needs. Delete no test.
- [X] T046 [US4] Add the two new checks to `tests/contract/test_mib_matches_catalog.py`: the regression check that the 35 hand-written names and OIDs survive, and the check that the MIB holds no object that `OidTree` does not answer (SC-004, SC-006).
- [X] T047 [US4] **Regenerate `documentation/mibs/MISTHELPER-MIB.mib`** from the new module. Run `python MistHelper.py --mib-generate`. Add the header comment that tells a reader the file is generated and that a person must not edit it. Add the revision history entry that records the fix of the table depth defect.

  **Proof**: run `python -m pytest tests/contract -v` and show every contract test passes, including the `snmptranslate` test in a Linux shell where Net-SNMP is present. Then load the file in the running Observium container with `docker exec <observium> ./scripts/add_mib.php` and run `snmptranslate -On -m ./documentation/mibs/MISTHELPER-MIB.mib -M ./documentation/mibs MISTHELPER-MIB::mistDeviceReceivedBytes`. The result must read `.1.3.6.1.4.1.11.2147483646.3.1.11` and not `.1.3.6.1.4.1.11.2147483646.3.1.1.11`. Paste both outputs into the pull request.

- [X] T048 [US4] Add the `--mib-check` step to the CI workflow file under `.github/workflows/`, so a drift fails the build (FR-039, SC-008).
- [X] T049 [P] [US4] Record in `CHANGELOG.md` that the MIB is generated and that a person must not edit it by hand again.

**Checkpoint**: The hand-written MIB is gone and CI guards the drift.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T050 [P] Add the performance test to `tests/unit/mib_generator/test_runner.py`, marked `slow`. It measures a full generate run with `tracemalloc` and it fails above 30 seconds or above 1 GB (SC-007).
- [X] T051 [P] Write the operator guide at `documentation/mib_generator.md`. It states the three actions, the two data files, and the rule that a person must not edit the MIB.
- [X] T052 Fill the coverage gaps of `src/mib_generator/` until the run reaches 90 percent. Run `python -m pytest tests/unit/mib_generator --cov=src/mib_generator --cov-report=term-missing` and close every missing line.

---

## Phase 8: Quality Gates

**Purpose**: Every gate must exit 0 before the pull request opens. Run them in this order, because an
earlier gate rewrites the file that a later gate reads.

- [X] T053 Run `python -m ruff check src/mib_generator tests/unit/mib_generator tests/contract` and fix every finding.
- [X] T054 Run `python -m black src/mib_generator tests/unit/mib_generator tests/contract` and then `python -m black --check` on the same paths.
- [X] T055 Run `python -m mypy src/mib_generator` and fix every type error. No `type: ignore` without a stated reason.
- [X] T056 Run `python -m pytest tests/unit/mib_generator tests/contract --cov=src/mib_generator --cov-report=term-missing` and prove coverage reaches 90 percent.
- [X] T057 Run `python -m pylint src/mib_generator` and reach a score of 9.5 or better.
- [X] T058 Run `python -m radon cc src/mib_generator -nc` and prove no block passes complexity 10.
- [X] T059 Run `python -m vulture src/mib_generator` and remove every dead name it finds.
- [X] T060 Run `python -m pydocstyle src/mib_generator` and fix every docstring finding.
- [X] T061 Run `python -m interrogate -v src/mib_generator` and reach 90 percent docstring coverage.
- [X] T062 Run `python -m bandit -r src/mib_generator` and clear every finding.
- [X] T063 Run the STE linter over every changed Markdown file and every changed Python file: `python -m tools.ste_linter src/mib_generator tests/unit/mib_generator tests/contract MistHelper.py src/utils/operation_registry.py documentation/mib_generator.md documentation/mibs/MISTHELPER-MIB.mib CHANGELOG.md specs/2159-openapi-mib-generator/tasks.md`. Each file must score 80 or better.
- [X] T064 Walk `specs/2159-openapi-mib-generator/quickstart.md` end to end and record the result of each of the seven scenarios in the pull request.

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 Setup**: no dependency. It starts at once.
- **Phase 2 Foundational**: needs Phase 1. It blocks every user story.
- **Phase 3 US1**: needs Phase 2.
- **Phase 4 US2**: needs Phase 2. T036 and T037 need T021 of US1.
- **Phase 5 US3**: needs Phase 2 and T021.
- **Phase 6 US4**: needs US1 and US2, because T047 regenerates the real MIB from a seeded ledger.
- **Phase 7 Polish**: needs every story.
- **Phase 8 Quality Gates**: needs Phase 7. It is the last phase.

### Task dependencies inside a phase

| Task | Waits for |
|---|---|
| T007 | T006 |
| T008 | T006, T007 |
| T010 | T009 |
| T011 | T009, T010 |
| T012 | T006 |
| T015 | T012, T013 |
| T017 | T016 |
| T018 | T016 |
| T019 | T018 |
| T020 | T018, T019 |
| T021 | T012, T018 |
| T022 | T021 |
| T024 | T023 |
| T025 | T024 |
| T027 | T023, T024, T025, T026 |
| T028 | T021 |
| T030 | T029 |
| T031 | T029 |
| T032 | T031 |
| T033 | T031, T032 |
| T034 | T031, T032 |
| T036 | T021, T034 |
| T037 | T036 |
| T038 | T021 |
| T039 | T038 |
| T041 | T040 |
| T042 | T021, T034 |
| T043 | T042 |
| T044 | T042 |
| T046 | T045, T034 |
| T047 | T036, T042, T046 |
| T048 | T044 |
| T052 | every test task |
| T053 to T064 | T052 |

### Parallel opportunities

- Phase 1: T002, T003, T004, and T005 run together. They touch four different files.
- Phase 3: T013 and T014 run together. They touch a data file and a contract file.
- Phase 3: T026 runs beside T023 to T025, because it changes `src/utils/operation_registry.py` and the others change `MistHelper.py`.
- Phase 4: T035 runs beside any task, because no other task writes `contracts/oid-assignments.schema.json`.
- Phase 6: T049 runs beside T047, because it changes `CHANGELOG.md` only.
- Phase 7: T050 and T051 run together. T050 changes a test file and T051 makes a new document.

**Not parallel, one file each**: T012, T029, T031, and T032 all write `src/mib_generator/assignment.py`. T016, T018, and T019 all write `src/mib_generator/mib.py`. T021, T036, T038, and T042 all write `src/mib_generator/runner.py`. T023, T024, T025, T040, and T044 all write `MistHelper.py`. None of these carries `[P]`.

---

## Parallel Example: Phase 1

```bash
Task: "Create the data folder marker data/mib_generator/.gitkeep"
Task: "Create the test package marker tests/unit/mib_generator/__init__.py"
Task: "Add src/mib_generator to the coverage source list in pyproject.toml"
Task: "Create the OpenAPI fixture tests/unit/mib_generator/fixtures/mini_openapi.json"
```

---

## Implementation Strategy

### MVP first

1. Phase 1 Setup.
2. Phase 2 Foundational.
3. Phase 3 User Story 1.
4. **Stop and validate**: run `--mib-generate --mib-dry-run` and load the output with `snmptranslate`.

### Incremental delivery

1. Setup and Foundational give the reader and the walker.
2. US1 gives a MIB. Validate it.
3. US2 gives the stable number. Validate it with the seed proof of T034.
4. US3 gives the operator control. Validate it with one added `operationId`.
5. US4 replaces the hand-written file. Validate it with T047 in the Observium container.
6. Polish and the quality gates close the change.

### Notes

- A `[P]` task shares no file with another task that can run at the same time.
- Commit after each task or after a logical group.
- The test task sits beside the code task it covers, because the gate needs 90 percent coverage.
- T034 and T047 both carry a stated proof. Do not mark either one done without that proof.
