# Tasks: Review management and security configuration families

**Input**: `spec.md`, `plan.md`, and the `design/` artifacts in this record.

**Prerequisites**: Issues 4634, 4636, 4637, 4638, and 4640 as listed in `plan.md`. Each task names its own prerequisites below.

**Tests**: Required. Each test task precedes its implementation task (FR-014).

**Organization**: The dependency table controls execution. Tasks that edit the same file run in sequence.

## Format

- `[P]` marks a task that can run in parallel with other `[P]` tasks. The task reads files or edits a file that no other task edits.
- Each task lists its requirement IDs, exact paths, acceptance statement, verification command, and status.
- Status values are open, verified-present, partial, and absent. All tasks start as open.

## Phase 1: Gates and Ownership

- [ ] T001 [P] Confirm the evidence rows E-01 to E-08 against the OpenAPI files.
  - Requirements: FR-002, FR-015
  - Paths: `documentation/mist-api-openapi31yaml.yaml`, `documentation/mist-api-openapi31json.json`, `design/contracts/mist-management-evidence.md`
  - Acceptance: Each pointer in the evidence file shows verified-present, partial, absent, or stale. The JSON twin matches each pointer, or the mismatch is recorded.
  - Verification: `Select-String -LiteralPath "documentation\mist-api-openapi31yaml.yaml" -Pattern "^    remote_syslog:"`
  - Status: open

- [ ] T002 [P] Confirm issue 4636 keeps the converter module in place.
  - Requirements: FR-011
  - Paths: `src/interfaces/portals/cisco_config_converter/conversion.py`, `src/interfaces/portals/cisco_config_converter/models.py`
  - Acceptance: The 4636 record names the same converter module. This change set does not touch `models.py`.
  - Verification: `git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" ls-files src/interfaces/portals/cisco_config_converter`
  - Status: open

## Phase 2: Test First

- [ ] T003 Add the secret, hash, and log tests: TM-03, TM-04, and TM-16.
  - Requirements: FR-006, FR-007, FR-014
  - Paths: `tests/integration/web_portal/cisco_config_converter/management/__init__.py`, `tests/integration/web_portal/cisco_config_converter/management/test_management.py`
  - Acceptance: The three tests exist and fail before T007. The fixtures use synthetic values such as `SYNTHETIC-SECRET-0001`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/management/test_management.py -k "secret or hash or log"`
  - Status: open

- [ ] T004 Add the family, parser-only, indentation, and command tests: TM-01, TM-02, TM-05, TM-06, and TM-07.
  - Requirements: FR-001, FR-003, FR-004, FR-005, FR-008
  - Paths: `tests/integration/web_portal/cisco_config_converter/management/test_management.py`
  - Acceptance: The five tests exist and fail before T007. Each test checks the fixed labels and the absence of command strings.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/management/test_management.py -k "family or source_text or parser or indent or command"`
  - Status: open

- [ ] T005 Add the mapping, model, and registry tests: TM-08 to TM-14.
  - Requirements: FR-002, FR-009, FR-013, FR-015
  - Paths: `tests/integration/web_portal/cisco_config_converter/management/test_management.py`
  - Acceptance: The seven tests exist and fail before T008. Each positive fixture has a negative fixture. The registry test checks each pointer and fixture ID.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/management/test_management.py -k "syslog or snmp or cellular or model or registry"`
  - Status: open

- [ ] T006 Add the regression and no-network tests: TM-15 and TM-17.
  - Requirements: FR-010, FR-012
  - Paths: `tests/integration/web_portal/cisco_config_converter/management/test_management.py`
  - Acceptance: TM-15 blocks sockets for the whole review. TM-17 compares the DNS output with a stored baseline for an input that holds management lines.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/management/test_management.py -k "network or dns_output"`
  - Status: open

## Phase 3: Implementation

- [ ] T007 Implement the review contract in the converter module.
  - Requirements: FR-001 to FR-008, FR-010, FR-014
  - Paths: `src/interfaces/portals/cisco_config_converter/conversion.py`
  - Acceptance: Tests T003 to T006 pass for the families, secrets, parser-only families, and DNS output. The method `IOSDnsConverter.banner_delimiter` replaces `_banner` and keeps its behavior. Each new function holds at most five parameters.
  - Depends on: T006, and task T014 of issue 4640 (D-16).
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/management/test_management.py tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`
  - Status: open

- [ ] T008 Add the verified mapping entries for syslog, SNMP location and contact, and cellular APN.
  - Requirements: FR-002, FR-009, FR-013, FR-015
  - Paths: `src/interfaces/portals/cisco_config_converter/conversion.py`
  - Acceptance: Each entry cites an evidence ID, a pointer, an SDK signature, a positive fixture, and a negative fixture. An entry whose evidence row is not verified-present is absent from the registry.
  - Depends on: T001, T007, and task T012 of issue 4638.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/management/test_management.py -k "syslog or snmp or cellular or registry"`
  - Status: open

## Phase 4: Scope and Documentation Gates

