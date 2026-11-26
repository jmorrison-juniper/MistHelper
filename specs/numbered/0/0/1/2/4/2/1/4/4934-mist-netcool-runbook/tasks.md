# Tasks: NOC runbook for the Juniper Mist to IBM Netcool alarm integration

**Input**: The numeric record `specs/numbered/0/0/1/2/4/2/1/4/4934-mist-netcool-runbook/` holds `spec.md`, `plan.md`, and the `design/` folder.

**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`.

**Tests**: AGENTS.md requires tests for each change. Each code task has a matching test task. The offline document test checks the runbook.

**Organization**: Tasks are grouped by user story. User Story 2 comes before User Story 1, because the live discovery run must finish before the runbook sections that need its facts. Both stories have priority P1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task uses a different file, and it has no dependency on an open task.
- **[Story]**: The user story of the task, from US1 to US5. Setup, foundational, verification, and polish tasks have no story label.
- **[Owner]**: The owner performs the task after the merge. The coordinator does not perform it.
- Each task names its file path, or the process step that it performs. Each task names the FR and SC ids that it satisfies.
- Each code task names the data-model fields or classes that it implements.
- A task that needs a live token or a human decision keeps its box unchecked until the condition is met.

## Path Conventions

- The package is `scripts/netcool_runbook_smoke/`. It holds `__init__.py`, `__main__.py`, `client.py`, `documents.py`, and the `checks/` folder.
- The `checks/` folder holds `__init__.py`, `identity.py`, `catalogs.py`, `searches.py`, and `scope.py`.
- The tests are in `tests/unit/scripts/netcool_runbook_smoke/`. The folder holds five test files and no `__init__.py` file.
- The runbook is `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`.
- Run each Python tool from `.venv\Scripts\` in the worktree. Do not run a bare `python` command.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the package folders, the test folder, and the package docstrings.

- [X] T001 Create the folders `scripts/netcool_runbook_smoke/` and `scripts/netcool_runbook_smoke/checks/`. The file `scripts/netcool_runbook_smoke/__init__.py` holds the package docstring and `__version__ = "1.0.0"`. The file `scripts/netcool_runbook_smoke/checks/__init__.py` holds a docstring only. Create the folder `tests/unit/scripts/netcool_runbook_smoke/` with no `__init__.py` file. (FR-030 to FR-048, SC-007.)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the GET client and the documents module. Each user story uses them.

**Checkpoint**: The client and the documents module pass their tests before any story starts.

- [X] T002 [P] Create `scripts/netcool_runbook_smoke/client.py` with `CallRecord`, `PageSet`, and `ReadOnlyMistClient`. The client sends GET calls only. Implement the fields of `CallRecord` and `PageSet` in `design/data-model.md`, sections 9 and 10. Read the budget from `SmokeSettings.max_requests`, and read the timeout from `SmokeSettings.call_timeout_seconds`. Accept `SmokeSettings.max_retries` from the `--max-retries` option, which has the range 0 to 2 and the default 2. Log each request with structlog: an info event before the call, and a debug event after it. Write each message as a `%s` template with positional values, for example `logger.info("GET %s started", path_label)`. Pass extra context as a keyword argument. Never format a message before the call. Log path labels, never real identifiers. (FR-030, FR-034, FR-038, FR-039, SC-005.)
- [X] T003 [P] Create `scripts/netcool_runbook_smoke/documents.py` with `MarkdownTables`, `RunbookClaims`, `OpenApiIndex`, `EvidenceRedactor`, and `EvidenceWriter`. `RunbookClaims` reads `SmokeSettings.runbook_path`. `OpenApiIndex` reads `SmokeSettings.openapi_path`. `EvidenceWriter` writes the record of `design/contracts/evidence.md`, section 1, to `SmokeSettings.output_path`. The writer uses UTF-8 JSON with sorted keys, and it records the time in UTC ISO 8601 form. `EvidenceRedactor` removes UUID, MAC address, email, and token values, and it cuts each `CheckResult.detail` to 200 characters or fewer. Log each file read and each file write with structlog. (FR-002, FR-041, FR-042, FR-043, FR-044, FR-050, FR-052, SC-003, SC-006.)
- [X] T004 [P] Write `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py` with a fake session object and no network. Cover HTTP 400, 401, 403, 404, 429, 500, and 503. Cover a 429 with a numeric and a non-numeric `Retry-After` value, and a 500 that a 200 follows. Cover connection failure, timeout, malformed JSON, and empty body. Cover a timeout that does not retry. Cover a foreign origin, a port other than 443, a `..` segment, and a backslash in `next`. Cover a repeated page, a page whose `results` hash repeats, the page ceiling, and budget exhaustion. Cover a three-page `next` chain, `limit=1000` on each query, and GET as the only method. Count the login validation as one request. Cover that the client never calls `APISession.login()`. SDK source check: confirm in the mistapi source that a GET call works without `APISession.login()`. (FR-034, FR-035, FR-036, FR-037, FR-039, SC-007.)
- [X] T005 Add the SDK insufficiency test to `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py`. Use a status 400 response that holds an empty list. The client must report an error, and the test must fail when the client reports an empty success. Add boundary tests for both token shapes of task T035 at 19, 20, 31, 32, 39, and 40 characters. (FR-011, FR-039, FR-048, SC-007.)
- [X] T006 [P] Write `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_documents.py` with Markdown and OpenAPI fixtures in `tmp_path`. Cover a valid runbook and four broken variants: a missing heading, a wrong heading order, a path with no GET operation, and a missing table. Cover the Appendix A paths and each Mist API path anywhere in the runbook. Cover the query parameters, `$ref` parameters, and server hosts. Cover a missing input file and a POST-only path. (FR-041, FR-050, FR-052, FR-053, SC-003, SC-007.)
- [X] T007 Add the redaction, allowlist, and writer tests to `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_documents.py`. Cover the redaction of UUIDs, MAC addresses, email addresses, token values, and token-like strings in nested structures. Cover the allowlist, the UTC file name, and the sorted UTF-8 JSON. Cover the 200-character cut of each `CheckResult.detail` value. Cover `tool.version`. The evidence record takes the value of `__version__` from the package, which is `1.0.0`, and it never reads `pyproject.toml` at run time. Write each file under `tmp_path`. (FR-042, FR-043, FR-044, SC-006, SC-007.)

---

## Phase 3: User Story 2 - Verify the runbook and the organization with a read-only smoke test (Priority: P1)

**Goal**: The smoke test checks the runbook facts and one Mist organization. It sends GET requests only.

**Independent Test**: Run the offline document test with no token. Then run the smoke test with one test organization, and read the exit code and the evidence record.

**Purpose**: Build the check modules, the command, and their tests. These tasks run after Phase 2.

- [X] T008 [US2] Define `CheckStatus`, `CheckResult`, `CheckContext`, and `StopRun` in `scripts/netcool_runbook_smoke/checks/__init__.py`. Class `CheckStatus` holds PASS, WARN, INFO, FAIL, and SKIP. Class `CheckResult` implements the fields of `design/data-model.md`, section 11. Class `CheckContext` holds the window start and end, which come from `SmokeSettings.window_minutes` and `SmokeSettings.delay_minutes`. Class `StopRun` carries one outcome class. (FR-040, FR-046, SC-010.)
- [X] T009 [P] [US2] Create `scripts/netcool_runbook_smoke/checks/identity.py` with `IdentityChecks` for SMK-01 to SMK-04. SMK-01 checks `SmokeSettings.org_id`, `SmokeSettings.site_id`, and the file paths. SMK-03 gives PASS only when the role for the organization is `read`. An entry without an `org_id` and without an `msp` scope does not grant the organization. When no entry grants the organization, SMK-03 gives FAIL and the run stops with exit code 2. SMK-04 requests the usage endpoint once for each run. SMK-04 ends the run with the rate-limit stop when `request_limit` minus `requests` is fewer than two times `SmokeSettings.max_requests`. A failed usage request gives WARN, and the run continues. (FR-031, FR-032, FR-038, FR-040, FR-045.)
- [X] T010 [P] [US2] Create `scripts/netcool_runbook_smoke/checks/catalogs.py` with `CatalogChecks` for SMK-05. The check compares each Appendix B name with the `key` of its live catalog. The check fills `CheckResult.field_names` with the catalog fields that it confirms. The evidence keeps each catalog item without its `example` member, as in `design/contracts/evidence.md`, section 5. A missing name gives FAIL, and the detail names the missing value. (FR-040, FR-041, SC-004.)
- [X] T011 [P] [US2] Create `scripts/netcool_runbook_smoke/checks/searches.py` with `SearchChecks` for SMK-06 and SMK-07. SMK-06 reads `PageSet.record_count`, `PageSet.pages_read`, and `PageSet.stop_reason`. SMK-06 checks the identifier fields only when the query returned records. SMK-06 records observation `q8`. The observation holds the distinct values of the enumerated fields, and no identifier. The OpenAPI file lists `open` and `resolved` as the values of `alarm_status`. SMK-07 compares the `total` of the alarm and system event searches with the sum of their `count` values. SMK-07 compares device events only when the device event search is complete, as `PageSet.complete` shows. SMK-07 gives INFO for Mist Edge events, because their responses hold no `total`. (FR-011, FR-035, FR-039, FR-040, FR-048, SC-005.)
- [X] T012 [P] [US2] Create `scripts/netcool_runbook_smoke/checks/scope.py` with `ScopeChecks` for SMK-08 and SMK-09, and `InventoryChecks` for SMK-10. Read the response shape of `/api/v1/orgs/{org_id}/mxedges` in the OpenAPI file before you write SMK-10. SMK-08 uses `SmokeSettings.site_id`, or the first site when that value is empty. SMK-09 sends six requests, and it fills `CheckResult.http_statuses` in call order. SMK-09 sends one probe with `limit=5000`, the only request above 1000. SMK-09 gives WARN for a filter that returns zero records, and FAIL for a type outside the filter. SMK-10 sends six requests, and it sums the `count` values of each device type. (FR-009, FR-010, FR-033, FR-040, SC-005.)
- [X] T013 [US2] Create `SmokeSettings` and `SettingsLoader` in `scripts/netcool_runbook_smoke/__main__.py`. Class `SmokeSettings` implements the fields of `design/data-model.md`, section 8, and it uses `SmokeSettings.max_retries`, which the `--max-retries` option sets. Class `SettingsLoader` reads the options, the environment, and the env file with `dotenv_values`, in the order of `design/contracts/smoke-cli.md`, section 2. The loader validates each value before the first request. The loader checks the path options with these rules. The `--output` option resolves under `test-artifacts/` in the repository root. The `--runbook` and `--openapi` options resolve under the repository root. The `--env-file` option resolves outside the repository root, or it equals `<root>/.env`. The repository root is `Path(__file__).resolve().parents[2]`. Each violation gives exit code 2 and states the cause. (FR-031, FR-032, FR-042, FR-045, SC-005.)
- [X] T014 [US2] Create `LogSetup` in `scripts/netcool_runbook_smoke/__main__.py`. Class `LogSetup` configures structlog once, with key-value output to stderr. The processor chain includes `structlog.stdlib.PositionalArgumentsFormatter()`, so each `%s` message template takes positional values. The processor replaces the token value with `[redacted]`, and it removes UUID, MAC address, and email patterns from each event. Class `LogSetup` sets the standard library logger `mistapi` to WARNING for the run. The token value is not a field of `SmokeSettings`, as `design/data-model.md`, section 8, states. (FR-044, FR-047, SC-006.)
- [X] T015 [US2] Create `SmokeCommand` in `scripts/netcool_runbook_smoke/__main__.py`. Class `SmokeCommand` builds the mistapi session only after SMK-01 passes. It counts the login validation as one request. It runs SMK-01 to SMK-10 in order. It maps each outcome class to an exit code from 0 to 6 in `design/contracts/smoke-cli.md`, section 3. It stops the run with exit code 3 at the second Timeout. It logs each unexpected exception, and it returns exit code 6. It writes the evidence record before it exits, when the output path is valid. It records `request_count` and `request_budget` in the evidence record, as `design/contracts/evidence.md`, section 1, defines. It prints the summary line and the outcome line on every run. A run that fails before SMK-01, for example on an invalid option or env file, prints both lines. Its counts are zero, its outcome is the Configuration error, and its exit code is 2. It marks each check that a run stop prevented as SKIP, with a detail such as `not run: rate-limit stop`. Add the `if __name__ == "__main__":` entry point. (FR-032, FR-034, FR-042, FR-045, FR-046, SC-005, SC-010.)
- [X] T016 [P] [US2] Write `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` with a fake client and scripted `CallRecord` and `PageSet` values. Cover PASS, WARN, INFO, FAIL, and SKIP for each check from SMK-01 to SMK-10. Cover the zero-record WARN, the `read` role rule, and the page ceiling WARN. Cover the SMK-03 privilege rule. A privilege with the scope `org` and the `org_id` of the organization gives PASS for the role `read`, and WARN with the role name for each other role. An `msp` privilege gives WARN. When no privilege grants the organization, the check gives FAIL and the run stops with exit code 2. Cover the SMK-09 WARN for zero records, and the SMK-09 FAIL for a type outside the filter. Cover the `not_observed` outcome with the status code for a `limit=5000` probe that does not return HTTP 200. Cover the SMK-07 SKIP for the device event family when its search is incomplete. Cover a failed usage request that gives WARN. Cover a missing catalog name that gives FAIL. Cover the observation keys of `design/contracts/evidence.md`, section 6. Cover observation `q8` of SMK-06, and check that it holds values only, with no identifier. Cover each run stop condition: HTTP 401, a final HTTP 429, and low hourly usage. Cover the second Timeout, the budget, a foreign origin, and a repeated page. (FR-040, FR-041, FR-048, SC-007.)
- [X] T017 [P] [US2] Write the settings tests in `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py`. Cover the settings from arguments, the environment, and the env file. Cover the process environment, which overrides the env file. Cover conflicting token variables, which give exit code 2. Cover the SDK authentication case: a run without a token sends zero requests and gives exit code 2. Cover a missing or bad organization ID, which gives exit code 2. Cover a host outside the OpenAPI `servers` list, which gives exit code 2. Cover an explicit missing runbook, which gives exit code 2. Cover a default missing runbook, which gives SKIP, and the run continues. Cover `SmokeSettings.max_retries` values outside the range 0 to 2, which give exit code 2. Cover an OpenAPI file that cannot be read, which gives exit code 2. Use only the fake token value `fake-token-for-tests`. (FR-031, FR-032, FR-045, SC-005, SC-007.)
- [X] T018 [US2] Add the path validation tests to `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py`. Cover a `..` traversal for each option: `--output`, `--runbook`, `--openapi`, and `--env-file`. Cover an `--output` path outside `test-artifacts/`. Cover an env file inside the repository that is not `<root>/.env`. Cover a missing `--env-file` path, which gives exit code 2. Each case gives exit code 2, sends no request, and writes no file. Use `tmp_path` for each file that a test creates. (FR-032, FR-042, SC-005, SC-007.)
- [X] T019 [US2] Add the redaction and logging tests to `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py`. Verify that the fake token value never appears in stdout, stderr, the structlog output, or the evidence file. Verify that the `LogSetup` processor replaces UUID, MAC address, and email values in each event. Verify that the `mistapi` logger is at WARNING for the run. (FR-044, FR-047, SC-006, SC-007.)
- [X] T020 [US2] Add the exit code tests to `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py`. Cover each exit code from 0 to 6 with a fake session. Cover an unexpected exception that gives exit code 6 and logs the traceback. Cover the summary line on every run, and the evidence file on a failed run. Verify that `Checks examined` counts only the checks that ran. Verify that a SKIP result does not change the exit code. Cover an evidence write failure that gives exit code 2. Cover an internal error with a failed evidence write, which keeps exit code 6 and prints both causes. Cover a connection failure during token validation, which gives exit code 2. Cover a run that fails before SMK-01. It prints both lines with zero counts and exit code 2, and it writes no evidence file when the output path is invalid. Verify that stdout and stderr hold ASCII text only. (FR-042, FR-045, FR-046, SC-007, SC-010.)
- [X] T021 [US2] Run the live discovery smoke test with a read-only token and no runbook. The run uses GET only. Keep the evidence under `test-artifacts/`. This task needs the author's token, so keep the box unchecked until the run. (FR-028, FR-042, SC-004.)
- [X] T022 [US2] Record the answers to the eight observations `q1` to `q8` of `design/contracts/evidence.md`, section 6. Write the full answers to an uncommitted local file. Write the redacted answers in `design/research.md`, which holds the facts for the writers. Replace each Pending live verification mark with its answer. Use the mark Verified (live) only for a fact that the run shows, or remove the claim from the runbook. Keep the box unchecked until T021 completes. (FR-028, SC-004.)

---

## Phase 4: User Story 1 - Configure the Mist to Netcool collection (Priority: P1)

**Goal**: The runbook gives each collection setting, with a value or a placeholder and a verification mark.

**Independent Test**: Read sections 5, 6, 8, and 9 of the runbook. Each setting has a value or a placeholder, and a verification mark.

**Note**: Each task in this phase edits the same runbook file. Run the tasks in order.

- [X] T023 [US1] Write sections 1 to 5 of `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. Include the Overview table and the verification legend. Include the regional host table in section 5.5. (FR-001, FR-002, FR-003, FR-004, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, SC-001.)
- [X] T024 [US1] Write section 6 and Appendix A in `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. Use one subsection for each endpoint family, the definition catalogs, and the webhook topics. Use the fact table of each family. (FR-005, FR-009, FR-010, FR-011, SC-003.)
- [X] T025 [US1] Write sections 7 and 8 in `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. Section 8 covers the schedule, the checkpoint, the overlap, the pagination, the rate-limit budget, the result states, and the deduplication keys. (FR-005, FR-006, FR-007, FR-008, FR-012, FR-013, FR-014, FR-015, SC-009.)
- [X] T026 [US1] Write section 9 and Appendix C in `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. Mark each Netcool item as a proposal, and mark each IBM fact with its vendor verification mark. Use synthetic and redacted examples only. State that the Netcool receiver must require authentication and TLS. (FR-016, FR-017, FR-018, FR-021, FR-055, SC-006.)

---

## Phase 5: User Story 3 - Operate the feed (Priority: P2)

**Goal**: The NOC operator knows whether the feed is healthy. The operator replays a missed window and escalates a fault.

**Independent Test**: Follow each procedure of section 11 on a test feed. Each step shows an expected result.

- [X] T027 [US3] Write section 11 in `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. Cover the start-of-shift check, alarm handling, checkpoint recovery and replay, token rotation, the webhook check, and escalation. Each step shows an expected result. Link each per-alarm runbook in `documentation/noc-runbooks/` with a relative link. An alarm type without a per-alarm runbook follows the generic steps of section 11.3 and the escalation of section 11.7. Add the webhook signature check of FR-056 to section 6.6, and write the same check in section 11.6. (FR-012, FR-013, FR-020, FR-026, FR-027, FR-056, SC-009.)

