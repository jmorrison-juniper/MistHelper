# Research: Hardware CLI failure reporting

## 1. Method

- The issue, the related issues, and the pull request search results came from `gh` read-only calls.
- The remote `main` tree was read once. Remote file bodies were read only for the cited lines.
- The publication worktree and the local git object store were read with read-only commands. No checkout, fetch, pull, add, commit, branch, worktree, or push ran.
- No build, test, lint, install, or container command ran. No GitHub write ran.
- Affected path: the entry point is `HardwareCollectionCli.run` (`cli.py` lines 60 to 74). The numbered menu entry is blocked (branch `tasks.md` lines 238 and 258), so no menu path exists yet. The write point is `services.sessions.batches.start` (`cli.py` line 101), which the CLI calls once.

## 2. Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. No decision needs a human answer, so the human count is 0.

| ID | Decision | Alternatives | Reason | Risk |
| - | - | - | - | - |
| D-1 | Publish the repair on the #4773 publication branch. The pull request body contains `Closes #4779` and `Refs #4773`. | (a) A new branch `fix/4779-hardware-cli-failure-reporting` from `main`. (b) Wait for #4773 to merge, then fix on `main`. | The CLI exists only on the #4773 branch (R-03). A branch from `main` contains no CLI. Waiting adds a second pull request for the same defect. The issue says the repair belongs before publication. | The pull request grows to about 35 files. `Refs #4773` keeps #4773 open for its blocked tasks. |
| D-2 | Rename the publication branch from `3999-transceiver-master-report` to `feat/4773-transceiver-master-report` before the push. | (a) Keep the current name. (b) Rename to `fix/4779-hardware-cli-failure-reporting`. | The number 3999 does not match issue 4773. `development-setup.md` lines 178 to 181 require a branch name that holds the type, the issue number, and a slug. The owner of issue 4773 owns the branch. | The local branch name changes. The worktree path stays the same. |
| D-3 | Keep the committed narrow boundary. Verify it with a test run. Add FR-003 and FR-005 to FR-008. | (a) Rewrite the boundary. (b) Close the issue on static reading alone. | Static reading predicts a pass for the regression cases. Two gaps remain: programming errors hide under `RuntimeError`, and an uncertain admission prints `Admitted: False`. | New messages change operator output before publication. The new tests cover each text. |
| D-4 | Re-raise `NotImplementedError` and `RecursionError` before the operational clauses. | (a) Keep the `RuntimeError` clause unchanged. (b) Remove `RuntimeError` from the clauses. | Both classes subclass `RuntimeError`, and both signal defects. Removing `RuntimeError` breaks the regression case `[RuntimeError]`. | A library that raises `NotImplementedError` for a supported feature shows a traceback. The traceback shows the defect. |
| D-5 | Store the admission state as a string attribute with three values. Annotate it with `Literal`. | (a) A boolean `admitted` flag. (b) A new enum class. | A boolean cannot represent an uncertain admission. A new class adds a top-level name to `cli.py`, which already holds five. The string style matches `HardwareCliResult.status` (L-01 to L-04). | A typo in a value still type-checks at runtime. The tests and the `Literal` annotation reduce this risk. |
| D-6 | Print the exact caution texts from the contract. Log `Admission state` with the state and the stable cause. | (a) Print the raw exception text. (b) Print the class name only (current behavior). | Raw text can hold service values. The #4773 contract forbids private values in shared output (`requests.md`, section "Completion and cancellation", L-14). The caution names the portal check as the next step. | An operator can read the caution as a failure. The text says "may", so the wording stays accurate. |
| D-7 | Classify a malformed start reply as uncertain admission with code `admission_unverified`. | (a) Keep the current behavior, where `AttributeError` or `TypeError` escapes. (b) Classify the reply as an operational failure without a state change. | The reply is external data. A missing session identifier can hide an admitted collection. The state must stay `uncertain`. | A real defect in the validation code appears as `admission_unverified`. The change limits this effect to the reply check. |
| D-8 | After an operational failure that follows admission, print the admitted caution. Do not stop the parent. Track the stop behavior in F-1. | (a) Stop the parent in this issue. (b) Ignore the admitted state. | Stopping changes the outcome for a transient poll error. One issue holds one concern (`AGENTS.md`, "Issue first"). The caution gives the operator the needed information now. | The admitted collection can keep running. The caution tells the operator to check the portal. |
| D-9 | Leave the report publication broad catches unchanged (L-11). Track them in F-2. | (a) Narrow the catches now. (b) Re-raise programming errors after native preservation. | The catches protect native files. The portal uses the same report path, so a change alters portal results. The issue names only the CLI boundary. | The CLI result can show a derived-output failure for a programming error until F-2 closes. |
| D-10 | Add the new cases to `test_cli.py`. Parametrize existing functions where possible. Add one new function for three cases. | (a) A new test module. (b) Three new functions. | A new module adds a child to a directory that already holds six. Three functions add three top-level names. One function limits the increase to one name. | `test_cli.py` stays above the five-name limit. Follow-up F-4 splits it. |
| D-11 | Update the operator guide section and the existing changelog fragment. Keep the fragment name. Add no new fragment. | (a) A new fragment named `issue-4779-hardware-cli-failure-reporting.md`. (b) Rename the fragment to the pull request name form. | The CLI is unpublished, so its behavior belongs to the feature fragment. `changelog.d/README.md` lines 32 and 33 say to keep the first name after the pull request opens. | The fragment layout changes. T011 applies the README layout rule. |
| D-12 | Resolve the format conflict as a union. Keep `csv`, `master-xml`, and `csv-master-xml` from `main`. Keep `xml`, `json`, and `both` from the branch. | (a) Keep the branch set only. (b) Keep the `main` set only. | `main` uses the three extra formats for menu 309 (R-06, line 309). Dropping them breaks that menu. Dropping the branch formats breaks the portal. | The union needs a test. T002 runs `test_ws_hardware_master_xml.py`. |
| D-13 | Run each gate that applies. Record each skipped gate with its reason. Run both `pytest-chunks` shards before the push. | (a) Run `test_cli.py` only. (b) Run every gate, including gates that do not apply. | The changed files touch shared web modules. The copilot-instructions table requires the gates that apply. The #4773 record ran a subset. | The two shards took about 26 minutes at the measured speed of 2026-09-17. |