- [ ] T009 [P] Confirm that no shared portal, route, model, or presentation file changes.
  - Requirements: FR-011
  - Paths: `web_portal/app.py`, `web_portal/templates/base.html`, `src/interfaces/portals/cisco_config_converter/routes.py`, `src/interfaces/portals/cisco_config_converter/models.py`, `src/interfaces/portals/cisco_config_converter/presentation`
  - Acceptance: The changed-file list has no entry under these paths.
  - Verification: `git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" diff --name-only origin/main -- web_portal src/interfaces/portals/cisco_config_converter/routes.py src/interfaces/portals/cisco_config_converter/models.py src/interfaces/portals/cisco_config_converter/presentation`
  - Status: open

- [ ] T010 Record the red run before T007 and the green run after T008.
  - Requirements: FR-014
  - Paths: none. The evidence goes in the pull request body.
  - Acceptance: The body holds the collected test count, the failing count before T007, and the passing count after T008.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/management/test_management.py --collect-only -q`
  - Status: open

- [ ] T011 [P] Add one changelog fragment for this change set and confirm that the shared changelog stays unchanged.
  - Requirements: FR-011, D-15
  - Paths: `changelog.d/issue-4639-management-security-families.md` until the pull request exists. After that, rename the fragment to the pull request number pattern `pr-` followed by the number. `CHANGELOG.md` stays unchanged.
  - Acceptance: One new fragment exists under `changelog.d/`. The change list has no entry for `CHANGELOG.md`. No other documentation file changes.
  - Verification: `git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" diff --name-only origin/main -- CHANGELOG.md documentation README.md`
  - Status: open

## Final Tasks

- [ ] T-LOCAL-GATES Run every local gate that applies to the changed files.
  - Requirements: All
  - Paths: The changed files and the Markdown files of this record.
  - Acceptance: Each applicable gate passes with its expected result. Each gate that does not apply names the reason.
  - Verification: The commands in `design/quickstart.md`, section 8.
  - Status: open

- [ ] T-PR Commit with a Conventional Commits message and push the implementation branch.
  - Requirements: All
  - Paths: The changed files.
  - Acceptance: The branch is `feat/4639-management-security-families`. The pull request body contains `Closes #4639`. The body lists each local gate with its result.
  - Verification: `gh pr view --json number,headRefName,body`
  - Status: open

- [ ] T-REMOTE-CI Watch the CI run for the pull request.
  - Requirements: All
  - Paths: None.
  - Acceptance: Each required check reports success.
  - Verification: `gh pr checks --watch` on the implementation branch
  - Status: open

- [ ] T-MERGE Enable auto-merge after remote CI passes and the orchestrator authorizes the merge.
  - Requirements: All
  - Paths: None.
  - Acceptance: Auto-merge is enabled only after both conditions hold. After the merge, the post-merge steps of constitution principle IV run only under orchestrator authorization (R85).
  - Verification: `gh pr view --json autoMergeRequest`
  - Status: open

## Dependencies and Execution Order

| Task | Prerequisites |
| --- | --- |
| T001 | None. Issue 4634 records the evidence rows. |
| T002 | None. Issue 4636 finishes first. |
| T003 | T002 |
| T004 | T003 |
| T005 | T004 |
| T006 | T005 |
| T007 | T006 and task T014 of issue 4640 |
| T008 | T001, T007, and task T012 of issue 4638 |
| T009 | T007 and T008 |
| T010 | T007 and T008 |
| T011 | T007 |
| T-LOCAL-GATES | T009, T010, and T011 |
| T-PR | T-LOCAL-GATES |
| T-REMOTE-CI | T-PR |
| T-MERGE | T-REMOTE-CI and the orchestrator authorization |

Tasks T003 to T006 edit one file, so they run in sequence. Tasks T001, T002, T009, and T011 only read files, so they can run in parallel.

## Test Plan Map

| Test ID | Task | Requirements | Purpose |
| --- | --- | --- | --- |
| TM-01 | T004 | FR-001 | Each family returns one fixed label. |
| TM-02 | T004 | FR-008 | No observation holds source text. |
| TM-03 | T003 | FR-006 | Each secret form is omitted. |
| TM-04 | T003 | FR-007 | Hash and type 7 forms are not decoded. |
| TM-05 | T004 | FR-003, FR-004 | Parser-only families are display-only with a limit. |
| TM-06 | T004 | FR-001 | Indented lines inherit the family of the parent line. |
| TM-07 | T004 | FR-005 | No command string appears in any observation. |
| TM-08 | T005 | FR-009 | Syslog maps for Branch and Standalone only. |
| TM-09 | T005 | FR-009 | Hub syslog stays display-only. |
| TM-10 | T005 | FR-009 | A logging host line never maps to a host-out field. |
| TM-11 | T005 | FR-002 | SNMP maps location and contact only. |
| TM-12 | T005 | FR-002, FR-006 | Cellular maps the APN and omits the username and password. |
| TM-13 | T005 | FR-013 | An unsupported model yields a limit and no mapped field. |
| TM-14 | T005 | FR-002, FR-015 | Each registry entry cites a pointer, an evidence ID, and fixtures. |
| TM-15 | T006 | FR-012 | No socket opens during the review. |
| TM-16 | T003 | FR-006 | Captured logs contain no synthetic secret value. |
| TM-17 | T006 | FR-010 | DNS output matches the stored baseline. |

FR-011 has no new test function. The existing route tests in `tests/integration/web_portal/cisco_config_converter/test_routes.py` run in T006 (R33). FR-014 is verified by the red-run evidence in T010.