---

## Phase 6: User Story 4 - Troubleshoot zero results, high volume, and HTTP errors (Priority: P2)

**Goal**: The NOC operator or the integration engineer finds the cause and the next action for each symptom.

**Independent Test**: Follow each symptom row of section 12 on a test organization.

- [X] T028 [US4] Write section 12 in `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. Include the symptom table and the procedure for each symptom. The symptoms are zero results, zero alarms for one organization, high device event volume, HTTP status errors, pagination faults, time faults, and webhook faults. (FR-005, FR-011, FR-026, SC-009.)

---

## Phase 7: User Story 5 - Decide the scope (Priority: P3)

**Goal**: The owners decide the scope of the feed. Each enhancement has its approval status and its owner role.

**Independent Test**: Verify that section 3 and section 15 list each enhancement, its approval status, and its owner role.

- [X] T029 [US5] Add the baseline and enhancement table to section 3 of `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. Each enhancement has its approval status and its owner role. (FR-006, FR-018, FR-019, SC-009.)
- [X] T030 [US5] Write section 10 in `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. Cover the function, the equivalence table, the recommendation, the unattended run, and the mapping to Netcool. (FR-005, FR-006, FR-018, SC-009.)
- [X] T031 [US5] Write section 15 in `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. List each open decision with its owner role. Include the token layout for each organization and for the AP Warning report. (FR-018, FR-029, SC-009.)

