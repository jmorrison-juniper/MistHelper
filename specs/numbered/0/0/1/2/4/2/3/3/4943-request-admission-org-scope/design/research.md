# Research: Ship the preserved admission scope work

This file holds the decisions, the remote verification table, the sources, and the unverified claims. Each decision names the alternatives, the choice, the reason, and the risk.

## Method

- **Truth order**: GitHub `main` outranks the local checkout. `main` is commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The local `HEAD` equals that commit. `git status` lists five modified files, and no other change.
- **Tree fetch**: One call, `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`, returned 11,404 entries with `truncated` set to false. The path filter ran in PowerShell, which avoided nested quoting in the jq program. The blob SHAs come from that tree.
- **Bodies and lines**: Each file body came from the contents endpoint of the repository, with the file path and the ref as query values. The reader decoded the base64 content in PowerShell. The OpenAPI file is 4,317,370 bytes. The contents endpoint returns no body above 1 MB, so that file came from the blobs endpoint, keyed by its blob SHA.
- **Branch**: Commit `5213149d63be00d4c47c0fe8194d4cbf0eca1f1f` has parent `ccff03e05a686ac3f7c14fddb0828cd373c6e822` and tree `ec0531b239058f0b9686352f259941518bc9a06d`. The commit changes exactly the five files.
- **Local hashes**: `git hash-object --no-filters` on each of the five files matched the branch blob for all five. The command writes no object, because it omits `-w`.
- **Compare**: The compare of ccff03e05 with main reports `ahead` with `ahead_by` 1 and 31 files. None of the five paths and no file under the two wan_performance folders appears in that list.
- **PR #4208**: The PR is a draft and OPEN. Its head is `843be63bc837513b4442dae69da9f0db922e0ed1`, and its base is `2a6a5844698aeb180fea353e0243034890774565`. The compare of main with 843be63b reports `diverged`, 33 commits ahead, and 82 files.
- **Thread check**: A search of the two packages that hold the report and the admission code found no thread, async, or executor code. The search did not cover the mistapi package internals (unverified item U-6).
- **External sources**: No `web_fetch` call ran. Each external behavior had a local source in `.venv` or in the repository.
- **Skills**: No skill loaded. The issue has no Podman question and no Juniper device question.
- **Writes**: This task wrote only under the draft folder and the meta folder. It ran no build, test, linter, formatter, install, container, or repository script. Git commands used `--no-optional-locks` and read-only subcommands. The GitHub commands were reads.
- **Shared folders**: The meta folder holds the meta files of other issues. The five-item rule applies to the record folders, not to the meta folder.
- **Session tasks**: The session task table holds rows of other issues. This record uses identifiers that start with `i4943-`.

## Decisions

### D-1 Sequencing with PR #4208

- **Alternatives**: (a) Ship after PR #4208 lands or releases the two files, then port from main. (b) Move the five files into PR #4208 now. (c) Ship the three files that PR #4208 does not touch. (d) Drop the work.
- **Chosen**: (a).
- **Reason**: AGENTS forbids two open pull requests on one file. PR #4208 changes `request_admission.py` with 193 insertions and 75 deletions, and it moves the admission test (RC-43, RC-44, RC-45). Option (b) mixes two concerns and needs a hand port. Option (c) fails, because `client.py:15` on the branch imports `organization_scope` from `request_admission.py`. Option (d) loses the repair for issue #4921 and the credential-safe output.
- **Risk**: Issue #4921 stays open while PR #4208 stays a draft. The preservation branch keeps the work.

### D-2 One pull request for the five-file set

- **Alternatives**: (a) One pull request for the five files and the two hardening repairs. (b) Three pull requests, one for each concern.
- **Chosen**: (a).
- **Reason**: `client.py` imports the scope primitive, and the admission test module holds tests for two concerns. Splitting the work edits the same test module twice and changes the preserved bytes twice.
- **Risk**: The reviewer reads three concerns. The pull request body maps each concern to its tests.

### D-3 Import direction for the scope primitive

- **Alternatives**: (a) Keep `OrganizationScope` in `interfaces` and import it from `mist`. (b) Move the class to `foundation`. (c) Duplicate the class in `mist`.
- **Chosen**: (a).
- **Reason**: The import from `mist` has precedents on main: `src/mist/intelligence/troubleshooting/synthetic_test_trigger/operation.py:16` (RC-41) and `src/mist/resources/device/client_session_control/handler.py:12` (RC-42). The `foundation` package imports `interfaces` at `initialize_mist_session.py:67` (RC-05). Option (b) touches four more files. Option (c) creates two sources of truth.
- **Risk**: The layering drifts further. RA-2 in `plan.md` records the follow-up.

