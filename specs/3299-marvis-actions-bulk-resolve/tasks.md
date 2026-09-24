# Tasks: Marvis Actions export and bulk resolve

**Feature**: `3299-marvis-actions-bulk-resolve` | **Issue**: #3299

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md)

Each task names its files. A task marked `[P]` can run beside another `[P]` task
in the same phase, because the two tasks touch no common file.

## Phase 1: Foundation

- [x] **T001** Add the strategies `listOrgMarvisActions` and
  `resolveOrgMarvisActions` to `src/refactors/endpoint_primary_key_strategies.py`.
  Use `natural_pk` on `uuid` and on `result_id`, with the indexes from the plan.
  The constitution requires this entry before any code writes a row. Satisfies
  FR-014 and FR-029.

- [x] **T002** Create the package `src/marvis/actions/` with an `__init__.py` that
  exports `MarvisActionsOperation` and `MarvisCatalog`. Create
  `tests/unit/marvis/__init__.py` and `tests/unit/marvis/actions/__init__.py`.

## Phase 2: User Story 1 -- the report (P1)

- [x] **T003** Write `src/marvis/actions/model.py`. Define the status, category,
  topic, and resolution code catalogs, `ResolutionCode`, `MarvisCatalog`,
  `MarvisFieldReader`, `MarvisActionRecord` with the 43 columns, and
  `MarvisActionRecordBuilder`. Satisfies FR-006, FR-015, and FR-016.

- [x] **T004** `[P]` Write `tests/unit/marvis/actions/test_model.py`. Cover the
  built-in names, the schema fallback name, the swapped schema names, and the field
  readers. Also cover the entity key order for AP Offline, the derived key, and the
  document shape.

- [x] **T005** Write `src/marvis/actions/client.py`. Define `MarvisListResult` and
  `MarvisActionsClient` with `list_actions`, `read_schema`, `read_site_names`, and
  `resolve_action`. Satisfies FR-004 to FR-007 and FR-023.

- [x] **T006** `[P]` Write `tests/unit/marvis/actions/test_client.py`. Cover the
  paging stops, the page guard, the discard after a failed page, and the shape
  guard. Also cover the schema fallback, the site read failure, and the resolve
  body.

## Phase 3: User Story 2 -- the filters (P2)

- [x] **T007** Write `src/marvis/actions/selection.py`. Define `MarvisTopicCount`,
  `MarvisTopicSelector`, `MarvisFilterPrompts`, `MarvisResolveRequest`, and
  `MarvisResolvePrompts`. Satisfies FR-008 to FR-012 and FR-019 to FR-022.

- [x] **T008** `[P]` Write `tests/unit/marvis/actions/test_selection.py`. Cover every
  token form, the number range, the unknown token, and the known token that selects
  nothing. Also cover the open filter, the tables, the code parser, the comment
  rules, and the exact confirmation match.

## Phase 4: User Story 3 -- the bulk resolve (P3)

- [x] **T009** Write `src/marvis/actions/operation.py`. Define
  `MarvisResolveResult`, `MarvisBulkResolver`, `MarvisLoadedActions`,
  `MarvisResolveWorkflow`, and `MarvisActionsOperation`. Satisfies FR-003, FR-013,
  FR-017, FR-018, and FR-024 to FR-030.

- [x] **T010** `[P]` Write `tests/unit/marvis/actions/test_operation.py`. Cover the
  three modes, the empty organization, the no-open path, the filter refusal, and the
  export arguments. Also cover the cap, the stop signal, a run with one HTTP 403,
  and each verification outcome.

- [x] **T011** `[P]` Write `tests/unit/marvis/actions/test_properties.py` with
  Hypothesis. Prove that the token parser and the field readers never raise. Prove
  that the confirmation accepts only the exact text and that the action key is
  deterministic.

## Phase 5: User Story 4 -- the menu and the portal (P4)

- [x] **T012** Add row `"270"` to `src/utils/operation_registry.py` as
  `interactive_safe`, with the WHY comment. Satisfies FR-001 and FR-002.

