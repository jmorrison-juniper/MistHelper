# Research: Preserve CSV Carriage Returns

Truth order: GitHub `main` read with `gh api` outranks local search. Local reads confirm content only where `main` and the local tree match. The local tree at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` equals remote `main`. Five unrelated tracked files differ locally (see Local Tree State).

## Issue Facts (Step 1)

- Issue #4776 is OPEN. Title: `Export: shared multiline escaping discards carriage returns`. Author: `jmorrison-juniper`. Created 2026-11-11. Updated 2026-11-16. The issue has no comments.
- Labels: `bug`, `MistHelper.py`, and `in-progress`.
- Requirement: preserve raw normalized values, and escape carriage returns in CSV presentation only.
- Reproduction command from the issue: `python -m pytest -q tests/unit/websocket_streams/web/hardware/test_report.py`. The issue reports one failed test and 37 passed before the stop.
- Error text from the issue: expected `apostrophe-backslash-r-plain`, actual `apostrophe-plain`.
- The issue says the defect was found during #4773.

## Linked Work and Existing Record (Steps 2 and 3)

- Step 2: `gh pr list --state all --search 4776` returns one pull request, PR #4813. It is open and not merged. Its head branch is `jmorrison-juniper-csv-carriage-return-preservation`. See RC-59 and RC-60.
- Step 3: a local glob for `specs/**/4776-*` found no folder on `main`. The PR branch holds one folder, `specs/numbered/0/0/1/2/3/1/0/1/4776-csv-carriage-returns`. Its files are reviewed in `analysis.md` (Legacy Record Review).
- Step 4: the full remote tree was read once with `git/trees/main?recursive=1`. Later remote reads used the contents API. Each claim below has one row in the remote table.

## Decisions

### D-1: Keep raw carriage returns in the shared normalizer

- Alternatives: (a) Keep the removal and add presentation later. (b) Convert carriage returns to backslash and `r` in the shared function. (c) Keep raw carriage returns in the shared function and present them in CSV only.
- Chosen: (c). The issue asks to preserve raw normalized values and to escape carriage returns in CSV presentation only.
- Reason: Database rows keep the value. Option (b) would write CSV text into database rows.
- Risk: New database rows keep carriage returns. Existing rows do not change (U-5).

### D-2: Place the presenter in a new package under `src/foundation/models`

- Alternatives: (a) Add a method to `DataProcessingUtils`. (b) Add a method to `DataExporter`. (c) Add a module to `src/foundation/models/data`. (d) Add a package to `src/foundation/models`.
- Chosen: (d). Option (a) and option (b) add a child to a class that already exceeds the limit (RC-03, RC-09). Option (c) makes a folder that holds five children hold six (RC-64). Option (d) makes `src/foundation/models` hold five children (RC-63).
- Risk: `src/foundation/models` reaches its limit (R-3, R-06).

### D-3: Present carriage returns in every CSV writer that receives normalized rows

- Alternatives: (a) Change only `write_to_csv`, as PR #4813 does. (b) Keep raw carriage returns in the 52-week CSV. (c) Present carriage returns in each CSV writer that receives normalized rows.
- Chosen: (c). Option (a) leaves raw carriage returns in the 52-week CSV (RC-11, RC-12, RC-13). Option (b) gives two CSV rules for one defect.
- Risk: Two more source files change. T006 and T013 cover the change.

### D-4: Copy each raw row before the CSV presentation

- Alternatives: (a) Escape rows in place, as `main` does. (b) Copy each row first.
- Chosen: (b). It keeps caller rows unchanged (FR-004). The checked callers escape rows before writing (RC-17).
- Risk: A caller reads rows after writing and expects escaped text. The full test run covers that case (R-03).

### D-5: Leave the writers that receive no normalized rows unchanged

- Alternatives: (a) Present carriage returns in every CSV writer in `src`. (b) Change only the writers that receive normalized rows.
- Chosen: (b). The EX report writer does not call the shared normalizer (RC-16). The organization inventory writers receive rows that the file does not escape (RC-17, RC-18). The Wi-Fi and WAN writers write fixed placeholders (RC-19, RC-20).
- Risk: A future change sends normalized rows to one of these writers. U-2 covers the EX case.

### D-6: Keep the EX hardware report contract unchanged

- Alternatives: (a) Apply the shared presentation to the EX report. (b) Keep the EX report unchanged.
- Chosen: (b). The EX contract in the reference record uses standard CSV quoting. Its folder is on `main` (RC-54).
- Risk: Issue #4773 may route EX rows through the shared path. U-2 requires an owner review first.

### D-7: Use tests on `main` as the reproduction

- Alternatives: (a) Wait for the file named in the issue. (b) Use tests that exist on `main`.
- Chosen: (b). The named file is absent on `main`, on the PR branch, and on matching branch names (RC-28, RC-29, RC-30).
- Risk: The issue command cannot run until the owner names a real file (U-3).

### D-8: Use a new branch and close PR #4813 after the push

- Alternatives: (a) Update PR #4813 in place. (b) Create branch `fix/4776-csv-carriage-returns` and open a new pull request.
- Chosen: (b). The branch name of PR #4813 does not follow the rule at RC-43 and RC-44. The closing comment holds the preservation proof required by RC-45.
- Risk: Two open pull requests exist for a short time (R-09).

### D-9: Name the changelog fragment after the issue

- Alternatives: (a) `pr-<number>.md`. (b) `issue-4776-csv-carriage-returns.md`. (c) A date name.
- Chosen: (b). The pull request number does not exist when the fragment is created. The README rule at RC-33 gives this form. The guard at RC-34 accepts it.
- Risk: None known.

### D-10: Make no README or operator guide change

- Alternatives: (a) Add a README note about carriage returns. (b) Change the operator guide. (c) Make no documentation change.
- Chosen: (c). The README describes CSV output in general terms only (RC-47). The operator guide rule covers the EX menu only (RC-48). The release note carries the user-facing change.
- Risk: A reviewer asks for a README note under the pull request template (RC-46).

### D-11: Add presenter tests in a new file

- Alternatives: (a) Add presenter tests to `test_data_processing_utils.py`. (b) Add presenter tests to a new file in the same folder.
- Chosen: (b). The new module needs its own test module. The folder holds two children (RC-67), so one more file is allowed.
- Risk: None known.

### D-12: Run every applicable gate and record each gate that does not apply

- Alternatives: (a) Run only the changed-file tests. (b) Run every applicable gate.
- Chosen: (b). The constitution requires each applicable gate to run (RC-41). The gates that do not apply are pip-audit, menu reference, Playwright, ops portal, and ops platform.
- Risk: The full test run takes a long time (R-08).

### D-13: Leave steps 10 to 12 of Principle IV to the orchestrator

- Alternatives: (a) Add deployment tasks to this record. (b) Leave deployment to the orchestrator after T-MERGE.
- Chosen: (b). The brief fixes the final tasks at T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.
- Risk: The constitution step stays open after the merge (U-1).

### D-14: Keep the issue labels unchanged

- Alternatives: (a) Add the `tests` scope label. (b) Keep the labels.
- Chosen: (b). The issue carries `bug`, `MistHelper.py`, and `in-progress`, which match the work.
- Risk: None known.

### D-15: Make no Mist, Podman, or Juniper device claim and load no skill

- Alternatives: (a) Read the OpenAPI file and the SDK for a claim. (b) Make no claim about them.
- Chosen: (b). The changed path receives rows after the API call returns. Neither changed module references mistapi (RC-61, RC-62). The issue has no Podman question and no Juniper device behavior, so no skill is loaded.
- Risk: None known.

## Remote Verification

Each row is one check. The row count equals `remote_checks` in the STATUS file.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Shared normalizer removes carriage returns with replace | src/foundation/models/data/data_processing_utils.py | main | f0e53336717eefbbe0bf7b4136b3e0d4f11f3847 | present | 167 |
| RC-02 | escape_multiline is a static method in DataProcessingUtils | src/foundation/models/data/data_processing_utils.py | main | f0e53336717eefbbe0bf7b4136b3e0d4f11f3847 | present | 156 |
| RC-03 | DataProcessingUtils holds 11 methods above the five-item limit | src/foundation/models/data/data_processing_utils.py | main | f0e53336717eefbbe0bf7b4136b3e0d4f11f3847 | present | 27 |
| RC-04 | write_to_csv spans 25 lines from 389 to 413 | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 389 |
| RC-05 | write_to_csv calls escape_multiline | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 408 |
| RC-06 | _write_csv_format is the only production caller of write_to_csv | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 375 |
| RC-07 | CSV rows are written with csv.DictWriter in _write_csv_open_and_emit | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 454 |
| RC-08 | export_with_processing escapes rows before write_with_format_selection | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 505 |
| RC-09 | DataExporter holds 27 methods above the five-item limit | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 81 |
| RC-10 | SQLite writer escapes rows before storage | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 181 |
| RC-11 | 52-week exporter returns escaped rows from _process_rows | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 220 |
| RC-12 | 52-week first CSV batch writes with csv.DictWriter | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 312 |
| RC-13 | 52-week CSV append writes with csv.DictWriter | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 327 |
| RC-14 | 52-week streaming pages pass rows through _process_rows | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 338 |
| RC-15 | DeviceEvents52wExporter holds 25 methods above the five-item limit | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 62 |
| RC-16 | EX report writer uses csv.DictWriter without a shared escape call | src/operations/exporting/ex_hardware_inventory/report/csv_file.py | main | aab90d618cfa5ead3427f366732b39ea3e9b2a93 | present | 50 |
| RC-17 | Organization inventory escapes rows only at lines 623 and 705 | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 623 |
| RC-18 | Weekly inventory CSV writer receives weekly data | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 449 |
| RC-19 | Wi-Fi clients CSV writer writes a fixed placeholder | src/operations/exporting/export/wifi_clients_exporter.py | main | 10cb50b7745731a1be9bb9127561721c29938d73 | present | 301 |
| RC-20 | WAN client events CSV writer writes a fixed placeholder | src/operations/exporting/export/wan_client_events_exporter.py | main | add89eccb4df634d60f3d6b922115256408d9506 | present | 281 |
| RC-21 | Shared test asserts carriage return removal | tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py | main | 2e66985896514322261e20350ec7d76d20bc3fe4 | present | 267 |
| RC-22 | Export tests patch escape_multiline in CSV flows | tests/unit/export/test_data_exporter.py | main | 8e91cbe472c2068183c15fca1fa350d1b76f9d34 | present | 500 |
| RC-23 | 52-week extended tests inject a MagicMock for data_processing_utils | tests/unit/test_device_events_52w_exporter_extended.py | main | 2361f5b0048d7834f63b8c360066a35344484f23 | present | 34 |
| RC-24 | Endpoint family test expects carriage return removal in the note | tests/unit/export/test_endpoint_family_exporter.py | main | d6df325c303441be73fd478b59589257ce520006 | present | 687 |
| RC-25 | Endpoint family test expects the paged note without carriage return | tests/unit/export/test_endpoint_family_exporter.py | main | d6df325c303441be73fd478b59589257ce520006 | present | 692 |
| RC-26 | SQLite backend preservation test module exists | tests/unit/db/sle_window_summary/test_backend_preservation.py | main | 38670362f1e2629a6630b6b0065cc251df117c4d | present | 0 |
| RC-27 | Web CSV test asserts CRLF bytes for the EX portal response | tests/unit/websocket_streams/web/test_ws_hardware_csv.py | main | 61168abc17ce5db1d74161017d46aeb13c530f67 | present | 384 |
| RC-28 | Named reproduction test file exists | tests/unit/websocket_streams/web/hardware/test_report.py | main | not applicable, HTTP 404 | absent | 0 |
| RC-29 | Named reproduction test file exists on the PR branch | tests/unit/websocket_streams/web/hardware/test_report.py | jmorrison-juniper-csv-carriage-return-preservation | not applicable, HTTP 404 | absent | 0 |
| RC-30 | No branch name contains 4773, 4776, hardware, or transceiver | repository branch list | all branches | not applicable, branch list | absent | 0 |
| RC-31 | Issue-named changelog fragment exists on main | changelog.d/issue-4776-csv-carriage-returns.md | main | not applicable, HTTP 404 | absent | 0 |
| RC-32 | Issue-named changelog fragment exists on the PR head | changelog.d/issue-4776-csv-carriage-returns.md | PR #4813 head | c00a85f8b3fe1dc7a972521e6f162aa4881f8dab | present | 0 |
| RC-33 | Changelog naming table names the pull request, issue, and date forms | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 26 |
| RC-34 | Changelog guard accepts the issue name form | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| RC-35 | CI defines MYPY, VULTURE, PYDOCSTYLE, and INTERROGATE path variables | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-36 | CI defines pylint, interrogate, and vulture thresholds | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 122 |
| RC-37 | Ruff and Black set line length 120 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 202 |
| RC-38 | Local gates table lists each gate command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| RC-39 | Test quality ratchet procedure section exists | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| RC-40 | Principle I sets the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-41 | Principle IV sets the full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| RC-42 | Principles VI and VII set the comment and logging rules | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RC-43 | Constitution branch naming rule for MistHelper | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 476 |
| RC-44 | AGENTS.md branch rule requires type-issue-slug names | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 192 |
| RC-45 | AGENTS.md requires a preservation proof before a pull request closes | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| RC-46 | Pull request template holds the documentation checklist | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 34 |
| RC-47 | README describes CSV output in general terms only | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 10 |
| RC-48 | Operator guide states the EX carriage return apostrophe rule | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 538 |
| RC-49 | Architecture names DataExporter write_with_format_selection as the output writer | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 258 |
| RC-50 | Container guide holds the test and debug container section | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| RC-51 | Route script sets base 5 and an eight-segment width | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-52 | Route parent 0/0/1/2/3/1/0 holds one child, directory 2 | specs/numbered/0/0/1/2/3/1/0 | main | 6b8d6e409242bd904d2e35ab897ec4bacf687e02 | present | 0 |
| RC-53 | Route leaf 0/0/1/2/3/1/0/1 is absent | specs/numbered/0/0/1/2/3/1/0/1 | main | not applicable, HTTP 404 | absent | 0 |
| RC-54 | Reference EX record folder is present on main | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv | main | 00922155516e4f21e34a0bf75613fae7ab481193 | present | 0 |
| RC-55 | Legacy spec.md exists on the PR branch | specs/numbered/0/0/1/2/3/1/0/1/4776-csv-carriage-returns/spec.md | jmorrison-juniper-csv-carriage-return-preservation | 6484cfd4247894026d8420b61a0ecf5daeab56c7 | present | 0 |
| RC-56 | Legacy analysis.md is absent on the PR branch | specs/numbered/0/0/1/2/3/1/0/1/4776-csv-carriage-returns/analysis.md | jmorrison-juniper-csv-carriage-return-preservation | not applicable, HTTP 404 | absent | 0 |
| RC-57 | Legacy quickstart holds no exact verification commands | specs/numbered/0/0/1/2/3/1/0/1/4776-csv-carriage-returns/design/quickstart.md | jmorrison-juniper-csv-carriage-return-preservation | 7a4ef5145be03011f5a1f916540f33726f4a768b | absent | 0 |
| RC-58 | PR write_to_csv grows to 29 lines, so the legacy no-violation claim is stale | src/operations/exporting/export/data_exporter.py | PR #4813 head | c00a85f8b3fe1dc7a972521e6f162aa4881f8dab | stale | 389 |
| RC-59 | PR #4813 is open, its body contains Closes #4776, and its head branch does not follow the naming rule | PR #4813 | PR #4813 head | c00a85f8b3fe1dc7a972521e6f162aa4881f8dab | present | 0 |
| RC-60 | PR #4813 non-skipped checks report SUCCESS | PR #4813 checks | PR #4813 head | c00a85f8b3fe1dc7a972521e6f162aa4881f8dab | present | 0 |
| RC-61 | Shared normalizer has no mistapi reference | src/foundation/models/data/data_processing_utils.py | main | f0e53336717eefbbe0bf7b4136b3e0d4f11f3847 | absent | 0 |
| RC-62 | DataExporter has no mistapi reference | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | absent | 0 |
| RC-63 | src/foundation/models holds four children | src/foundation/models | main | directory listing, no blob SHA | present | 0 |
| RC-64 | src/foundation/models/data holds five children | src/foundation/models/data | main | directory listing, no blob SHA | present | 0 |
| RC-65 | src/operations/exporting/export holds 49 children | src/operations/exporting/export | main | directory listing, no blob SHA | present | 0 |
| RC-66 | tests/unit/export holds 55 children | tests/unit/export | main | directory listing, no blob SHA | present | 0 |
| RC-67 | tests/unit/config/foundation/models/dataproc holds two children | tests/unit/config/foundation/models/dataproc | main | directory listing, no blob SHA | present | 0 |
| RC-68 | src/foundation/models/csv_presentation is absent | src/foundation/models/csv_presentation | main | directory listing, no blob SHA | absent | 0 |
| RC-69 | tests/unit/websocket_streams/web holds 11 children and no hardware folder | tests/unit/websocket_streams/web | main | directory listing, no blob SHA | present | 0 |
| RC-70 | List branch joins values without escaping line feeds | src/foundation/models/data/data_processing_utils.py | main | f0e53336717eefbbe0bf7b4136b3e0d4f11f3847 | present | 164 |
| RC-71 | Constitution Technology section requires Python 3.15 or newer | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 274 |

Remote head of `main`: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (read with `gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/main`).

## Route Verification

- Algorithm: `Get-SpecRadixSegments` in `.specify/scripts/powershell/spec-route.ps1` (RC-51). It writes the number in base 5, with eight digits, most significant first.
- For 4776: 4776 in base 5 is 123101. Padded to eight digits, the route is `0/0/1/2/3/1/0/1`. This matches the ROUTE in the task.
- Route parent `0/0/1/2/3/1/0` holds one child, directory `2` (RC-52). It has room for the new child `1`.
- Route leaf `0/0/1/2/3/1/0/1` is absent on `main` (RC-53). The feature folder `4776-csv-carriage-returns` is the only child of the leaf.
- Reference check: 4920 in base 5 is 124140, which gives route `0/0/1/2/4/1/4/0`. The reference folder exists on `main` (RC-54), so the algorithm matches the existing records.
- The script was read, not run. Repository scripts stay unexecuted under the brief.

## Mist API and mistapi

- Not applicable. The changed path receives rows after the API call returns. No endpoint behavior changes.
- The OpenAPI file `documentation/mist-api-openapi31yaml.yaml` was not read. No claim depends on it.
- The pinned mistapi package was not read. Neither changed module references mistapi (RC-61, RC-62). No SDK claim is made.

## Local Tree State

- `git status --porcelain --untracked-files=no` in the repository root lists five tracked files that differ from `HEAD`: `src/foundation/support/utils/logger_utils.py`, `src/interfaces/wan_performance/collection/request_admission.py`, `src/mist/intelligence/reports/subscription_expiry/client.py`, and two test files under `tests/unit`.
- None of the eight existing files that the change modifies differs from `HEAD`.
- None of the five files contains a call to `escape_multiline` (local `Select-String`).

## Sources

- AGENTS.md (repository root): read in full. Rules cited at RC-44 and RC-45.
- .github/copilot-instructions.md: read in full. Rules cited at RC-35 to RC-39. Its Local gates table is the source for each verification command.
- .specify/memory/constitution.md: read in full. Rules cited at RC-40 to RC-43 and RC-71.
- .specify/templates/spec-template.md, plan-template.md, tasks-template.md, and checklist-template.md: read for the required headings and the shape of each file.
- Reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`: read for shape and depth. Its folder exists on `main` (RC-54). Its content was not copied.
- documentation/quality-gates.md: read for the CI job list. No claim in this record depends on a line of it.
- documentation/development-setup.md: read for the bootstrap rule of the test environment. No claim depends on a line of it.
- documentation/architecture.md: RC-49.
- documentation/container-deployment.md: RC-50.
- documentation/operator-guide.md: RC-48.
- changelog.d/README.md: RC-33.
- tests/guardrails/test_changelog_fragment_policy.py: RC-34.
- .github/PULL_REQUEST_TEMPLATE.md: RC-46.
- README.md: RC-47.
- .github/workflows/ci.yml: RC-35 and RC-36.
- pyproject.toml: RC-37.
- .specify/scripts/powershell/spec-route.ps1: RC-51.
- PR #4813 on GitHub: RC-32, RC-58, RC-59, RC-60. The patches came from `gh api repos/jmorrison-juniper/MistHelper/pulls/4813/files`.
- Python csv module documentation, URL `https://docs.python.org/3/library/csv.html`, fetched 2026-11-26. It states that `QUOTE_MINIMAL` quotes a field that contains a carriage return, a line feed, or a character of `lineterminator`. It states that `lineterminator` defaults to `\r\n`. It states that `escapechar` applies to `QUOTE_NONE` and to `doublequote` set to false. The record uses these statements for the regression risk in R-02.
- Skills: none loaded. The issue has no Podman question and no Juniper device behavior.

## Unverified

- UV-01: The test named in the issue exists in another place. Reason: it is absent on `main` (RC-28), on the PR branch (RC-29), and on every branch name that matches (RC-30).
- UV-02: The 69 call sites in 53 files match the remote tree file by file. Reason: the count came from a local read at the commit that equals remote `main`. The record did not fetch each file from the remote.
- UV-03: No other EX report module calls the shared normalizer. Reason: only `csv_file.py` was read from the remote tree (RC-16). The code search command rejected the path filter.
- UV-04: Primary key strategy fields hold no free text. Reason: `src/foundation/support/refactors/endpoint_primary_key_strategies.py` was not read.
- UV-05: The container smoke and the staging smoke in the legacy record ran. Reason: this agent has no container test run and no staging credential. The new record requires neither check.
- UV-06: The full test run passes on the implementer machine. Reason: the brief forbids test runs in this session.
- UV-07: The raw carriage return inside a quoted cell is written as is. Reason: the Python documentation gives the quoting rule, but no test wrote the bytes in this session.