### D-4 Module structure

- **Alternatives**: (a) Named classes, and one new module for the mute. (b) Keep the module-level functions. (c) Keep the mute in `client.py` with nine top-level names.
- **Chosen**: (a).
- **Reason**: Constitution Principle I limits each module to five top-level names. Principle II requires functionality in named classes. The branch breaks both rules (seven names in `request_admission.py` and nine in `client.py`).
- **Risk**: The change renames four symbols. The tests in T005 and T006 cover each renamed symbol. The symbol gate lists each move in the pull request body.

### D-5 Removal of the menu 309 workaround

- **Alternatives**: (a) A follow-up issue after the merge. (b) Remove `AdmissionBinding` in the same pull request. (c) Keep `AdmissionBinding` for good.
- **Chosen**: (a).
- **Reason**: The removal changes menu 309 and adds a second concern (D-2). The workaround coexists with the repair. The ledger takes its own organization first (`request_admission.py:107` on main checks `self.org_id` before the scope).
- **Risk**: Two attribution paths exist for a while. RA-3 in `plan.md` records the follow-up.

### D-6 Color for the traceback formatter

- **Alternatives**: (a) Keep the branch code, which forces `truecolor` for every stream. (b) Use `color_system="auto"`. (c) Use `color_system="truecolor" if supports_color else None`. (d) Use the structlog default formatter.
- **Chosen**: (c).
- **Reason**: Option (a) writes escape sequences to pipes (derived from `.venv\Lib\site-packages\rich\console.py:707-712` and `:2136-2144`). Option (b) uses `_detect_color_system`, which returns no color when `is_terminal` is false (`rich/console.py:789-793`). The formatter renders into a string buffer, so option (b) removes color from terminals too. Option (d) shows frame locals, which breaks FR-012 (`structlog/dev.py:420` and `:529`).
- **Risk**: `NO_COLOR` still disables color in rich (`rich/console.py:725-728`), which keeps the intended behavior.

### D-7 Weak assertion

- **Alternatives**: (a) Delete the assertion. (b) Keep `assert frame is not None`. (c) Use `assert isinstance(frame, types.TracebackType)`.
- **Chosen**: (c).
- **Reason**: The issue comment reports one new `weak_is_not_none` finding at `test_request_admission.py:141` (RC-50). Option (a) removes the guard that the next line depends on. Option (b) keeps the finding.
- **Risk**: None significant.

### D-8 Branch, fragment, and labels

- **Alternatives**: (a) Branch `fix/4943-request-admission-org-scope`, fragment `changelog.d/issue-4943-request-admission-org-scope.md`, and the existing labels. (b) Branch named for issue #4921. (c) Rename the fragment to a pull request name after the pull request opens.
- **Chosen**: (a).
- **Reason**: AGENTS requires an issue number in the branch name, and the tracker of this work is issue #4943. The changelog rule says to keep the first fragment name after the pull request opens (`changelog.d/README.md:19-26`). The issue already carries `bug`, `MistHelper.py`, and `in-progress`, so no label change is needed.
- **Risk**: None.

### D-9 Operator text and README

- **Alternatives**: (a) Change `documentation/operator-guide.md` to match the warning text. (b) Change the warning text to say "uses one organization". (c) Leave both texts.
- **Chosen**: (a). The README stays unchanged.
- **Reason**: The guide says "uses one organization" at line 502 (RC-19), but the warning says "continues with direct organizations" (`client.py:191-194` on the branch). Option (b) makes the warning wrong, because the report reads every direct organization. A search of `README.md` found no mention of menu 308 or of the MSP organization list.
- **Risk**: Minimal.

### D-10 Log lines for the MSP organization list

- **Alternatives**: (a) Add one info line before the call and one debug line after it. (b) Add no log line.
- **Chosen**: (a).
- **Reason**: Constitution Principle VII requires a log line before and after each action. The branch lacks both lines around `listMspOrgs` (`client.py:170` on main).
- **Risk**: Low. The debug line adds one line per MSP call.

### D-11 Preservation branch after the merge