## 3. Remote Verification Table

Ref `main` means the GitHub repository `jmorrison-juniper/MistHelper` at its default branch. Rows marked `commit lookup` use the commit endpoint. Result values are `present` or `absent`.

| Row | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Issue test module exists on main | tests/unit/websocket_streams/web/hardware/test_cli.py | main | none | absent | 0 |
| R-02 | Test package directory exists on main | tests/unit/websocket_streams/web/hardware | main | none | absent | 0 |
| R-03 | Hardware CLI module exists on main | src/mist/realtime/websocket_streams/web/services/operations/hardware/cli.py | main | none | absent | 0 |
| R-04 | Hardware package directory exists on main | src/mist/realtime/websocket_streams/web/services/operations/hardware | main | none | absent | 0 |
| R-05 | Hardware report module exists on main | src/mist/realtime/websocket_streams/web/services/operations/hardware/report.py | main | none | absent | 0 |
| R-06 | Main hardware XML preset lists csv and master-xml formats | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | main | bb018c99e0fc0ffe982a7f532064f1755a87865a | present | 309 |
| R-07 | Assembly factory defines ExplicitSessionServices | src/mist/realtime/websocket_streams/web/services/assembly/factory.py | main | 2e35ee8b777a6ac419f606e9de7cb0099adcb28a | absent | 0 |
| R-08 | Shared safe input accepts raise_on_cancel | src/foundation/support/utils/input_utils.py | main | 960c6ba244134982ec892df3a45232a157a2a853 | absent | 61 |
| R-09 | StreamRequestError class defines a code attribute | src/mist/realtime/websocket_streams/intake/fields/error.py | main | a509d72dee9a9249dc5e992498a2b93f76f7cfd4 | present | 9 |
| R-10 | EX hardware batch catches StreamRequestError and re-raises | src/operations/exporting/ex_hardware_inventory/run/batch.py | main | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 201 |
| R-11 | Spec route computes base-5 segments | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-12 | Spec route rejects a parent with five children | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 93 |
| R-13 | Route parent 0/0/1/2/3/1/0 exists with one child | specs/numbered/0/0/1/2/3/1/0 | main | c47c7c101ce36bcdaef3b8f09bc03547be168df8 | present | 0 |
| R-14 | Route parent 0/0/1/2/3/1 exists with three children | specs/numbered/0/0/1/2/3/1 | main | 42d51be54c337e7b0c6c5abba0ed6513cbd390d6 | present | 0 |
| R-15 | Route leaf 0/0/1/2/3/1/0/4 is free for issue 4779 | specs/numbered/0/0/1/2/3/1/0/4 | main | none | absent | 0 |
| R-16 | Reference record 4920 holds spec.md | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R-17 | No 4773 record exists on main | specs/numbered/0/0/1/2/3/0/4/3/4773-transceiver-master-report/spec.md | main | none | absent | 0 |
| R-18 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R-19 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R-20 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R-21 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R-22 | Process folder baseline guard file exists | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| R-23 | Operator guide on main has no CLI section | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| R-24 | Issue 4773 changelog fragment is absent on main | changelog.d/issue-4773-transceiver-master-report.md | main | none | absent | 0 |
| R-25 | Changelog README states the fragment rules | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 37 |
| R-26 | CI workflow defines the gate path variables | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-27 | Development setup states the branch name rule | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 181 |
| R-28 | Agent rules file exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| R-29 | Repository instructions file exists | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 0 |
| R-30 | Constitution exists | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| R-31 | Worktree bootstrap script exists | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 0 |
| R-32 | STE linter configuration exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| R-33 | Project tool configuration exists | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 0 |
| R-34 | Test quality configuration exists | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| R-35 | Test quality baseline exists | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 0 |
| R-36 | Quality gates document exists | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 0 |
| R-37 | Sessions module exists on main, and the branch changes it | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | main | edcb8413a4bfb0dbc9a3d1471dce4558e9100a68 | present | 0 |
| R-38 | Branch base commit exists on GitHub | commits/ac046837b2bef943f0edbcd3298456265d7014fe | main | none (commit lookup) | present | 0 |
| R-39 | Local commit 8140bb37c exists on GitHub | commits/8140bb37c | main | none (commit lookup) | absent | 0 |
| R-40 | Local commit 58ab484 exists on GitHub | commits/58ab484 | main | none (commit lookup) | absent | 0 |
| R-41 | Local commit 07cf3ee exists on GitHub | commits/07cf3ee | main | none (commit lookup) | absent | 0 |
| R-42 | Local commit edc12d5 exists on GitHub | commits/edc12d5 | main | none (commit lookup) | absent | 0 |
| R-43 | Remote main points to the local HEAD | git/ref/heads/main | main | none (commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca) | present | 0 |