---

## Phase 8: Verification

**Purpose**: Complete the runbook, test it offline, and record the live check.

- [X] T032 Write section 13 and section 14 in `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. Section 13 holds the manual checks, the automated smoke test, and the live verification record. The live record holds the UTC date, the tool version, and the request count. The live record holds a table of Check, Status, and Notes. The live record holds a table of Question, Answer, and Evidence for the eight questions. The live record holds no identifier. (FR-003, FR-028, SC-009.)
- [X] T033 Write Appendix B in `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md` with subsections B.1 to B.5. Include B.4 only when the live system event catalog is not empty. Write Appendix D as a glossary of each term and abbreviation of the runbook. Write Appendix E as a revision table with the columns Version, Date, Author, and Change. (FR-002, FR-041, SC-004.)
- [X] T034 Assemble the runbook in `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md` with a table of contents after the Overview table. Verify the heading order against FR-002. (FR-002, FR-052, SC-002.)
- [X] T035 [P] Write `tests/unit/scripts/netcool_runbook_smoke/test_netcool_runbook_document.py` for the offline runbook. Check the headings in the order of FR-002. Check each Mist API path anywhere in the runbook for a GET operation in the OpenAPI file. The path check covers code spans, code blocks, and tables. Check the query parameters. Check the 25 operations of the transport table against the OpenAPI file and the SDK. Accept Appendix B.4 present or absent. Check that the subsections 4.4, 5.4, 5.5, 8.4, 12.2, 12.3, 12.4, and 12.5 exist. Check that section 9 states the receiver requirement of FR-055. Check that sections 6.6 and 11.6 state the signature check of FR-056. Scan for UUIDs, MAC addresses, email addresses, and tokens. Never print a matched value. A token has one of two forms. The first form is the word `Token`, a space, and 20 or more letters or digits. The second form is a run of 40 or more letters or digits, because the runbook holds written text. Print the count of each examined path, identifier, heading, and line. Fail when an input file cannot be read. (FR-049, FR-050, FR-051, FR-052, FR-053, FR-054, SC-003, SC-006, SC-007.)
- [ ] T036 Run the final live smoke test with the runbook at `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. SMK-02 must pass. SMK-05 must run, and it must report PASS for each Appendix B name. A run that has a run stop before SMK-05 does not satisfy SC-004. Record the statuses in section 13 with the UTC date and no identifier. This task needs the author's token, so keep the box unchecked until the run. (FR-028, FR-041, SC-004.)