- **Alternatives**: (a) Keep the branch after the merge. (b) Delete the branch after the merge.
- **Chosen**: (a).
- **Reason**: The branch is the only remote copy of the five files until the merge is verified. The issue acceptance requires the branch. Deleting it gives no benefit in this change.
- **Risk**: Branch clutter. The owner decides the deletion date in a separate step.

### D-12 Record placement

- **Alternatives**: (a) Commit the record as the first commit on the ship branch. (b) Open a separate pull request for the record.
- **Chosen**: (a).
- **Reason**: One pull request and one CI run cost fewer minutes (AGENTS, section GitHub Actions minutes). FR-029 limits the first commit to the record.
- **Risk**: The record merges with the code. The first commit holds no other file.

### D-13 Live validation

- **Alternatives**: (a) The owner runs menu 308 once with a real token after the merge. (b) Make a live run a merge gate.
- **Chosen**: (a).
- **Reason**: The live run needs an operator token and a Redis service. The unit tests cover the same paths with fake doubles. Menu 308 is in the `safe` category (`operation_registry.py:536`), so the run reads data only.
- **Risk**: A live defect appears after the merge. The rollback steps in `plan.md` restore the previous behavior.

## Remote Verification

Each row names one claim. The result column uses the values present, absent, partial, or stale. The `main` rows cite the commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The branch rows cite commit `5213149d63be00d4c47c0fe8194d4cbf0eca1f1f`. The PR rows cite head `843be63bc837513b4442dae69da9f0db922e0ed1`. A line of 0 means the claim concerns the whole file.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
|---|-------|------|-----|----------|--------|------|
| RC-01 | The ledger fails closed for a site request with no organization | src/interfaces/wan_performance/collection/request_admission.py | main | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 108 |
| RC-02 | Shared admission is enabled only when the application store uses Redis | src/interfaces/wan_performance/collection/request_admission.py | main | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 53 |
| RC-03 | No `organization_scope` symbol exists on main | src/interfaces/wan_performance/collection/request_admission.py | main | a6064e8fadce930813f8404f85d6b0b830c68cb6 | absent | 0 |
| RC-04 | Session setup uses AdmittedAdapter when RequestLedger.enabled() is true | src/foundation/support/refactors/initialize_mist_session.py | main | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 72 |
| RC-05 | The foundation package imports request_admission | src/foundation/support/refactors/initialize_mist_session.py | main | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 67 |
| RC-06 | The console renderer receives `colors=supports_color`, which is the terminal check | src/foundation/support/utils/logger_utils.py | main | 6cb99dc0e3e0a4808391e6953560071b69e36683 | present | 148 |
| RC-07 | The MSP organization list call uses listMspOrgs | src/mist/intelligence/reports/subscription_expiry/client.py | main | 980b332e7f8be83e4f495cf86913ba3c1b84ac5c | present | 170 |
| RC-08 | A non-200 MSP list result takes the failure path | src/mist/intelligence/reports/subscription_expiry/client.py | main | 980b332e7f8be83e4f495cf86913ba3c1b84ac5c | present | 173 |
| RC-09 | The VC status read is the only site-scoped SDK call in the client | src/mist/intelligence/reports/subscription_expiry/client.py | main | 980b332e7f8be83e4f495cf86913ba3c1b84ac5c | present | 507 |
| RC-10 | The expansion method calls the VC member read, and it keeps the source row when no member returns | src/mist/intelligence/reports/subscription_expiry/client.py | main | 980b332e7f8be83e4f495cf86913ba3c1b84ac5c | present | 629 |
| RC-11 | The menu 308 report class builds the client from the menu session | src/mist/intelligence/reports/subscription_expiry/operation.py | main | c0d4d13d2390152da9596c7e3bea298d7867af64 | present | 214 |
| RC-12 | The menu 308 entry names CrossOrgSubscriptionInventoryReport.run | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4488 |
| RC-13 | Menu 308 is registered in the safe category | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 536 |
| RC-14 | The AdmissionBinding class exists for menu 309 | src/operations/exporting/ex_hardware_inventory/scope/session.py | main | 225a80511a3248a8c0138d67e002e8fe62eda62c | present | 25 |
| RC-15 | The menu 309 batch uses AdmissionBinding | src/operations/exporting/ex_hardware_inventory/run/batch.py | main | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 199 |
| RC-16 | The admission test module exists on main | tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py | main | 2aafadca588ab0a14385e9b3c53fb7fe68c31201 | present | 0 |
| RC-17 | The client test module exists on main | tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py | main | fec6907f47190960c5870f0d5093b301bec6566 | present | 0 |
| RC-18 | The mistapi SDK compatibility test exists | tests/integration/test_mistapi_sdk_compatibility.py | main | cab2d602113012729f6c392dff43197d05913a38 | present | 0 |
| RC-19 | The operator guide says the menu uses one organization when the MSP list is denied | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 502 |
| RC-20 | The OpenAPI file defines the listMspOrgs operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 4081 |
| RC-21 | The OpenAPI file defines the getSiteDeviceVirtualChassis operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 31433 |
| RC-22 | The endpoint page gives the VC status path | documentation/api/sites/GET_sites_site_id_devices_device_id_vc.md | main | 4deda89b31fdebc64126683bdfe992fc421ff103 | present | 7 |
| RC-23 | The endpoint catalog maps listMspOrgs to mistapi msps.orgs | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 331 |
| RC-24 | The endpoint catalog maps the VC status read to mistapi sites.devices | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1223 |
| RC-25 | The architecture page lists an api directory under src | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 207 |
| RC-26 | The api folder under src does not exist on main | src, child api | main | none | absent | 0 |
| RC-27 | The CI mypy scope names the src directory | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-28 | The CI vulture scope names the src directory | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-29 | The CI interrogate scope names the src directory | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-30 | The CI pylint threshold is 9.5 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 122 |
| RC-31 | The test quality baseline holds weak_is_not_none entries | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 10 |
| RC-32 | The repository guide holds the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-33 | The repository guide states that src holds four packages | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 175 |
| RC-34 | The changelog rule names the file by the pull request state | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 19 |
| RC-35 | The route script defines the radix segment function | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| RC-36 | The reference record defines the Mist transport section | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 260 |
| RC-37 | The requirements file pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-38 | The requirements file pins rich 15.0.0 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 233 |
| RC-39 | The requirements file pins structlog 26.1.0 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 249 |
| RC-40 | The pyproject lower bound for mistapi is 0.64.1 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RC-41 | A mist module imports from interfaces (synthetic trigger) | src/mist/intelligence/troubleshooting/synthetic_test_trigger/operation.py | main | 6a4b83d30489d31c2a5e54c4b22bd02f5fba0c15 | present | 16 |
| RC-42 | A mist module imports from interfaces (client session control) | src/mist/resources/device/client_session_control/handler.py | main | 6d0a923d05d9af814431caab7b4e8e71d7bd4ccd | present | 12 |
| RC-43 | PR #4208 head still raises the unscoped site error | src/interfaces/wan_performance/collection/request_admission.py | jmorrison-juniper-4200-migrate-mistwanperformance | 4cf92ab977bb667ef0fe4e72de68994a80f1ffea | present | 212 |
| RC-44 | PR #4208 head holds the admission test at the moved path | tests/unit/wan_performance/test_request_admission.py | jmorrison-juniper-4200-migrate-mistwanperformance | d6368eb4b2483b1ed1faa934cba10a33fb0d5d67 | present | 0 |
| RC-45 | PR #4208 head lacks the wan_dashboard admission test | tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py | jmorrison-juniper-4200-migrate-mistwanperformance | none | absent | 0 |
| RC-46 | The preservation branch holds logger_utils.py with the preserved bytes | src/foundation/support/utils/logger_utils.py | chore/4943-preserve-wip-2026-11-24 | b47036046770f9a36aaecaff1e2821f165ed66df | present | 0 |
| RC-47 | The preservation branch holds request_admission.py with the preserved bytes | src/interfaces/wan_performance/collection/request_admission.py | chore/4943-preserve-wip-2026-11-24 | 5ee19a82c40acbaf2b6364aebd2561b31fc981da | present | 0 |
| RC-48 | The preservation branch holds client.py with the preserved bytes | src/mist/intelligence/reports/subscription_expiry/client.py | chore/4943-preserve-wip-2026-11-24 | 4bc021ea9d089f7c981d6e6be4c02052f1f7329a | present | 0 |
| RC-49 | The preservation branch holds the client test with the preserved bytes | tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py | chore/4943-preserve-wip-2026-11-24 | 913247f0e25799656e4df72234f9fac5cbefbf39 | present | 0 |
| RC-50 | The preservation branch holds the admission test, with the weak assertion at line 141 | tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py | chore/4943-preserve-wip-2026-11-24 | 526be2c14a388c7cc62a27d3005c33f80f3bb7aa | present | 141 |
| RC-51 | The preservation branch client mutes SDK error lines during the MSP call | src/mist/intelligence/reports/subscription_expiry/client.py | chore/4943-preserve-wip-2026-11-24 | 4bc021ea9d089f7c981d6e6be4c02052f1f7329a | present | 208 |
| RC-52 | The preservation branch client wraps the VC read in the organization scope | src/mist/intelligence/reports/subscription_expiry/client.py | chore/4943-preserve-wip-2026-11-24 | 4bc021ea9d089f7c981d6e6be4c02052f1f7329a | present | 672 |

