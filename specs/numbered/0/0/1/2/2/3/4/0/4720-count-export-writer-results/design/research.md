# Research: Count export write results

Each decision lists what the record chose, why, and which alternatives the record considered. Remote facts were read from `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, which equals the local HEAD, with one recursive tree read. Line numbers come from decoded remote file bodies.

## Method

- One recursive tree read of `main` returned 11,404 entries, with `truncated` false.
- Each cited file body came from `gh api` contents for `main`, decoded from base64. The 4.3 MB OpenAPI file came from the blob endpoint.
- Directory tree SHAs came from `git rev-parse HEAD:<dir>`. HEAD equals `main`, so the tree SHAs match the remote tree.
- Local SDK file SHAs are git blob hashes of the installed files. The SDK is not in the repository tree, so `ref` reads `local-venv`.
- For 24 cited repository files, `git hash-object` matched the remote blob SHA. Local line numbers therefore equal remote line numbers for those files.
- Legacy record: none. A local search found no folder whose name starts with `4720-` under `specs/`. The route folder is absent on `main` (row 50). The draft folder held no earlier draft.
- Linked pull requests: `gh pr list --search 4720` returned no pull request on 2026-11-26.
- Coverage documents `documentation/MIST_API_GET_ENDPOINTS.md` and `documentation/MIST_API_MISSING_ENDPOINTS.md` were searched for count entries. No decision in this record depends on them.

## R1. Judge the writer result by truth value

- **Decision**: Store the result in `written`. Return when `not written`. A false value or `None` takes the failure path (D-1).
- **Rationale**: `write_with_format_selection` declares a Boolean result (remote row 12). PR #4847 used the same check in the sibling site exporters (rows 16 and 17). The issue requires `None` to fail (issue comment, 2026-11-09).
- **Alternatives considered**:
  - Compare with `is True`. It rejects a truthy value that the writer never returns today. It adds a rule that the writer contract does not state.
  - Wrap only the writer call in `try` and `except`. `_dispatch_format_write` already catches write exceptions and returns `False` (rows 14). A wrapper would miss the false result.
- **Risk**: A future writer that returns a truthy non-Boolean value would pass as success. No such value exists today.

## R2. Failure log and failure notice

- **Decision**: On failure, log one `error` line that names the operation, row count, and filename. Print one `info` notice that starts with `! Write failed for` and says not to treat the file as complete (D-2).
- **Rationale**: The error line matches the sibling message (row 16). The notice gives the NOC operator a visible result, and the error line keeps an audit trail.
- **Alternatives considered**:
  - Error log only, as in the sibling site exporters. The operator screen would show no failure notice.
  - Notice only. The log would lose the operation and row count.

## R3. Regression tests in an existing file

- **Decision**: Add class `TestCountWriteOutcomes` to `tests/unit/export/test_count_exporter_workflows.py` (D-3).
- **Rationale**: `tests/unit/export/` holds 55 children (row 53). Principle I forbids a new direct child under a noncompliant parent. The workflow file already holds the entry-point tests (rows 25 and 26).
- **Alternatives considered**:
  - New file `tests/unit/export/test_count_exporter_write_outcomes.py`. It adds a direct child to a noncompliant parent.
  - New package under `tests/unit/export/`. It also adds a direct child.
  - New test module outside `tests/unit/export/`. It splits the count tests across two folders.

## R4. Scope limited to the count exporter

- **Decision**: Change only `CountExporter._persist` and its tests. Other writer call sites stay unchanged (D-4).
- **Rationale**: The issue names menus 235 to 237. One concern belongs in one pull request (`AGENTS.md`, Git flow). The sibling record used the same scope rule (4717 decision D-15).
- **Alternatives considered**:
  - Change every call site in one pull request. The local search found 139 lines in 71 files (Unverified item U-5). That change would exceed one concern.
  - Change the count exporter and the other exporters that use `_persist`. Only `count_exporter.py` contains the count `_persist` (research row 1). No other exporter shares this code.

## R5. Operator guide and changelog, no README change

- **Decision**: Add one operator guide paragraph after line 120. Add one changelog fragment. Do not change `README.md` (D-5).
- **Rationale**: Line 120 already states the failed-write rule for menus 213 and 214 (row 29). The count menus need the same statement. Issue #4916 removed menu references from the README (closed 2026-11-24), and the README names no menus 235 to 237 (row 34). A user-visible fix needs one fragment (`copilot-instructions`, Git and GitHub section).
- **Alternatives considered**:
  - Add menu text to `README.md`. It reverses issue #4916.
  - Add only a changelog fragment. Operators then find no failed-write rule in the guide.

## R6. Candidate patch from the issue comment

- **Decision**: Do not reuse the candidate patch that the issue comment describes. Write the change from repository evidence (D-6).
- **Rationale**: The patch is in a coordinator session, not in the repository. This record cannot inspect it, and the truth order requires repository evidence. The repository pattern from PR #4847 supplies the same fix shape.
- **Alternatives considered**:
  - Adopt the patch after review. The record cannot verify its content, and the comment says it was not applied.
  - Rewrite the change without the PR #4847 pattern. It would diverge from the sibling fix without a reason.

## R7. Publication and merge hold

- **Decision**: Keep T-PR, T-REMOTE-CI, and T-MERGE open. The issue owner holds publication and merge (D-7).
- **Rationale**: The issue body and the comment of 2026-11-09 say to keep publication and merge on hold. The owner already decided this, so the record does not mark it as a human decision.
- **Alternatives considered**:
  - Publish now. It contradicts the issue owner's instruction.
  - Mark the hold as a human decision. The brief limits human decisions to licensing, production data, credential policy, and product priority.

## R8. Branch and worktree

- **Decision**: Create branch `fix/4720-count-export-writer-results` in a new worktree with `git worktree add` (D-8).
- **Rationale**: `AGENTS.md` requires one worktree for each branch (Git flow). The issue comment reports that the Bash branch hook attempts `git checkout -b` before it checks for an existing branch. The hook also uses indirect parameter expansion.
- **Alternatives considered**:
  - Run the Bash branch hook. The issue comment says it was not run, and it changes the branch before it checks for conflicts.
  - Switch the branch in the shared checkout. `AGENTS.md` forbids it in a checkout that another agent uses.

## R9. Route for issue 4720

- **Decision**: Use route `0\0\1\2\2\3\4\0` under `specs\numbered\`. Verify it by base-5 arithmetic and by reading the route script. Run `Resolve-SpecFeaturePath` before T-PR (D-9).
- **Rationale**: The base-5 form of 4720 is 122340. Padded to eight digits, it gives the route 0, 0, 1, 2, 2, 3, 4, 0. The script's `Get-SpecRadixSegments` uses the same arithmetic (row 49). The sibling record for 4717 uses the same rule (row 51). The route folder is absent on `main` (row 50).
- **Check**: The digits 1, 2, 2, 3, 4, and 0 give 4720 in base 5.
- **Alternatives considered**:
  - Run the script now. The brief forbids running a repository script in this stage (Unverified item U-6).
  - Accept the route from the orchestrator without a check. The rule requires a check.

## R10. mistapi pins

- **Decision**: Keep the pins unchanged. `requirements.txt` pins `==0.64.1`, and `pyproject.toml` requires `>=0.64.1,<0.65`. Record the `>=0.64.0` text in `copilot-instructions` as drift (D-10).
- **Rationale**: The installed SDK is 0.64.1 (row 63), which satisfies both texts. Changing a pin is outside this change. The 4717 record recorded the same drift (its decision D-11).
- **Alternatives considered**:
  - Align the `copilot-instructions` text now. It is a documentation fix outside this issue.
  - Change the pin to `>=0.64.0`. It would widen the accepted range without a reason.

## R11. Test runner on the host

- **Decision**: Run tests in the host virtual environment with `python -m pytest`. Use no compose container (D-11).
- **Rationale**: The tests use mocks and need no service. The container policy requires a compose group, an issue-based name, and cleanup (`copilot-instructions`, Containers and ports). A host run avoids that work.
- **Alternatives considered**:
  - Run `scripts\compose.ps1 run --rm misthelper python -m pytest`. The run adds a container with no benefit here.

## R12. Stale MistHelper comment

- **Decision**: Leave the `MistHelper.py` comment at line 585 for a separate issue (D-12).
- **Rationale**: `MistHelper.py` is a hot file. The `copilot-instructions` file says one agent holds an open pull request for it at a time. The comment is outside `_persist`.
- **Alternatives considered**:
  - Correct the comment in this pull request. It adds a second concern to this change.

## R13. Remote commands for held tasks

- **Decision**: Verify T-PR, T-REMOTE-CI, and T-MERGE with `gh` commands. Use no local gate row for them (D-13).
- **Rationale**: The local gates table has no remote row. Issue #4717 used the same rule (its decision D-14).
- **Alternatives considered**:
  - Invent a local gate row for publication. It would misstate the gates table.

## R14. Labels, size, and related issues

- **Decision**: Keep the labels `bug`, `MistHelper.py`, and `in-progress`. Set the size to `S`. Name related issues 1794, 4717, and 1802 (D-14).
- **Rationale**: The issue already holds these labels (issue read, 2026-11-26). The change adds one function fix, one test class, one paragraph, and one fragment. Issue #1794 covers blind exception handlers. Issue #4717 covers the sibling site exporters. Issue #1802 introduced the count family and closed on 2026-08-07.
- **Alternatives considered**:
  - Add a `tests` scope label. The issue names one scope, and the change keeps that scope.

## Remote verification

Rows: 63. Each row maps to one entry in the `remote_checks` array of `META_DIR\4720-STATUS.json`. Result `stale` means the text disagrees with a newer source. Result `absent` means the path has no entry.

| Row | Claim | Path | Ref | SHA | Result | Line |
| - | - | - | - | - | - | - |
| 1 | `_persist` calls the writer and discards its result. `_persist` starts at line 199. | src/operations/exporting/export/count_exporter.py | main | bba22300fdc53aee02e732edefda34eec4cd2b03 | present | 212 |
| 2 | `_persist` prints the success notice without a condition. | src/operations/exporting/export/count_exporter.py | main | bba22300fdc53aee02e732edefda34eec4cd2b03 | present | 216 |
| 3 | `_persist` returns before the writer when no rows exist. | src/operations/exporting/export/count_exporter.py | main | bba22300fdc53aee02e732edefda34eec4cd2b03 | present | 207 |
| 4 | `_run` calls the SDK function and pages the response with `mistapi.get_all`. | src/operations/exporting/export/count_exporter.py | main | bba22300fdc53aee02e732edefda34eec4cd2b03 | present | 233 |
| 5 | `_run` catches `Exception` at line 237 and logs the error at line 238. | src/operations/exporting/export/count_exporter.py | main | bba22300fdc53aee02e732edefda34eec4cd2b03 | present | 238 |
| 6 | Organization table `_ORG_OPS` starts at line 51 and holds 37 rows. | src/operations/exporting/export/count_exporter.py | main | bba22300fdc53aee02e732edefda34eec4cd2b03 | present | 51 |
| 7 | Site table `_SITE_OPS` starts at line 91 and holds 32 rows. | src/operations/exporting/export/count_exporter.py | main | bba22300fdc53aee02e732edefda34eec4cd2b03 | present | 91 |
| 8 | MSP table `_MSP_OPS` starts at line 126 and holds 3 rows. | src/operations/exporting/export/count_exporter.py | main | bba22300fdc53aee02e732edefda34eec4cd2b03 | present | 126 |
| 9 | `org_counts` handler is defined. | src/operations/exporting/export/count_exporter.py | main | bba22300fdc53aee02e732edefda34eec4cd2b03 | present | 242 |
| 10 | `site_counts` handler is defined. | src/operations/exporting/export/count_exporter.py | main | bba22300fdc53aee02e732edefda34eec4cd2b03 | present | 256 |
| 11 | `msp_counts` handler is defined. | src/operations/exporting/export/count_exporter.py | main | bba22300fdc53aee02e732edefda34eec4cd2b03 | present | 270 |
| 12 | `write_with_format_selection` is defined and declares a Boolean result at line 159. | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 153 |
| 13 | `write_with_format_selection` returns the primary result. | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 180 |
| 14 | `_dispatch_format_write` catches a write exception and returns false. | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 150 |
| 15 | The polyglot outcome drives only a warning, not the return value. | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 179 |
| 16 | The site application list exporter keeps the writer result and returns on false (pattern). | src/operations/exporting/export/site_application_list_exporter.py | main | 01cba0e52d5a3a6ced43d3e4b8c2d949cd76a31b | present | 63 |
| 17 | The site system events exporter keeps the writer result and returns on false (pattern). | src/operations/exporting/export/site_system_events_exporter.py | main | 12dcaccad3a704231f66127e6ed1f60e2414d27d | present | 63 |
| 18 | `MistHelper.py` imports `CountExporter`. | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 584 |
| 19 | Menu 235 entry uses `CountExporter.org_counts`. | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4360 |
| 20 | Menu 236 entry uses `CountExporter.site_counts`. | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4368 |
| 21 | Menu 237 entry uses `CountExporter.msp_counts`. | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4376 |
| 22 | The comment at line 585 states 70 count endpoints. The tables hold 72. | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 585 |
| 23 | Menus 235 to 237 are `interactive_safe` in the registry. | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 303 |
| 24 | The count test module holds the persist tests. | tests/unit/export/test_count_exporter.py | main | abd5134dbca0f948823607b8a13d0776af3b3b72 | present | 120 |
| 25 | The workflow test module defines the `fake_mh` fixture. | tests/unit/export/test_count_exporter_workflows.py | main | c29ffe0a2a28bae59df4e294bb917c385c6fe340 | present | 24 |
| 26 | The workflow test module holds class `TestOrgCounts`. | tests/unit/export/test_count_exporter_workflows.py | main | c29ffe0a2a28bae59df4e294bb917c385c6fe340 | present | 103 |
| 27 | The site test module holds class `TestSiteWriteOutcomes`. | tests/unit/export/test_site_asset_and_events_exporters.py | main | a2aa37e006a3265a70422c2bbca32faecacf030c | present | 322 |
| 28 | The contract guard requires `api_function_name` on each writer call. | tests/contract/test_export_api_function_names.py | main | 53f0238a6a248a75283120cf93099527349add8a | present | 25 |
| 29 | The operator guide states the failed-write rule for menus 213 and 214. | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 120 |
| 30 | The menu reference lists menus 235 to 237 with counts 37, 32, and 3. | documentation/menu_reference.md | main | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 271 |
| 31 | The quality gates page holds the writing gate section. | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 277 |
| 32 | The changelog fragment for issue 4717 holds a Fixed bullet. | changelog.d/issue-4717-site-export-writer-results.md | main | daee06e8a274a98f7b06a70f34143e0e3f7a3441 | present | 3 |
| 33 | The changelog rules name the issue-only file form. | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| 34 | The README names no menus 235 to 237. | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| 35 | The copilot instructions hold the Local gates section. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| 36 | The gate rows from Compile to Menu reference start at line 57. The Symbols row is at line 73 and the STE row at line 74. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| 37 | The test quality ratchet section exists. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| 38 | The copilot instructions pin mistapi at `>=0.64.0,<0.65`. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| 39 | The copilot instructions name the Python 3.15.2 bootstrap. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 28 |
| 40 | `pyproject.toml` requires Python `>=3.15`. | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| 41 | `pyproject.toml` pins mistapi `>=0.64.1,<0.65`. | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| 42 | `requirements.txt` pins mistapi `==0.64.1`. | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| 43 | The CI type check scope includes `src/`. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 44 | The CI dead-code scope includes `src/`. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| 45 | The CI docstring style scope includes `src/`. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| 46 | The CI docstring coverage scope includes `src/`. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| 47 | The CI pylint gate runs on `SRC_PATH` with the 9.5 threshold. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 529 |
| 48 | Principle I forbids a new direct child under a noncompliant parent. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 42 |
| 49 | The route script defines the base-5 segment function. | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| 50 | The route folder `specs/numbered/0/0/1/2/2/3/4/0` holds no entries. The SHA is that of its parent folder. | specs/numbered/0/0/1/2/2/3/4/0 | main | d98eafc320dff5952d225f214b52e60c4e2dc7b4 | absent | 0 |
| 51 | The sibling record for issue 4717 exists. | specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/spec.md | main | 7affd7ec04391168ebd3b494d106152d012d4d71 | present | 1 |
| 52 | The parent route folder `specs/numbered/0/0/1/2/2/3` holds three children (0, 2, and 3). | specs/numbered/0/0/1/2/2/3 | main | d98eafc320dff5952d225f214b52e60c4e2dc7b4 | present | 0 |
| 53 | `tests/unit/export` holds 55 children. | tests/unit/export | main | f87e46d24e73c34cda279cc88a5dfd16c26d55e4 | present | 0 |
| 54 | `src/operations/exporting/export` holds 49 children. | src/operations/exporting/export | main | a0956c911946e08c84fee7a003099c7dc5f60a1e | present | 0 |
| 55 | The changelog fragment guard test exists. | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| 56 | The test quality preflight test exists. | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 0 |
| 57 | The STE linter configuration exists. | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| 58 | The cited commit `3964d21d` exists on GitHub. The SHA column holds its tree SHA. | commit 3964d21d03f9f5717cb8eafb7272ecff21f5362a | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | b89d20f534a27dfa39cdf8fdb4bf6afe10e4d2d6 | present | 0 |
| 59 | The local OpenAPI file defines operation `countOrgDevices`. | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 8462 |
| 60 | The installed SDK defines `countOrgDevices` with a session and an organization identifier. | .venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py | local-venv | 90fe126e9c3e34d7784644016e12833b7359737d | present | 42 |
| 61 | The installed SDK defines `get_all` with a session and a response. | .venv\Lib\site-packages\mistapi\__pagination.py | local-venv | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 39 |
| 62 | The installed SDK re-exports `get_all`. | .venv\Lib\site-packages\mistapi\__init__.py | local-venv | f6fca30f4088d763e76f3072d02a3095d46852b9 | present | 15 |
| 63 | The installed SDK version is 0.64.1. | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local-venv | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |

## Sources

Remote reads (`gh`, read only, 2026-11-26):

- Issue #4720 body and comment `IC_kwDOQltU8c8AAAABkmNIkA` (2026-11-09). Labels `bug`, `MistHelper.py`, and `in-progress`. https://github.com/jmorrison-juniper/MistHelper/issues/4720
- PR #4847, merged 2026-11-19 with merge commit `db06604d18d832c25edb60eaa2edac6c72cea4cc`. It fixed the sibling site exporters for issue #4717. https://github.com/jmorrison-juniper/MistHelper/pull/4847
- PR #4242, merged 2026-10-16 with merge commit `351871c4345405cdd035b043b046f046f192ddc1`. It completed the SDK count catalog. https://github.com/jmorrison-juniper/MistHelper/pull/4242
- PR #4813, open, has 15 changed files, including `data_exporter.py`. It overlaps this change only at `data_exporter.py`, which this change reads and does not edit. https://github.com/jmorrison-juniper/MistHelper/pull/4813
- Issue #1802, closed 2026-08-07. It introduced the count-endpoint family. https://github.com/jmorrison-juniper/MistHelper/issues/1802
- Issue #1794, open. It covers blind exception handlers. https://github.com/jmorrison-juniper/MistHelper/issues/1794
- Issue #4717, open. It covers the sibling site exporters, and its fix PR merged on 2026-11-19. https://github.com/jmorrison-juniper/MistHelper/issues/4717
- Issue #4916, closed 2026-11-24. It removed menu references from the README. https://github.com/jmorrison-juniper/MistHelper/issues/4916
- Branch protection on `main` through `repos/jmorrison-juniper/MistHelper/branches/main/protection/required_status_checks`. The `strict` value is true. The API lists 15 required contexts:
  - Black (format check), mypy (strict), pytest (coverage gate), Bandit (security), and pip-audit (CVE scan).
  - Pylint (score gate), Radon (complexity), Vulture (dead code), pydocstyle (docstring style), and Interrogate (docstring coverage).
  - Diagram reference lint, E2E smoke tests, Ruff (lint), CodeQL, and pytest (ops platform).
- Open pull requests (7). Only PR #4813 overlaps the change set, at `data_exporter.py`.

Local sources:

- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the four templates under `.specify/templates/`.
- `documentation/quality-gates.md`, `documentation/operator-guide.md`, `documentation/menu_reference.md`, `documentation/architecture.md`, `documentation/development-setup.md`, and `documentation/container-deployment.md`. The last two hold no rule that changes this record, except the container policy named in D-11.
- `changelog.d/README.md` and `changelog.d/issue-4717-site-export-writer-results.md`.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`. Its shape and depth guided this record. Its content did not.
- Installed SDK: `.venv\Lib\site-packages\mistapi\` and `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\`.

Web sources: none fetched. No local source was missing.

Skills: none loaded. The issue concerns Python export code. It does not concern Podman, Juniper device behavior, or container runtimes.

## Unverified

- U-1. The candidate patch and regression test in the coordinator session (issue comment `IC_kwDOQltU8c8AAAABkmNIkA`). The patch is not in the repository, so the record did not inspect it and did not rely on it.
- U-2. The claim that six `False` and `None` cases fail on the original source. Brief rule 2 forbids running tests in this stage. Code reading supports the claim (rows 1 and 2).
- U-3. The claim that two non-merged local branches hold the earlier count-catalog change. The record did not check the local branches, and no decision depends on them.
- U-4. The claim that the managed Spec Kit route is unavailable on the issue host because PowerShell is missing. This host has PowerShell. The record did not check the claim, and no decision depends on it.
- U-5. The count of 139 unassigned writer call lines in 71 files. The source is a local working tree search. Five tracked files differ from `main` in the working tree (`git status`), and the record did not check each call site on `main`. The count only sizes the out-of-scope item A-4.
- U-6. The run of `Resolve-SpecFeaturePath` under pwsh. Brief rule 2 forbids running a repository script in this stage. The route follows from the arithmetic in R9 and from row 49.
- U-7. The shard durations (1179.3 seconds and 366.3 seconds) from `copilot-instructions`. The record did not measure them.
- U-8. The ste-linter scores of the changed files. The score runs in T004 and in `design/quickstart.md` Scenario 8.
- U-9. The return path of the SQLite writer. The record read only the caller. The truth-value test handles a Boolean or `None` result either way.
