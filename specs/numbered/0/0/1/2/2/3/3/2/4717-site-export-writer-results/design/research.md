# Research: Site export write results (issue #4717)

## Summary

Remote `main` holds the repair. PR #4847 merged it on 2026-11-19 as commit `db06604d18d832c25edb60eaa2edac6c72cea4cc`. Both persistence methods check the writer result, and both menus have tests. Four gaps remain. The touched statements lack inline comments. The offline proof is not in the repository. The route check with `Resolve-SpecFeaturePath` did not run. The issue is still open. Each claim below cites remote evidence, unless it appears in the Unverified list.

## Remote Verification

Every row cites `main`. Each blob SHA came from `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main --jq .sha`. Each line range came from the decoded raw text of the same ref.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| 1 | Application list persistence checks the writer result | `src/operations/exporting/export/site_application_list_exporter.py` | main | `01cba0e52d5a3a6ced43d3e4b8c2d949cd76a31b` | present | 63-68 |
| 2 | System event persistence checks the writer result | `src/operations/exporting/export/site_system_events_exporter.py` | main | `12dcaccad3a704231f66127e6ed1f60e2414d27d` | present | 63-68 |
| 3 | Shared test class `TestSiteWriteOutcomes` exists | `tests/unit/export/test_site_asset_and_events_exporters.py` | main | `a2aa37e006a3265a70422c2bbca32faecacf030c` | present | 322-435 |
| 4 | Writer returns `bool` | `src/operations/exporting/export/data_exporter.py` | main | `f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411` | present | 153-180 |
| 5 | Menu 213 handler is `application_list` | `MistHelper.py` | main | `98d7828479ded6bc4c83d15e0c1847171cfbfd49` | present | 4174-4181 |
| 6 | Menu 214 handler is `system_events` | `MistHelper.py` | main | `98d7828479ded6bc4c83d15e0c1847171cfbfd49` | present | 4182-4189 |
| 7 | Menus 213 and 214 are `interactive_safe` | `src/foundation/support/utils/operation_registry.py` | main | `ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891` | present | 281-282 |
| 8 | Operator guide documents failed-write behavior | `documentation/operator-guide.md` | main | `60d28f9ea461fc8798973d1d1b7e40491c27c248` | present | 120 |
| 9 | Menu reference lists menus 213 and 214 | `documentation/menu_reference.md` | main | `2bd972183c64302e76442d30669bb9e7362856f1` | present | 249-250 |
| 10 | README text for menus 213 and 214 | `README.md` | main | `331a4567f72156fe2a3e3ee91005d2cbbcaed6d0` | stale | none, file has 136 lines |
| 11 | Changelog fragment exists | `changelog.d/issue-4717-site-export-writer-results.md` | main | `daee06e8a274a98f7b06a70f34143e0e3f7a3441` | present | 1-3 |
| 12 | Endpoint strategy for the application list | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | main | `3547991028bdbe955e1ba6c8a6bf3082240f2af8` | present | 483-489 |
| 13 | Endpoint strategy for system events | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | main | `3547991028bdbe955e1ba6c8a6bf3082240f2af8` | present | 520-526 |
| 14 | Site prompt helper `_resolve_site_for_stats` | `src/operations/exporting/export/site_device_exporter.py` | main | `f9fd54c69b9458df6182b6142c63bf15b012bb1a` | present | 130-146 |
| 15 | Flatten and escape helpers | `src/foundation/models/data/data_processing_utils.py` | main | `f0e53336717eefbbe0bf7b4136b3e0d4f11f3847` | present | 66, 156 |
| 16 | Resolver returns test host values | `src/foundation/runtime/config/source_dependency_resolver.py` | main | `18c0e2b88560614a4c987510032fea4946b0fc7c` | present | 154-160, 242-270 |
| 17 | Draft spec in the record folder | `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results/spec.md` | main | `7affd7ec04391168ebd3b494d106152d012d4d71` | partial | whole file (draft) |
| 18 | Route directory holds one child | `specs/numbered/0/0/1/2/2/3/3/2` | main | `d00e5cd0f56b97091ccc012207c21a9f31459062` | present | none, directory |
| 19 | Process folder guard limits children to five | `tests/guardrails/test_process_folder_structure.py` | main | `f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5` | present | 32-34 |
| 20 | Route contract guard | `tests/guardrails/test_spec_route_contract.py` | main | `b174399ad5f23f4844dc442954bf203be07342f3` | present | 33-42, 64-77 |
| 21 | Route helper algorithm | `.specify/scripts/powershell/spec-route.ps1` | main | `37293a255f9b5de20ccb2b3ef0ad15717bab2826` | present | 17-31, 34-52 |
| 22 | Changelog guard checks the fragment name | `tests/guardrails/test_changelog_fragment_policy.py` | main | `dbd5e8776797f12536b3bc2bd613143b85f3fc4a` | present | 39, 192-197 |
| 23 | Socket guard in project configuration | `pyproject.toml` | main | `eca34c826ea44ba4f2faefc07d04c2c117e99751` | absent | none, `[tool.pytest.ini_options]` at line 510 has no socket setting |
| 24 | Pinned `mistapi` version | `requirements.txt` | main | `50fe63d4cf5e6071612c62c288e965190c60b969` | present | 129 |
| 25 | Allowed `mistapi` range | `pyproject.toml` | main | `eca34c826ea44ba4f2faefc07d04c2c117e99751` | present | 29 |
| 26 | Required Python version | `pyproject.toml` | main | `eca34c826ea44ba4f2faefc07d04c2c117e99751` | present | 23 |
| 27 | Pin text in the Copilot instructions | `.github/copilot-instructions.md` | main | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | stale | 21 (states `>=0.64.0`) |
| 28 | CI path variables | `.github/workflows/ci.yml` | main | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 93, 101, 104, 107 |
| 29 | Latest commit on the three owned paths | `src/operations/exporting/export/site_application_list_exporter.py`, `site_system_events_exporter.py`, and the test module | main | commit `db06604d18` | present | commit list, 2026-11-19 |
| 30 | Candidate commit from the issue thread | `5501a141ca1273c4a242e23771b0740fcb30ab29` | archive branch | commit exists | absent from `main` | compare `5501a141` with `main`: `main` is 88 commits ahead and 1 behind. Merge base `3964d21`. |