Count of rows: 52. The count matches `remote_checks` in the status file and the count in the summary.

## Sources

- Issue #4943: `gh issue view 4943` with the fields title, body, state, labels, comments, and timestamps. The issue was created 2026-11-26 06:45:40 UTC and updated 06:50:20 UTC. The first comment holds the branch name, the commit, and the gate table.
- Issue #4921 (OPEN, label `bug`, `MistHelper.py`): the runtime defect in shared request admission.
- Issue #4200 (OPEN): the WAN parity spec linked from PR #4208.
- Issue #4920 (CLOSED): the reference record for menu 309.
- Issue #4936 (OPEN): a browser sign-in for the operations portal. It is not related to this change.
- PR #4208 (draft, OPEN): `gh pr view 4208`, with fields headRefOid, baseRefOid, updatedAt, and files.
- PR #4924 (MERGED): menu 309 work on the branch `feat/4920-ex-hardware-inventory-csv`.
- PR #4941 (MERGED): the single commit between `ccff03e05` and `f03c6c9b`. It changes 31 files, and none of the five paths.
- Commit `5213149d63be00d4c47c0fe8194d4cbf0eca1f1f`, read through the commits endpoint, with the five file entries and their blob SHAs.
- Local mistapi 0.64.1 source: `.venv\Lib\site-packages\mistapi\__logger.py:218`, `.venv\Lib\site-packages\mistapi\__api_request.py:30` and `:242`, `.venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py:17`, and `.venv\Lib\site-packages\mistapi\api\v1\sites\devices.py:3529`.
- Local structlog 26.1.0 source: `.venv\Lib\site-packages\structlog\dev.py:393`, `:414`, `:420`, `:445-446`, `:529`, `:675`, and `:713-714`.
- Local rich 15.0.0 source: `.venv\Lib\site-packages\rich\console.py:707-712`, `:725-728`, `:789-793`, and `:2132-2144`.
- Local OpenAPI file: `documentation/mist-api-openapi31yaml.yaml:4081-4085` and `:31433-31464`. The `git status` output lists no change for this file, so the local file equals `HEAD`, and `HEAD` equals `main`.
- Repository documents and rules: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, `documentation/development-setup.md:176-196`, `documentation/container-deployment.md:141-175`, `documentation/quality-gates.md:241-262`, `changelog.d/README.md:19-26`, and `.github/PULL_REQUEST_TEMPLATE.md`.
- Reference record: `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` for shape only. No content was copied.