Row count: 43. The STATUS file lists the same 43 checks.

## 4. Local Evidence (Branch Only)

Local evidence shows what the unpushed branch contains. It does not prove that GitHub holds the code. Remote rows R-01 to R-05 and R-39 to R-42 cover that proof.

- **L-01** `cli.py` lines 60 to 74: the `run` boundary. Clauses at lines 68 and 70. Cleanup at line 74.
- **L-02** `cli.py` lines 76 to 86: `_failure` at lines 76 to 81, with the error log at line 79 and the operator write at line 80. `_incomplete` at lines 83 to 86.
- **L-03** `cli.py` lines 89 to 103: `_collect`. The preview call is at line 92, and the start call is at line 101. Line 102 assigns `session_id`. No log call exists in lines 89 to 103.
- **L-04** `cli.py` lines 109 to 119: `HardwareCliWorkflow.__init__`. Line 117 sets `session_id`.
- **L-05** `cli.py` lines 212 to 233: `Completion.wait`. The summary call is at lines 220 to 223. The stop call is at line 232.
- **L-06** `cli.py` lines 235 to 249: `Completion.cancel`. The except clause is at lines 243 to 248.
- **L-07** `cli.py` line 111: the constructor imports `ExplicitSessionServices`. Line 114 calls `ExplicitSessionServices.build`.
- **L-08** `test_cli.py`: class `CliScenario` at line 28. Test functions with their parametrize decorators at lines 92 to 95, 110 to 121, 129 to 142, 144 to 158, 161 to 168, and 170 to 173. Six test functions and one class make seven top-level names.
- **L-09** `input_utils.py` line 66: the parameter `raise_on_cancel: bool = False`. The branch adds it. `main` lacks it (R-08).
- **L-10** `preset.py` line 272 defines class `HardwareXmlPreset`. Line 281 sets `FORMATS` to `xml`, `json`, and `both`.
- **L-11** `report.py` lines 332 and 479 hold broad `except Exception` clauses.
- **L-12** The #4773 record `tasks.md`: line 226 (T042), line 233 (T046), line 319 (64 CLI cases), and lines 418 to 423 (the #4779 repair claim and 66 CLI cases).
- **L-13** The #4773 record `spec.md` line 94 (FR-019): preserve cancellation and disclose incomplete collection.
- **L-14** The #4773 record `design/contracts/requests.md` line 172: do not start a replacement run after an uncertain admission response.
- **L-15** The #4773 record `documentation/operator-guide.md` line 423: heading `#### Reusable CLI class`.
- **L-16** The fragment `changelog.d/issue-4773-transceiver-master-report.md` has headings `### Added` and `### Fixed`.
- **L-17** Commit `8140bb37c` changes 35 files. The `operations/hardware/` package gains six files: `__init__.py`, `cli.py`, `models.py`, `normalization.py`, `preset.py`, and `report.py`. The `tests/unit/websocket_streams/web/hardware/` directory gains six files: `__init__.py`, `test_cli.py`, `test_contracts.py`, `test_native.py`, `test_normalization.py`, and `test_report.py`.
- **L-18** The worktree metadata at `.git\worktrees\MistHelper-feat-4773\HEAD` names `refs/heads/3999-transceiver-master-report`. Its `gitdir` names `MistHelper-feat-4773`.
- **L-19** `git diff --name-status` shows that `main` modified `hardware_xml.py` after base `ac046837b`. The branch renamed it to `hardware/preset.py` with a 72 percent similarity score.
- **L-20** Committer dates: `8140bb37c` at 2026-11-11 17:51:08 -0600 (23:51:08 UTC). `58ab484` at 17:54:23 -0600. `07cf3ee` at 17:56:09 -0600. `edc12d5` at 18:00:18 -0600 on 2026-11-11.