---

## Phase 9: Polish and Gates

**Purpose**: Run each local gate and each repository check before the commit.

- [ ] T037 [P] Create the changelog fragment `changelog.d/issue-4934-mist-netcool-runbook.md` with one `### Added` heading and one bullet that names issue #4934. Do not edit `CHANGELOG.md` on this branch. (FR-001, FR-040.)
- [ ] T038 [P] Run `ste-linter` in both modes on the runbook, on each changed Markdown file of the feature directory, and on the changelog fragment. Run once with `--no-dictionary`, and once with the licensed dictionary `data/ste_dictionary.json`. Repair each file until it scores 80 or more. (SC-001.)
- [ ] T039 Stage the runbook by explicit path. Then run `markdown-link-check --root . documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md` and `pytest tests/guardrails/test_markdown_links.py`. (SC-002.)
- [ ] T040 [P] Verify each Mermaid diagram in the runbook with the Mermaid lint step of `ci.yml`. (FR-002.)
- [ ] T041 [P] Run Ruff, Black, mypy, Bandit, radon with complexity-gate, pydocstyle, interrogate, vulture, and pylint on `scripts/netcool_runbook_smoke/` and on the five test files. The interrogate floor is 90 percent, and the target for the new package is 100 percent. Repair each finding at its cause. (FR-040, SC-007.)
- [ ] T042 [P] Run `pydoclint --style=google` on each new Python file when `.venv\Scripts\pydoclint.exe` exists. The worktree venv had no `pydoclint.exe` on 2026-11-25. Without that file, report its absence in the pull request, and do not report the gate as passed. (FR-040, SC-007.)
- [ ] T043 [P] Run `.venv\Scripts\python.exe -m py_compile MistHelper.py`. The expected output is empty. (No FR or SC id applies. The change does not edit `MistHelper.py`.)
- [ ] T044 [P] Run `pytest tests/unit/scripts/netcool_runbook_smoke/ --cov=scripts/netcool_runbook_smoke --cov-report=term-missing`. Run the test quality ratchet in `.github/copilot-instructions.md`, and repair each new finding. (SC-007, SC-008.)
- [ ] T045 [P] Review each new Python file for an inline comment on each executable line, as constitution principle VI requires. Review each file for an info event before each action. Review each file for a debug event after each action, as constitution principle VII requires. Repair each gap that the review finds. (FR-044, FR-047.)
- [ ] T046 Run the full `tests/guardrails` suite on this branch and on `origin/main`. The failure list of `origin/main` is the baseline. Compare the failing test identifiers of the two runs, and report each failure that the branch adds. Repair each added failure at its cause. The guardrails include the spec tree guards, the changelog fragment guard, and the markdown links guard. Run both `pytest-chunks` shards that `.github/copilot-instructions.md` lists, and record the summary line of each shard. (SC-008.)
- [ ] T047 Scan the runbook and each committed file for each customer identifier of SC-006. The identifiers are an organization ID, a site ID, a device MAC address, a device serial, and a device name. They also include a site name, a customer name, a customer person name, an email address, and a token. The offline scan checks the pattern classes. The coordinator runs the name scan with a private term list that the repository never holds. After the implementation, a reviewer task updates the Result text of each checklist item in `design/checklists/` with evidence. The reviewer leaves each checkbox unchecked for the owner. (FR-021, FR-022, FR-023, SC-006.)
- [ ] T048 Restore `.specify/feature.json` before the commit. (No FR or SC id applies. The pointer file selects the active feature.)
- [ ] T049 Commit the paths of this feature by explicit name. The commit subject and the pull request title use the Conventional Commits format. Rebase on `origin/main`, and rerun the affected local gates. Push, and open the pull request. Add the labels `feature`, `docs`, and `in-progress`. The pull request body names `Closes #4934`, and it gives the changed-file summary, the local gate results, and the deployment and rollback notes. The change adds a script and documents only, so a rollback is a revert of the squash commit. Wait for CI steps 1 to 8. (FR-001, SC-001, SC-002, SC-008.)