## Unverified

- **U-1**: The gate results in the issue comment (py_compile, ruff, black, mypy, bandit, complexity, pydocstyle, 985 passing tests, and the test quality result). Reason: rule 2 forbids a gate or a test run. The research task reads and reasons only.
- **U-2**: The older copy of `client.py` in the worktree `MistHelper-cross-org-discovery`, named in the issue body. Reason: the folder lies outside the repository, and this task reads the repository only.
- **U-3**: The run logs at 16:15 and 16:23 on 2026-11-24, named in the issue body. Reason: the logs sit under `data/`, and they may hold credential-shaped text. This task does not read them.
- **U-4**: The save times of the five files, named in the issue body. Reason: this task reads no file timestamp. The blob equality in T001 proves the content, not the save time.
- **U-5**: The VS Code checkpoint details in the issue body. Reason: the checkpoints sit outside the repository.
- **U-6**: Thread use inside the mistapi package. Reason: the thread search covered only the two packages of this change. The SDK internals were not searched.
- **U-7**: The runtime output of the color defect and the mute. Reason: derived from source reading, and not executed. The red run in T007 confirms the failures.
- **U-8**: The live output of menu 308 with a real token and a Redis service. Reason: the run needs an operator token and a live service. Decision D-13 assigns it to the owner.
- **U-9**: The symbol gate output, the STE score of the operator guide, and the pylint, vulture, and interrogate results. Reason: rule 2 forbids those runs in this task. T-LOCAL-GATES runs them in the ship step.
