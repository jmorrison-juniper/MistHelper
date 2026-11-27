# Research: Check Every Operation Pair in the mistapi Spec Guard

Each entry gives the evidence, the decision, the alternatives, and the risk. Remote facts are read from GitHub `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, using `gh api`. SDK facts are read from the installed package `.venv\Lib\site-packages\mistapi`, version 0.64.1. Mist API facts are read from `documentation\mist-api-openapi31yaml.yaml`.

## R0. Issue facts, linked work, and existing records

- Issue #4935 is open. Its title is `Test: test_mistapi_spec_modules checks only the last operationId pair in each spec file`. Its labels are `bug` and `tests`. It has no comments. It was created and last updated on 2026-11-25 at 21:44:20 UTC.
- The issue names the helper `MistapiSpecModuleIndex._source_fields` at lines 67 to 77. It states that the feature 4934 specification declares 25 operation pairs, and that the guard examined one pair.
- The issue lists three expected behaviors. The guard checks each declared pair. The guard fails when an operation line has no matching module line. The guard reports the number of pairs examined.
- The issue proposes a repair. The helper returns a list of pairs. The test uses a two-pair fixture with a wrong first pair. The issue includes no traceback or command output.
- Linked pull requests: none. The search for `4935` returned pull request 4438, merged on 2026-10-28. It is a dependency update. Its body names an issue 4935 in the Hypothesis repository, not in this repository.
- Existing record: none. A search of `specs\` for folders that begin with `4935-` found none. The remote tree has no matching path (remote check 21).

## R1. The defect in the guard

- **Evidence**: The helper `_source_fields` keeps the last operation line and the last module line of each file (remote checks 1 to 3). Its caller `spec_declarations` appends one tuple for each file (remote check 4). The test asserts one failure list (remote check 6).
- **Effect**: The spec file of issue 4934 holds 25 operation lines and 25 module lines (remote checks 10 and 11). The guard checks only `listWebhookTopics`.
- **Scope of the old guard**: 463 files hold both fields. The frozen file is one of them, so the old guard examines 462 declarations.

## R2. Remote verification table

Each row is one remote check. A line of 0 marks a path-level check, and no line claim applies. The `Result` column records whether the claim holds on `main`. The table has 50 rows, the same count as `META_DIR\4935-STATUS.json`.

| No. | Claim | Path | Blob SHA | Result | Line |
| - | - | - | - | - | - |
| 1 | Helper `_source_fields` spans lines 67 to 77 | tests/guardrails/test_mistapi_spec_modules.py | 050f0c80df40dd395ef7a256c810233dbb93a7b9 | present | 67 |
| 2 | Helper overwrites `operation_id` on each operation line | tests/guardrails/test_mistapi_spec_modules.py | 050f0c80df40dd395ef7a256c810233dbb93a7b9 | present | 71 |
| 3 | Helper returns `None` when no module path exists | tests/guardrails/test_mistapi_spec_modules.py | 050f0c80df40dd395ef7a256c810233dbb93a7b9 | present | 77 |
| 4 | `spec_declarations` appends one declaration for each spec file | tests/guardrails/test_mistapi_spec_modules.py | 050f0c80df40dd395ef7a256c810233dbb93a7b9 | present | 54 |
| 5 | `frozen_spec_files` names the 595 spec file | tests/guardrails/test_mistapi_spec_modules.py | 050f0c80df40dd395ef7a256c810233dbb93a7b9 | present | 45 |
| 6 | Test method asserts one failure list | tests/guardrails/test_mistapi_spec_modules.py | 050f0c80df40dd395ef7a256c810233dbb93a7b9 | present | 95 |
| 7 | Guard scans every `spec.md` under `specs` | tests/guardrails/test_mistapi_spec_modules.py | 050f0c80df40dd395ef7a256c810233dbb93a7b9 | present | 48 |
| 8 | Guard imports mistapi with `importorskip` | tests/guardrails/test_mistapi_spec_modules.py | 050f0c80df40dd395ef7a256c810233dbb93a7b9 | present | 11 |
| 9 | Guard defines `_SPECS_ROOT` from `_REPO_ROOT` as a module global | tests/guardrails/test_mistapi_spec_modules.py | 050f0c80df40dd395ef7a256c810233dbb93a7b9 | present | 18 |
| 10 | Spec 4934 declares operation pairs from line 461 | specs/numbered/0/0/1/2/4/2/1/4/4934-mist-netcool-runbook/spec.md | fd0fef1b3787d6459eba01762213a75924a6fea3 | present | 461 |
| 11 | Spec 4934 last pair names `listWebhookTopics` at line 557 | specs/numbered/0/0/1/2/4/2/1/4/4934-mist-netcool-runbook/spec.md | fd0fef1b3787d6459eba01762213a75924a6fea3 | present | 557 |
| 12 | Spec 511 operation line has no module path line | specs/511-mist-count-org-client-fingerprints/spec.md | 467ae11b1c3162c0144ac7859d4828166a32b32a | present | 10 |
| 13 | Spec 511 line 14 names no module path | specs/511-mist-count-org-client-fingerprints/spec.md | 467ae11b1c3162c0144ac7859d4828166a32b32a | present | 14 |
| 14 | Spec 511 line 15 says the installed SDK lacks `countOrgClientFingerprints` | specs/511-mist-count-org-client-fingerprints/spec.md | 467ae11b1c3162c0144ac7859d4828166a32b32a | stale | 15 |
| 15 | Spec 511 line 69 names `mistapi.api.v1.sites.insights.fingerprints.count`, which the SDK lacks | specs/511-mist-count-org-client-fingerprints/spec.md | 467ae11b1c3162c0144ac7859d4828166a32b32a | stale | 69 |
| 16 | Spec 591 operation line has no module path line | specs/591-mist-get-org128-t-registration-commands/spec.md | e9b973855db56baaf89fc5b366f823cc572801fe | present | 10 |
| 17 | Spec 591 line 14 states that the SDK module is not available | specs/591-mist-get-org128-t-registration-commands/spec.md | e9b973855db56baaf89fc5b366f823cc572801fe | present | 14 |
| 18 | Spec 932 operation line has no module path line | specs/932-mist-list-org-audit-logs-legacy/spec.md | 236ffc70f605d3fd3b0cd09e6b3f64ed24a5dd0b | present | 11 |
| 19 | Spec 932 line 15 states that no SDK module exists | specs/932-mist-list-org-audit-logs-legacy/spec.md | 236ffc70f605d3fd3b0cd09e6b3f64ed24a5dd0b | present | 15 |
| 20 | Frozen spec 595 has one operation line, which names `getOrgAosRegisterCmd` at line 10 | specs/595-mist-get-org-aos-register-cmd/spec.md | cccdba394218ed18013f9c109f6c7e473af80f33 | present | 10 |
| 21 | No record folder with the 4935 prefix exists on `main` | specs/numbered/0/0/1/2/4/2/2/0 | none | absent | 0 |
| 22 | Reference record 4920 holds a `spec.md` file | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| 23 | Changelog README allows no fragment for an internal-only change | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| 24 | Changelog README keeps the first fragment name after the pull request opens | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 32 |
| 25 | Constitution requires one fragment for each change | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| 26 | Constitution supersedes other practice documents | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |
| 27 | Local gates table has the Tests row | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| 28 | Local gates table has the Full tests row | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 62 |
| 29 | Local gates table has the Test quality row | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 65 |
| 30 | Local gates table has the Symbols row | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| 31 | Local gates table has the STE row | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| 32 | Mypy scope excludes the tests directory | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 33 | Radon scope excludes tests/guardrails | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 99 |
| 34 | Pytest shard includes tests/guardrails | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| 35 | CI runs the changelog policy guard | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 298 |
| 36 | CI runs bandit on the repository root | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| 37 | CI runs the test quality gate with config and baseline | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 632 |
| 38 | Bandit exclude_dirs includes tests | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 503 |
| 39 | Ruff line length is 120 | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 202 |
| 40 | Ruff extend-exclude omits tests | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 206 |
| 41 | Black line length is 120 | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 559 |
| 42 | Citation lint scans tests | documentation/quality-gates.md | 6776d334cca5d9b43273473a06da367a65605c6d | present | 66 |
| 43 | Test quality baseline holds no entry for the guard file | .github/test-quality-baseline.json | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | absent | 0 |
| 44 | Test quality config file exists | .github/test-quality-config.toml | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| 45 | Route width is 8 segments | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| 46 | Route base is 5 | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| 47 | Missing-endpoint catalog lists `listWebhookTopics` as missing | documentation/MIST_API_MISSING_ENDPOINTS.md | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | present | 246 |
| 48 | Dependency parity guard prints its examined count | tests/guardrails/test_dependency_declaration_parity.py | 51e24f5e98fbf78af50eb6bb91513776db8aa838 | present | 137 |
| 49 | Folder guard test checks the examined count output | tests/guardrails/test_process_folder_structure.py | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 184 |
| 50 | Dependency lock guard prints its examined count | tests/guardrails/test_dependency_lock_workflow.py | e529b5c8dc2ce363c670a42595070135fac230c4 | present | 77 |

Each remote file read used the `contents` endpoint with `?ref=main`. Each row above matches the blob SHA that the tree call returned. The tree calls used `git/trees/main?recursive=1`, which reported 11,404 entries and no truncation.

## R3. Survey of operation pairs on main

- **Method**: The tree call listed 910 `spec.md` blobs. Local HEAD equals `main`. The local index holds 4,159 entries under `specs`. `git diff --cached` and `git diff` report no change under `specs`. The index blob SHA equals the remote blob SHA for all 910 files, with zero mismatches.
- **Results**: 466 spec files hold an operation line or a module line. There are 490 operation lines and 487 module pairs. Three operation lines have no module line, in spec files 511, 591, and 932. There are zero stray module lines and zero module lines without an operation line. Only the spec file of issue 4934 holds two or more operation lines, and it holds 25.
- **Totals for the change**: The frozen file holds one operation line. The new guard examines 489 operation lines, which is 490 minus the frozen one. After spec file 511 is corrected, 487 pairs carry a module, and 2 pairs hold declared absences.

## R4. SDK check simulation

- **Method**: A PowerShell read scanned 288 `.py` files under `.venv\Lib\site-packages\mistapi`. Each top-level line that begins with `def name(` maps `name` to the dotted module path. The scan found 1,137 names. It logged one duplicate name, `show`, defined in `mistapi.device_utils.__tools.routes` and `mistapi.device_utils.__tools.sessions`.
- **Results**: Each non-frozen pair with a module matches its SDK definition, with zero mismatches. The frozen pair for `getOrgAosRegisterCmd` mismatches, because the SDK lacks the function. No operation name in a pair has a duplicate definition.
- **Projection**: After the change, 487 pairs match, 2 declared absences hold, and the defect count is zero.
- **Approximation**: The guard uses the `ast` module and checks top-level `FunctionDef` nodes. A column-zero `def` match gives the same set for ordinary modules. The gate run decides the final count.

## R5. The three operation lines without module lines

- **Spec file 511, line 10**: The operation is `countOrgClientFingerprints`. Line 14 is prose, and line 15 says the SDK lacks the function (remote checks 12 to 14). The installed SDK defines it at `.venv\Lib\site-packages\mistapi\api\v1\orgs\insights.py` line 17, with its URI at line 57. The Mist API defines it at `documentation\mist-api-openapi31yaml.yaml` line 10428. The module `mistapi.api.v1.sites.insights` does not exist in the installed SDK, so line 69 is stale (remote check 15).
- **Spec file 591, line 10**: The operation is `getOrg128TRegistrationCommands`. Line 14 is prose (remote checks 16 and 17). The installed SDK has no definition. The nearest SDK function is `getOrgSsrRegistrationCommands` at `.venv\Lib\site-packages\mistapi\api\v1\orgs\ssr.py` line 48. The Mist API defines the operation at `documentation\mist-api-openapi31yaml.yaml` line 4955.
- **Spec file 932, line 11**: The operation is `listOrgAuditLogsLegacy`. Line 15 is prose (remote checks 18 and 19). The installed SDK has no definition. The SDK defines `listOrgAuditLogs` at `.venv\Lib\site-packages\mistapi\api\v1\orgs\logs.py` line 93. The Mist API defines the legacy operation at `documentation\mist-api-openapi31yaml.yaml` line 12020.

## R6. Pairing rule

- **Evidence**: In the spec file of issue 4934, each module line follows its operation line (remote checks 10 and 11). The issue states the repair rule: pair each operation line with the next module line.
- **Decision**: D-1 and D-2.

## R7. Declared absence rule

- **Evidence**: The installed SDK lacks both functions in spec files 591 and 932. The spec prose states the absence (remote checks 17 and 19). The Mist API defines both operations (R5).
- **Decision**: D-3 and D-4.

## R8. Count reporting

- **Evidence**: The repository guards print the count they examine. The parity guard prints `dependency parity: examined {examined} requirements, {len(defects)} defects` at line 137 (remote check 48). The folder guard asserts that the output contains `children examined` at line 184 (remote check 49). The lock guard prints `Examined 1 dependency lock job, {len(defects)} defects` at line 77 (remote check 50).
- **Decision**: D-6 and D-7.

## R9. Gate applicability

- **Evidence**: The local gates table names each gate (remote checks 27 to 31). The scope lines of CI, pyproject, and the quality guide show which files each gate reads (remote checks 32 to 42). The baseline has no entry for the guard file (remote check 43).
- **Decision**: D-12.

## R10. Changelog fragment

- **Evidence**: The README says a change owns one file, and it allows no fragment for an internal-only change (remote checks 23 and 24). The constitution requires one fragment for each change (remote check 25), and it supersedes other practice documents (remote check 26). The changelog policy test runs in CI (remote check 35).
- **Decision**: D-10.

## R11. Record route

- **Method**: The route script uses base 5 and width 8 (remote checks 45 and 46). Its loop computes each digit by position.
- **Result**: The number 4935 equals `124220` in base 5, so its eight-digit route is `0/0/1/2/4/2/2/0`. The check uses the same method for two records. Issue 4934 equals `124214` and has the route `0/0/1/2/4/2/1/4`, which matches its folder. Issue 4920 equals `124140` and has the route `0/0/1/2/4/1/4/0`, which matches its folder. No folder for 4935 exists (remote check 21).

## R12. Test design

- **Evidence**: The guard defines `_SPECS_ROOT` from `_REPO_ROOT` as a module global (remote check 9). The scan reads that global at call time (remote check 7).
- **Method**: Fixture tests use `monkeypatch` to set both globals to a temporary tree. They use a fixed map for the SDK definitions, so each fixture test skips the full SDK scan.
- **Decision**: D-8.

## R13. Mist API and SDK references

- **Mist API, local OpenAPI**: The operation `listWebhookTopics` appears at `documentation\mist-api-openapi31yaml.yaml` line 2204. The operations `countOrgClientFingerprints`, `getOrg128TRegistrationCommands`, and `listOrgAuditLogsLegacy` appear at lines 10428, 4955, and 12020.
- **SDK, installed package version 0.64.1**: `listWebhookTopics` is defined at `.venv\Lib\site-packages\mistapi\api\v1\const\webhook_topics.py` line 17, with its URI at line 32, `/api/v1/const/webhook_topics`.
- **Documentation drift**: The missing-endpoint catalog lists `listWebhookTopics` as missing (remote check 47). This drift is out of scope (F8).

## R14. Skills

No skill was loaded. The issue concerns a Python test guard. It does not concern Podman behavior or Juniper device behavior, which are the subjects of the skills listed in the brief.

## Decisions

Each decision names the chosen option, the alternatives, the reason, and the risk. No decision requires a human.

- **D-1 Pairing rule**. Chosen: pair each operation line with the next module line in the same spec file. Alternatives: pair by section heading. Accept only an adjacent module line. Reason: the issue states this rule, and the 4934 spec uses adjacent lines. Risk: a distant module line can pair with the wrong operation. The SDK check then reports a mismatch.
- **D-2 Orphan handling**. Chosen: return the operation with no module, and let the failure helper report it. Alternatives: raise an exception, which stops at the first file. Skip the file silently, which is the current defect. Reason: the test then reports every repair at once. Risk: the failure helper must handle the `None` value. Test TST-3 covers that path.
- **D-3 Declared absences**. Chosen: a class attribute `ABSENT_SDK_OPERATIONS` with two entries. Each entry needs a matching spec path and operation, and the SDK must lack the operation. Alternatives: edit spec files 591 and 932 to a sentinel module value. Add the files to the frozen set. Fail both files. Reason: the records keep their historical prose, and the drift check still runs on each pass. A frozen entry would remove the drift check. Risk: the map can grow. The drift check and the reviewer limit that growth.
- **D-4 Spec file 511**. Chosen: declare `mistapi.api.v1.orgs.insights` on line 14 and correct line 15. Alternatives: add the file to the absence map, which the drift check would reject because the SDK defines the operation. Leave `main` red. Reason: R5 shows the SDK defines the operation. Risk: line 69 and FR-001 remain stale. The Out of Scope section covers them.
- **D-5 Stray module lines**. Chosen: ignore a module line with no pending operation line, as the current helper does. Alternative: fail such a line. Reason: the issue limits failures to operation lines, and the survey found zero stray lines. Risk: a second module line for one operation can hide a declaration. The owner decides this later (F11).
- **D-6 Zero-pair failure**. Chosen: fail when the guard examines zero pairs. Alternative: pass with a count of zero, which is the current behavior. Reason: AGENTS requires each guard to prove that it can fail. Risk: none on `main`, because the count is 489.
- **D-7 Count reporting**. Chosen: print one summary line on each run, and begin each failure text with the same line. Alternative: write the count to the logger only. Reason: pytest hides the captured log of a passing test, and R8 shows the repository convention. Risk: a small amount of console output.
- **D-8 Test placement and injection**. Chosen: add fixture tests to the existing guard file, with monkeypatched globals and a fixed SDK map. Alternatives: a new test file, or optional parameters on the scan method. Reason: AGENTS prefers existing files. Monkeypatching lets the pre-change logic run for the proof step, which new parameters would prevent. Risk: global patches must restore after each test. pytest does that for `monkeypatch`.
- **D-9 Logging and comments**. Chosen: apply the inline comment and action logging rules to each changed line and helper. Alternative: keep the sparse comment style of the current file. Reason: AGENTS and constitution Principles VI and VII require both rules. Risk: a longer file.
- **D-10 Changelog fragment**. Chosen: add `changelog.d/issue-4935-mistapi-spec-pairs.md` with one `Fixed` bullet. Alternative: add no fragment, under README rule 4. Reason: R10 shows that the constitution requires one fragment and supersedes the README. Risk: an internal entry appears in the release notes. The owner can remove the fragment.
- **D-11 Scope**. Chosen: change only the guard, lines 14 to 16 of spec file 511, one fragment, and the record. Alternatives: refresh all of spec file 511 in this change. Also correct the missing-endpoint catalog. Reason: AGENTS requires one concern for each issue. Risk: spec file 511 remains partly stale until its separate issue lands.
- **D-12 Gate selection**. Chosen: run each gate that covers a changed file, and record the reason for each other gate. Alternative: run every gate. Reason: each excluded gate has a configuration line that excludes the changed file (R9), so a run adds time but no evidence. Risk: a scope can change later. T-REMOTE-CI runs the full remote CI.

## Sources

- Local paths read: `AGENTS.md`, `.github\copilot-instructions.md`, `.specify\memory\constitution.md`, and the four templates under `.specify\templates`. Also `documentation\quality-gates.md`, `documentation\architecture.md`, `documentation\development-setup.md`, `documentation\container-deployment.md`, and `documentation\operator-guide.md`. Also the Mist API catalogs, `changelog.d\README.md`, `pyproject.toml`, `.github\workflows\ci.yml`, the guard file, and the record of issue 4920 under `specs\numbered\0\0\1\2\4\1\4\0`.
- Remote reads: `gh api` calls to `repos/jmorrison-juniper/MistHelper`. The calls used the ref, trees, contents, and blobs endpoints. The blobs endpoint served as a fallback, and it did not run for the cited files.
- Issue and pull request reads: `gh issue view 4935`, `gh pr list` with the search term 4935 (one merged unrelated pull request), and `gh pr view` for that pull request.
- Local read-only git commands: `rev-parse`, `cat-file -t`, `log -1`, `ls-files -s`, `diff --cached --name-only`, `diff --name-only`, and `hash-object` without `-w`.
- Installed SDK: `.venv\Lib\site-packages\mistapi` and its `mistapi-0.64.1.dist-info` folder.
- Mist API: `documentation\mist-api-openapi31yaml.yaml`.
- Web sources: none. No web read was made.

## Unverified

- The regular-expression SDK simulation in R4 approximates the `ast` scan that the guard uses. The gate run in T-LOCAL-GATES is the authority for the final count.
- The test quality analyzer result for the new tests is not known. The record did not run the analyzer, because the brief forbids tool runs.
- The guard run time is not known. The record did not run the guard.
- The ste-linter score of each record file is not known. The record did not run the linter.
- The dictionary option of ste-linter is not known. The quality guide describes it, but the record did not read that option.
- The remote CI result for the pull request is not known until the pull request exists.
- The constitution outranks the README for fragments by its own statement (remote check 26). The owner has not confirmed that reading.