---

## Phase 10: Owner Steps After the Merge

**Purpose**: The owner runs pipeline steps 9 to 12 of constitution principle IV. The coordinator does not run these steps.

- [ ] T050 [Owner] Step 9, squash merge: merge the approved pull request into `main` with one squash commit, after CI steps 1 to 8 pass. Do not push to `main` directly. (Process step. No FR or SC id applies.)
- [ ] T051 [Owner] Step 10, main build: wait for `.github/workflows/container-build.yml` on the merged `main` revision. (Process step. No FR or SC id applies.)
- [ ] T052 [Owner] Step 11, revision check: confirm that the image revision label equals the merged commit SHA. (Process step. No FR or SC id applies.)
- [ ] T053 [Owner] Step 12, deploy and health check: pull the approved image, deploy it, and confirm the container and portal health checks. The change adds no runtime code to the product container. (Process step. No FR or SC id applies.)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. It blocks each user story. Its tasks run first.
- **User Story 2 (Phase 3)**: Depends on Foundational. Its tasks run second. Tasks T021 and T036 need the author's token.
- **User Story 1 (Phase 4)**: Depends on Foundational and on T022, because the runbook uses the live facts.
- **User Stories 3, 4, and 5 (Phases 5 to 7)**: Depend on the runbook sections of Phase 4.
- **Verification (Phase 8)**: Depends on the stories that it covers. T036 runs after T034 assembles the runbook.
- **Polish and Gates (Phase 9)**: Depends on Phase 8.
- **Owner Steps (Phase 10)**: Depends on T049 and on CI steps 1 to 8. The owner runs these steps after the merge.