Notes for the table:

- Row 10 is stale. Commit `0788b975ea` on 2026-11-24 (PR #4918) removed menu references from `README.md`. The file on `main` has no text for menus 213 or 214.
- Row 17 is partial. The draft exists, but several claims in it are stale or absent. See the verdict table below.
- Row 23 is absent. `pyproject.toml` lines 510-523 set no socket guard, and `requirements-dev.txt` lists no socket plugin.
- Row 27 is stale. `pyproject.toml` line 29 and `requirements.txt` line 129 both match version 0.64.1. The Copilot instructions line 21 and the brief state `>=0.64.0`.
- Row 30 is absent from `main`. The commit lives on `archive/laptop-20261121/jmorrison-juniper-site-export-writer-results`. That archive branch diverged from the base commit.

## Local Evidence

This evidence does not prove committed state. It supports the remote rows above.

- `git rev-parse HEAD` in the local checkout names `f03c6c9b3`. The GitHub `main` commit is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The short hashes match.
- `git rev-parse HEAD:<path>` returns the same blob SHA as the remote API for the three owned paths (rows 1 to 3).
- The base commit `3964d21d03f9f5717cb8eafb7272ecff21f5362a` exists in local git. Its exporter blobs (`3feee36440202307534c05985425862629461a97` for the application list) differ from `main`. The base version calls the writer at lines 62-64 and ignores its result.
- The merge commit `db06604d18d832c25edb60eaa2edac6c72cea4cc` exists in local git.
- The installed `mistapi` package is version 0.64.1 (`.venv\Lib\site-packages\mistapi-0.64.1.dist-info`).

## Issue Facts and Linked Pull Requests

Issue #4717 (GitHub, read with `gh issue view` on 2026-11-26):

- State: OPEN. Last update 2026-11-10T10:07:35Z. Author: `jmorrison-juniper`.
- Labels: `bug`, `MistHelper.py`, and `in-progress`.
- Comments: three. The IDs are `IC_kwDOQltU8c8AAAABkhNNKA` (2026-11-09T16:43:18Z), `IC_kwDOQltU8c8AAAABkhjOeg` (2026-11-09T16:57:22Z), and `IC_kwDOQltU8c8AAAABkzNK-w` (2026-11-10T10:07:35Z).
- Base commit in the issue: `3964d21d03f9f5717cb8eafb7272ecff21f5362a`.
- Reproduction steps in the issue. Step 1 supplies one synthetic row to each persistence method. Step 2 replaces the shared writer with a mock that returns `False`. Step 3 captures the persistence and export messages. Step 4 repeats with a successful writer, empty input, and a writer exception.
- Error text in the issue for the application list: `getSiteApplicationList persisted 1 rows to SiteApplicationList_Synthetic_Site.csv` and `! 1 application records exported to SiteApplicationList_Synthetic_Site.csv`.
- Error text in the issue for system events: `searchSiteSystemEvents persisted 1 rows to SiteSystemEvents_Synthetic_Site.csv` and `! 1 system event records exported to SiteSystemEvents_Synthetic_Site.csv`.
- Issue counters: `Independent baseline: 2 failed, 6 passed` and `Offline guard attempts: socket=0, dns=0, sqlite=0`. These counters have no repository evidence (U-1).

Linked pull requests (`gh pr list --search 4717` and `gh pr view 4847`):

- PR #4847: state MERGED. Merged 2026-11-19T20:28:35Z. Closing references: none.
- PR #4847 details: head `fix/4717-site-export-writes`, base `main`, merge commit `db06604d18d832c25edb60eaa2edac6c72cea4cc`.
- PR #4847 body states: "Refs #4717. This PR does not close the issue."
- PR #4847 files: nine paths. They are the three owned source and test paths, the changelog fragment, the README, and four record files.
- PR #4847 checks: every gate in the rollup reports SUCCESS.
- Open pull requests: seven on 2026-11-26. PR #4813 (`jmorrison-juniper-csv-carriage-return-preservation`) touches `src/operations/exporting/export/data_exporter.py`, which is the shared writer, and it does not touch the owned paths. No open pull request touches the three owned paths.

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. Human decisions are not required. Each decision is within the authority of this record.

### R-1 Repair of record (D-1)

- **Alternatives**: (a) Implement the writer result check again on a new branch. (b) Accept merged PR #4847 as the repair and verify it.
- **Chosen**: (b).
- **Reason**: Rows 1 and 2 show the check on `main`. PR #4847 passed its CI checks, as recorded in the PR rollup.
- **Risk**: The code depends on the writer `bool` contract. Mitigation: `design/contracts/writer-result.md`.

### R-2 Comment repair scope (D-2)

- **Alternatives**: (a) Add comments to every statement in both exporter modules and the test module. (b) Add comments only to touched statements.
- **Chosen**: (b).
- **Reason**: `AGENTS.md` line 97 and the constitution Principle VI require comments on the touched block. The smallest diff satisfies the rule. Lines 58, 67, and 68 in both exporters, and 27 lines in the test class, are the touched statements.
- **Risk**: Untouched methods keep their gaps (analysis F-13).

### R-3 Offline harness location (D-3)

- **Alternatives**: (a) Add an autouse fixture and self-test functions to the shared test module. (b) Add a new guard test module under `tests/unit/export/`. (c) Keep the harness outside the repository in `test-artifacts/`.
- **Chosen**: (c).
- **Reason**: The shared module holds more than five top-level names (row 3, and E-25). Adding a name adds a violation to a noncompliant parent. The folder `tests/unit/export/` holds 55 children on `main`. A new module there also breaks the rule. `test-artifacts/` is git-ignored by design (`.github/copilot-instructions.md` line 339).
- **Caution**: the harness does not run in CI. Mitigation: T-PR records the harness output in the pull request body.

### R-4 Route check (D-4)

- **Alternatives**: (a) Run `spec-route.ps1` during authoring. (b) Compute the route by hand now, and require a `pwsh` run before closure. (c) Skip the check.
- **Chosen**: (b).
- **Reason**: The brief forbids running repository scripts during authoring. The owner named the check as a closure gate in the issue thread (comment at 2026-11-10T10:07:35Z). Hand computation matches the algorithm: base 5, eight digits, value 4717, digits `0 0 1 2 2 3 3 2`. The same arithmetic appears in `python_route` (`test_spec_route_contract.py` lines 33-42).
- **Caution**: an arithmetic error would pass this check. Mitigation: T011 runs the script under `pwsh`.

### R-5 README and operator guide (D-5)

- **Alternatives**: (a) Restore the README paragraph. (b) Keep the README without menu text and rely on the operator guide.
- **Chosen**: (b).
- **Reason**: PR #4918 closed issue #4916 on purpose. The commit message states that menu details move to `documentation/operator-guide.md`. Row 8 shows the failed-write text in that file.
- **Risk**: The constitution README rule requires an update for each operation change. The rule and the later decision disagree (analysis F-07). Mitigation: record the conflict for the owner. No change in this issue.

### R-6 Changelog fragment (D-6)

- **Alternatives**: (a) Add a new fragment for the comment and harness changes. (b) Keep the existing fragment and add none.
- **Chosen**: (b).
- **Reason**: `changelog.d/README.md` rule 4 (line 58) says an internal change needs no fragment. The guard accepts the existing name (row 22).
- **Risk**: None found.

### R-7 Record slug (D-7)

- **Alternatives**: (a) Use a new slug. (b) Reuse the draft slug `site-export-writer-results`.
- **Chosen**: (b).
- **Reason**: The draft folder already uses this slug on `main`. Reuse keeps one record for one route.
- **Caution**: a reader might confuse the old and new drafts. Mitigation: the Clarifications section in `spec.md`.

### R-8 Publication authority (D-8)

- **Alternatives**: (a) Treat the 2026-11-10 hold as active. Close nothing. (b) Treat the owner merge on 2026-11-19 as publication. Gate only closure on evidence.
- **Chosen**: (b), with T-MERGE gated on orchestrator authorization.
- **Reason**: The owner account `jmorrison-juniper` opened PR #4847 and merged it, with no review (PR metadata). The pull request body says publication is authorized. No issue comment after 2026-11-10 lifts the hold, so the record names this gap. The merge event is the stronger evidence.
- **Caution**: the route gap stayed open when the merge occurred. Mitigation: T011 must pass before T-MERGE.

### R-9 Closure mechanism (D-9)

- **Alternatives**: (a) Close the issue by hand. (b) Name `Closes #4717` in the T-PR body. (c) Keep the issue open with no merge.
- **Chosen**: (b).
- **Reason**: `.github/workflows/close-linked-issues.yml` closes an issue that a merged pull request names (`.github/copilot-instructions.md`, workflow table). Caution: a manual close bypasses the evidence trail.
- **Risk**: None found.

### R-10 Menu dry run (D-10)

- **Alternatives**: (a) Run menus 213 and 214 against the live Mist cloud. (b) Use mocked menu entry-point tests.
- **Chosen**: (b).
- **Reason**: Issue #4717 says "Do not call Mist." The `wired` fixture drives both menu entry points through mocks (test lines 28-74 and 322-435). The SDK signatures and endpoint paths are cited in `design/contracts/mist-api-calls.md`.
- **Caution**: no live proof that the SDK arguments match the live API. Mitigation: the contract cites the SDK source and the OpenAPI file.

### R-11 `mistapi` pin (D-11)

- **Alternatives**: (a) Change `pyproject.toml` to `>=0.64.0,<0.65`. (b) Keep `>=0.64.1,<0.65` and record the drift.
- **Chosen**: (b).
- **Reason**: `pyproject.toml` line 29 and `requirements.txt` line 129 agree on 0.64.1. The brief and the Copilot instructions are the outliers. The change is out of scope.
- **Risk**: Documentation drift remains (row 27). Mitigation: analysis F-10 for a later docs change.

### R-12 Test module debt (D-12)

- **Alternatives**: (a) Split the shared test module now. (b) Defer the split to a separate issue.
- **Chosen**: (b).
- **Reason**: The split changes files outside the owned set for this issue. Owned paths are fixed by the issue comment at 2026-11-09T16:43:18Z.
- **Caution**: the debt grows with each new exporter test. Mitigation: a separate issue (plan, Complexity Tracking).

### R-13 Truth-value check (D-13)

- **Alternatives**: (a) Use `if success is not True`. (b) Use `if not success`.
- **Chosen**: (b).
- **Reason**: The writer returns `bool` (row 4). The existing code style uses truth values in this module.
- **Caution**: a truthy non-Boolean value counts as success. The writer contract prevents that value (`design/contracts/writer-result.md`).

### R-14 Remote verification for final tasks (D-14)

- **Alternatives**: (a) Invent a local command for each final task. (b) Use the remote commands from `AGENTS.md` for T-PR, T-REMOTE-CI, and T-MERGE.
- **Chosen**: (b).
- **Reason**: The local gates table has no remote row. The `gh` commands match `AGENTS.md` sections "Pull request" and "Merge".
- **Risk**: The brief rule for one local verification command is not met literally for these three tasks. The tasks state this exception in `tasks.md`.

### R-15 Scope of other callers (D-15)

- **Alternatives**: (a) Audit every writer caller now. (b) Limit the issue to the two site exports and name the audit in a separate issue.
- **Chosen**: (b).
- **Reason**: Issue #4717 states its scope. It reads: "It does not claim that all exporter calls have been audited." Row 29 confirms that `main` holds no broader change.
- **Caution**: other exporters can keep the same defect. Mitigation: analysis F-15 recommends a separate audit issue linked to #1794.

## Existing Record Verification

The draft on `main` holds four files. They are `spec.md`, `plan.md`, `tasks.md`, and `design/checklists/requirements.md`. Each claim below received one verdict. Verdicts follow the brief rules. A verdict of `verified` means remote or repository evidence supports the claim. A verdict of `stale` means evidence contradicts the claim or predates the merge. A verdict of `absent` means the repository holds no evidence.

| ID | Claim in the draft | Verdict | Evidence |
| - | - | - | - |
| E-01 | Status says "Publication is authorized." | stale | Merged on 2026-11-19. Status text predates the merge. |
| E-02 | Feature Branch is `jmorrison-juniper-site-export-writer-results` | stale | The merged branch is `fix/4717-site-export-writes`. |
| E-03 | Failed write logs an error with endpoint and filename | verified | Rows 1 and 2. Test lines 358-372. |
| E-04 | Failed write produces no persistence or export success message | verified | Lines 66-68. Test lines 373-374. |
| E-05 | Successful write keeps both success messages | verified | Lines 69-72. Test lines 376-397. |
| E-06 | Empty response does not call the writer | verified | Lines 56-58. Test lines 399-414. |
| E-07 | Writer exception reaches the menu error handler | verified | `application_list` lines 89-98. Test lines 416-435. |
| E-08 | Persistence methods and menu entry points return `None` | verified | Test assertions at lines 365, 388, 406, and 424. |
| E-09 | Filename, transforms, row count, and endpoint name are unchanged | verified | Lines 59-64. Test lines 389-393. |
| E-10 | Shared pagination and other exporters are unchanged | verified | PR #4847 changed nine paths. None holds pagination code. |
| E-11 | Socket, DNS, and SQLite access is blocked | absent | Row 23. No harness in the repository. |
| E-12 | Six independent controls pass | absent | Controls exist only in the issue harness. The repository holds 12 control cases. |
| E-13 | Zero socket, DNS, and SQLite attempts | absent | No repository evidence. |
| E-14 | Shared tests pass without changes to another issue file | verified | PR #4847 changed only reserved paths. CI passed. |
| E-15 | Local commit stays available without publication | stale | Publication occurred on 2026-11-19. |
| E-16 | Writer returns a Boolean | verified | Row 4. |
| E-17 | Base commit is `3964d21d03f9f5717cb8eafb7272ecff21f5362a` | verified | Local git evidence. |
| E-18 | An app-managed branch replaces the branch hook | absent | No repository evidence. |
| E-19 | Route follows the eight-digit base-5 algorithm | verified | Row 21 and the arithmetic in R-4. |
| E-20 | PowerShell is unavailable | absent | Environment claim. The repository does not show it. |
| E-21 | Active specification selector stays unchanged | absent | No repository evidence. |
| E-22 | Persistence methods discard the writer result | stale | True on the base commit only. Rows 1 and 2 show the check on `main`. |
| E-23 | No dependency, schema, transport, or signature change | verified | PR #4847 changed no dependency file. |
| E-24 | The repair changes only the reserved methods | verified | PR #4847 diff is +5 and -1 per source file. Rows 1 and 2. |
| E-25 | Shared test module exceeds five top-level names | verified | Top-level definitions at lines 28, 77, 100, 150, 175, 200, 256, 286, and 322. |
| E-26 | New test class has five members | verified | Fixture at line 334 and tests at lines 358, 376, 399, and 416. |
| E-27 | Source modules hold more than five module-level names | absent | Each exporter holds one class and one logger. The claim is imprecise. |
| E-28 | 27 open pull requests and no overlap | stale | Seven open pull requests on 2026-11-26. None touches the three paths. |
| E-29 | Public reservation is issue comment 6745705768 | verified | Comment URL `issuecomment-6745705768` on issue #4717. |
| E-30a | Tasks T001 to T007 are complete, with session artifacts | absent | Artifacts are outside the repository. |
| E-30b | Task T008 prepares a local commit | stale | The commit merged in PR #4847. |
| E-31 | Baseline has 2 failed and 6 passed cases | absent | Reproduction exists only in the harness. The issue body states the numbers. |
| E-32 | Guard results show 29 passes and one skip | absent | No repository evidence. |
| E-33 | Pylint scores are 9.92, 9.49, and 9.43 | absent | CI reports the pass state only. |
| E-34a | Lint, format, types, compile, security, complexity, docstrings, STE, and links pass | verified | CI rollup for PR #4847: Ruff, Black, mypy (strict), Bandit, Radon, pydocstyle, Interrogate, ste-lint, Citation reference lint, and Mermaid lint are SUCCESS. |
| E-34b | Symbol gate passes | absent | `symbol-diff` is not in the CI rollup. The claim is local only. |
| E-35 | Test-quality scan reports zero new findings | verified | CI check "Test quality ratchet (gate)" is SUCCESS. |
| E-36 | 692 paths across 27 pull requests show no overlap | stale | Seven open pull requests now. The overlap check on 2026-11-26 found none. |
| E-37 | Changelog fragment exists | verified | Row 11. |
| E-38 | README lists menus 213 and 214 | stale | Row 10. PR #4918 removed the menu text. |
| E-39 | Session artifacts preserve commands and output | absent | Outside the repository. |

Totals: 41 claims. 20 verified. 8 stale. 13 absent.

## Sources

Local sources are read from the repository or the installed packages. No `web_fetch` call was needed, because the local sources answered each question.

- `AGENTS.md` (remote blob `44a9afffb5bd6f774973a845d27343e4e528b6ad`): writing style lines 40-61, inline comments lines 97-103, action logging lines 104-116, git flow lines 179-241, preserve work lines 271-277.
- `.github/copilot-instructions.md` (remote blob `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179`): pin line 21, local gates lines 57-74, pytest-chunks lines 87-88.
- `.github/copilot-instructions.md` (same blob): test quality ratchet line 95, Spec Kit layout lines 159-167, categories lines 219-227, test-artifacts row line 339.
- `.specify/memory/constitution.md` (remote blob `4584997a264c5a7ade2ca7441246e1f067083aa1`): Principle I lines 38-90, Principle VI lines 204-234, Principle VII lines 235-273, technology lines 274-336.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md` (local): headings and required sections.
- Reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` (local): shape only. It holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/` with `data-model.md`, `quickstart.md`, `research.md`, `contracts/`, and `checklists/`.
- `documentation/development-setup.md` lines 28-44 (venv activation and bootstrap). `documentation/quality-gates.md` lines 57-58 (pip-audit and pylint rows). `documentation/architecture.md` line 258 (exporting package row).
- `documentation/mist-api-openapi31yaml.yaml` (local): `/api/v1/sites/{site_id}/events/system/search` at lines 32015-32020, and `/api/v1/sites/{site_id}/wxtags/apps` at lines 43213-43216.
- `documentation/MIST_API_GET_ENDPOINTS.md` (local): rows at lines 1245 and 1661.
- `.venv\Lib\site-packages\mistapi\api\v1\sites\wxtags.py` lines 89-106 (`getSiteApplicationList`).
- `.venv\Lib\site-packages\mistapi\api\v1\sites\events.py` lines 134-144 (`searchSiteSystemEvents`).
- `.venv\Lib\site-packages\mistapi\__pagination.py` line 39 (`get_all`), and `mistapi\__init__.py` line 15 (export).
- `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` (installed version).
- Issue #4717 (GitHub): comments `IC_kwDOQltU8c8AAAABkhNNKA` (2026-11-09), `IC_kwDOQltU8c8AAAABkhjOeg` (2026-11-09), and `IC_kwDOQltU8c8AAAABkzNK-w` (2026-11-10).
- PR #4847 (merged 2026-11-19, merge commit `db06604d18`). PR #4918 (commit `0788b975ea`, closes #4916).
- `changelog.d/README.md` (remote blob `fcbde10e0c293390bd9df8d62a5d61f158eca384`): name rule lines 19-21, keep-name rule lines 32-34, internal-change rule line 58.

## Unverified

Each item below lacks repository or remote evidence. Each item states the reason.

- U-1: Harness results (2 failed and 6 passed, 43 cases, 321 cases, zero socket, DNS, and SQLite attempts). Reason: the harness is outside the repository, and its output is not stored there.
- U-2: Exact Pylint scores (9.92, 9.49, and 9.43). Reason: CI logs were not read. Only the pass state was read.
- U-3: Session artifacts and their commands. Reason: outside the repository.
- U-4: Ownership scan of 692 paths. Reason: the scan method is not in the repository. This record checked only the open pull requests.
- U-5: PowerShell is unavailable on the author machine. Reason: an environment fact that the repository does not show.
- U-6: Application list response fields and the suitability of `misthelper_internal_id` as a primary key. Reason: the response schema was not read.
- U-7: Live behavior of menus 213 and 214. Reason: issue #4717 forbids Mist calls.
- U-8: Behavior of the polyglot mirror under failure. Reason: out of scope. The record read `data_exporter.py` lines 176-198 only.
- U-9: Other writer callers that ignore the result. Reason: no audit was run.
- U-10: Whether the owner lifted the publication hold outside GitHub. Reason: no record exists in the repository or the issue thread.
- U-11: Whether archive branch head `5501a141` matches the content in PR #4847. Reason: the branches diverged, and no content comparison was run.
- U-12: The exit code of `symbol-diff` for an added class. Reason: the tool did not run in this session. The PR author states exit code 1.

## Skills

No skill was loaded. The issue concerns Python exporters and a test module. It concerns no Podman, container, or Juniper device behavior.