## 5. Sources

- GitHub issue 4779 (read-only `gh issue view`): created 2026-11-11T23:05:37Z, open, labels `bug` and `web-portal`, no comments.
- GitHub issue 4773 (read-only `gh issue view`): open, labels `feature`, `web-portal`, and `in-progress`. Owner comment `IC_kwDOQltU8c8AAAABleuvrQ`, created 2026-11-12T00:00:42Z.
- GitHub pull request search for `4779`: no result. Search for `4773`: pull request #4619 (merged 2026-11-13T08:54:28Z), #4607 (merged 2026-11-13T07:14:03Z), and #4208 (open). These are search hits, not confirmed links.
- GitHub issue 4783 (read-only): open, "Test quality: native report tests miss failure-boundary checks". The body lists five new findings.
- GitHub issue 4920 (read-only): closed, "[Spec]: Collect EX switch hardware inventory into one CSV for one organization or an MSP".
- Remote files read with the contents endpoint at ref `main`: `.github/workflows/ci.yml` (lines 93, 101, 104, 107), `.specify/scripts/powershell/spec-route.ps1` (lines 4, 17, 93), `src/operations/exporting/ex_hardware_inventory/run/batch.py` (lines 201 and 204), `src/mist/realtime/websocket_streams/intake/fields/error.py` (lines 9 and 44), `src/foundation/support/utils/input_utils.py` (lines 61 to 66), `src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py` (lines 300 and 309), `changelog.d/README.md` (lines 37 to 39), and `factory.py` (no class named `ExplicitSessionServices`).
- Local files at the repository HEAD: `documentation/development-setup.md` lines 176 to 186. Its local blob matches R-27.
- Local `AGENTS.md`, `.github/copilot-instructions.md`, and `.specify/memory/constitution.md` supply the rules. The record cites their sections by name.
- No URL was fetched. The `web_fetch` tool was not used.

## 6. Unverified

- **U-1** The pass or fail result of the three regression cases on the branch. The brief forbids test runs in this step.
- **U-2** The owner-reported counts: 358 passed tests, 64 and 66 CLI cases, and 93.98 percent hardware coverage. These values come from owner text only.
- **U-3** The test-quality finding count. Sources disagree: two findings in the #4773 comment and five in issue 4783.
- **U-4** The status of the #4607 menu blocker. The pull request merged on 2026-11-13, and the owner has not updated the comment.
- **U-5** The rebase result for the ten overlap files and for the hardware preset. No rebase ran.
- **U-6** The source of the output quoted in issue 4779. The issue predates the committed narrow boundary, and no snapshot of that state exists.
- **U-7** The full content of the #4773 spec, plan, tasks, and contract files. Only the cited lines were read.

## 7. Skills and Sources Not Used

- Skills: none loaded. The issue asks about exception handling. It has no Podman or Juniper device question.
- Mist OpenAPI file: not used. The repair makes no endpoint claim.
- mistapi source: not used. The record makes no SDK claim.
- Container documentation: not used. No container runs in this issue.