### User Story Dependencies

- User Story 2 comes first, because the live facts feed the runbook sections.
- User Story 1 starts after T022.
- User Stories 3, 4, and 5 start after the sections of User Story 1.

### Within Each User Story

- Write each code task with its test task in the same change. Confirm that each test fails when its behavior is absent.
- Write the types before the checks, and the checks before the command.
- Write the runbook sections in the order of the outline.

### Parallel Opportunities

- The Foundational code tasks T002 and T003 are [P]. Each one uses its own file. The test tasks T004 and T006 are [P] with them.
- The check modules T009 to T012 are [P]. Each one uses its own file.
- The test tasks T016 and T017 are [P] with the check modules.

## Parallel Example: Foundational

```text
Task: T002 Create client.py
Task: T003 Create documents.py
Task: T004 Write the client tests
```

---

## Implementation Strategy

### MVP First (User Story 2)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3, the read-only smoke test.
3. Run T021 and T022 with the author's token.
4. Stop and verify that the smoke test runs and records the live facts.

### Incremental Delivery

1. Build the foundation (Phases 1 and 2).
2. Build the smoke test (Phase 3), and run the live discovery.
3. Write the runbook sections in Phase 4. Then write the procedures in Phases 5 and 6, and the scope decisions in Phase 7.
4. Complete the verification (Phase 8), then the gates (Phase 9), then the owner steps (Phase 10).

---

## Notes

- [P] tasks use different files and have no dependency on an open task.
- [Story] labels map each task to a user story for traceability.
- [Owner] tasks run after the merge. The owner performs them.
- Keep each checkbox unchecked until you verify the delivered file. Then add the evidence note in this form: `(delivered: path/to/file)`.
- The live tasks T021 and T036 need the author's token. Keep their boxes unchecked until the run.