- [x] **T013** Add the import and the `MenuEntry` row for 270 to `MistHelper.py`.
  Change `EXPECTED_MENU_ENTRY_COUNT` in `tests/unit/test_menu_entry_metadata.py`
  from 269 to 270.

- [x] **T014** Add `(270, 270, "Marvis Actions")` to `CATEGORY_RANGES` and add
  `registry["270"]` with six controls to `web_portal/services/operation.py`. Put
  the block after `registry["209"]`, so it does not overlap pull request #3284.
  Satisfies FR-031 to FR-033.

- [x] **T015** Regenerate `web_portal/menu_registry.py` with
  `python scripts\generate_portal_menu_registry.py`. Regenerate the menu reference
  with `python scripts\generate_menu_wiki.py`.

- [x] **T016** `[P]` Write `tests/guardrails/test_marvis_actions_portal_exposure.py`.
  Prove that the portal admits 270, that the six controls hold the prompt order,
  and that the choice values come from the catalog.

- [x] **T027** Show each line for the operator at the Display level. The constant
  `DISPLAY_LEVEL` in `selection.py` holds `logging.WARNING`, so the SSH console
  shows the tables when `.env` sets `CONSOLE_LOG_LEVEL=30`. Log one progress line
  after each group of 25 resolve requests. Write
  `tests/unit/marvis/actions/test_console_visibility.py`. Follows issue #886.

- [x] **T028** Write `tests/unit/marvis/actions/test_portal_contract.py`. Make
  `tools/prompt_audit.py` find the six prompts of menu 270. Call
  `InputUtils.safe_input` directly in each filter method, and give the workflow
  method the unique name `resolve_open_actions`.

## Phase 6: User Story 5 -- the endpoint report (P5)

- [x] **T017** Write `documentation/marvis-actions-api-endpoints.md`. Copy it to
  `data/Marvis_Actions_API_Endpoints_Report.md` in the served checkout. Satisfies
  FR-034.

- [x] **T018** Update `README.md`, the category table in
  `.github/copilot-instructions.md`, and `deploy/.env.example`. Add
  `changelog.d/issue-3299-marvis-actions.md`. Satisfies FR-035.

## Phase 7: Validation

- [ ] **T019** Run `py_compile`, `ruff`, `black`, `mypy`, `pylint`, `bandit`,
  `radon`, `vulture`, `pydocstyle`, `interrogate`, and `tools.symbol_diff` on the
  changed files. Run the new tests and the menu and portal guardrails.

- [ ] **T020** Prove each new guard with a direct test of the guard decision: the
  confirmation check, the comment check, the cap, and the page guard. Record the
  count of checked cases in the pull request.

- [ ] **T021** Deploy the files into `misthelper-app` with a Class B deploy, and log
  the START line and the DONE line in the coordination log. Start no new container.

- [ ] **T022** Run modes 1, 2, and 3 from the portal with Playwright. Confirm the
  status, the log lines, and the Results panel.

- [ ] **T023** Run modes 1 and 3 over SSH on port 2200. Confirm the tables and the
  messages.

- [ ] **T024** Read `podman logs misthelper-app`, `data/script.log`, and the portal
  error log. File or update an issue for each new problem.

- [ ] **T025** Read `data/OrgMarvisActions.csv` and the ArangoDB collection
  `listOrgMarvisActions`. Compare the counts and three sample rows with the live
  list.

## Phase 8: Delivery

- [ ] **T026** Commit, rebase on `origin/main`, and push. Open the pull request with
  `Closes #3299`, the labels, and the checklist. Wait for every check, including
  CodeQL. Merge with a squash. Remove the worktree and post the DONE line.

## Dependencies

- T001 and T002 come first.
- T003 comes before T005, T007, and T009, because each one reads the catalog.
- T005 and T007 come before T009.
- T012 and T013 come before T015.
- T019 comes before T021. T021 comes before T022 to T025.
- T026 comes last.
