# Research: Dash pytest plugin marker warning

This file holds the decisions, the remote verification table, the sources, and the unverified list. Line 0 means that the check covers the whole file or the whole listing.

## Decisions

### D-1 Treatment of PytestRemovedIn10Warning

- **Options**: (a) Ignore the warning with a filter. (b) Disable the plugin with `-p no:dash`. (c) Install Dash from upstream commit `1ed9150a`. (d) Fork or vendor the plugin. (e) Keep the plugin loaded and wait for a Dash release with the fix.
- **Chosen**: (e).
- **Reason**: (a) breaks the issue rule "Do not suppress the warning" and the constitution suppression rule (RC-18, RC-20). (b) changed a test result for the owner (RC-57). It also failed the pytest gate in issue #4832 (RC-60). (c) installs unreleased code. Upstream `dev` is 154 commits ahead and 232 behind `v4.5.1` (RC-55). (d) takes ownership of a third-party plugin.
- **Risk**: The warning stays visible until a release. Mitigation: exact pytest pins (RC-08, RC-11) and the watch task T008.

### D-2 Upgrade trigger

- **Options**: (a) Any Dash release after 4.5.1. (b) A release that contains commit `1ed9150a` or a later commit, with `pytest.hookimpl` at plugin line 104. (c) A release that removes the `pytest11` entry point.
- **Chosen**: (b).
- **Reason**: (a) can ship without the fix. (c) does not match upstream. Upstream `dev` keeps the entry point at `setup.py` line 54 (RC-51). The issue comment says "migrates its pytest11 entry point". This record reads that phrase as the marker change, because upstream changed only the marker (RC-48, RC-49).
- **Risk**: The owner may mean something else by the phrase. Mitigation: the reading is recorded in `spec.md` Clarifications. Task T008 posts each check result on issue #4826, so the owner can confirm the reading.

### D-3 Placement and form of the policy check

- **Options**: (a) New file under `tests/guardrails/`. (b) New package under `tests/contract/`. (c) A child-process test that counts removal warnings. (d) A narrow edit of `tests/contract/test_pytest_coverage_gate.py`. (e) No regression test.
- **Chosen**: (d).
- **Reason**: (a) adds a direct child to a folder with 79 children (RC-38). (b) adds a direct child to a folder with 17 children (RC-37). (c) reports zero warnings when `-p no:dash` disables the plugin. That result passes for the wrong reason. (e) leaves the approach of PR #4831 open to a second attempt. The module already tests pytest gate behavior (RC-36).
- **Risk**: The module name does not describe the policy check. Mitigation: task T011 moves the check when the folder rule allows it.

### D-4 Issue keyword in the interim pull request

- **Options**: (a) `Closes #4826`. (b) `Refs #4826`.
- **Chosen**: (b).
- **Reason**: The owner keeps the issue open until upstream migrates (RC-57). AGENTS requires `Closes` for a change that resolves the issue (RC-22). The interim change does not resolve the issue. The upgrade change uses `Closes #4826` in task T009.
- **Risk**: A reviewer expects the AGENTS default. Mitigation: the pull request body states the reason.

### D-5 Location of the known-warning section

- **Options**: (a) `documentation/development-setup.md`. (b) The CI gate reference. (c) `documentation/architecture.md`. (d) `README.md`.
- **Chosen**: (a).
- **Reason**: Engineers read the setup guide for local runs. The guide already explains the conftest environment check (RC-31). The architecture guide names no pytest term (RC-33). The CI gate reference describes CI jobs, not local runs. The README has no user-facing change.
- **Risk**: Low. The section needs an update when the upgrade change lands (task T009).

### D-6 Branch and PR history

- **Options**: (a) Reuse `fix/4826-dash-pytest-hooks`. (b) Delete the fix branch now. (c) Keep the fix branch and create `chore/4826-dash-pytest-hook-warning`.
- **Chosen**: (c).
- **Reason**: (a) carries the rejected `-p no:dash` change (RC-58, RC-59). (b) removes the branch name before a replacement exists. AGENTS requires keeping the work until a replacement keeps it (RC-23).
- **Risk**: Branch clutter. Mitigation: task T010 decides after the merge.

### D-7 Form of the warning gate

- **Options**: (a) Search the output for the warning text. (b) Run pytest with `-W error::pytest.PytestRemovedIn10Warning`. (c) Count warnings in a child process.
- **Chosen**: (b).
- **Reason**: (a) can pass while the warning appears in a different format. (b) turns the warning into a failing run, so the warning cannot stay hidden. The category name `PytestRemovedIn10Warning` matches the warning exactly (RC-46). The option `-W error::DeprecationWarning` would also catch it, but it would catch other warnings too.
- **Risk**: Another plugin with the same category fails the gate. Mitigation: the engineer reads the module named in the failure.

### D-8 Manifest changes

- **Options**: (a) Pin a pre-release or a development build now. (b) Keep the current pins until a release contains the fix. (c) Change the pytest pin.
- **Chosen**: (b).
- **Reason**: (a) installs unreleased code (D-1). (c) gives no benefit. The exact pin `pytest==9.2.0` already matches the installed version (RC-08, RC-11, RC-46). FR-005 forbids manifest changes in the interim change.
- **Risk**: The dependency lags upstream. Mitigation: tasks T008 and T009.

## Remote Verification

Each row records one check. The count of rows matches `remote_checks` in the status file and the count in `summary.md`.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Unit test file defines 16 test functions | tests/unit/refactors/test_app_context_session_state.py | main | 6f28712d03b99e60b4405fcef3d95d823efb13f0 | present | 37 |
| RC-02 | Integration file defines the journey test | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 60 |
| RC-03 | Journey test patches builtins.open with AssertionError | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 65 |
| RC-04 | Root pytest configuration table exists | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 510 |
| RC-05 | Root addopts omit no:dash | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 523 |
| RC-06 | Root pytest configuration holds no warning filter | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | absent | 510 |
| RC-07 | Root Dash range is 4.5.1 up to but excluding 5 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 70 |
| RC-08 | Root dev extra pins pytest 9.2.0 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 109 |
| RC-09 | requirements.txt pins dash 4.5.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 45 |
| RC-10 | requirements-dev.txt pins dash 4.5.1 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 76 |
| RC-11 | requirements-dev.txt pins pytest 9.2.0 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 325 |
| RC-12 | requirements-dev.txt holds no selenium, percy, or dash-testing pin | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | absent | 0 |
| RC-13 | MistHelper.py filter names only SyntaxWarning | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 41 |
| RC-14 | tests/conftest.py holds no Dash or warning filter | tests/conftest.py | main | f55885cafab8f4c346ee7d7a813835bab300e45d | absent | 0 |
| RC-15 | Copilot instructions give the bootstrap command and Windows activation path | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 29 |
| RC-16 | Copilot instructions gate table lists the Tests and STE gates | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-17 | Constitution forbids a direct child in a noncompliant parent | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 43 |
| RC-18 | Constitution forbids suppression of security findings | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 373 |
| RC-19 | Constitution requires a spec for three or more files | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 420 |
| RC-20 | AGENTS states that a suppression comment can ship a defect | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 154 |
| RC-21 | AGENTS defines Warning and Caution for safety statements | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 52 |
| RC-22 | AGENTS requires Closes in the pull request body | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| RC-23 | AGENTS requires preserving work before closing an unmerged pull request | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| RC-24 | Changelog rule 4 exempts internal-only changes | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-25 | Route resolver joins numbered segments under specs/numbered | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| RC-26 | Process folder guard validates the managed specs tree | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 133 |
| RC-27 | Spec route guard exists | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 0 |
| RC-28 | Route folder for issue 4826 is free on main | specs/numbered/0/0/1/2/3/3/0/1 | main | none (tree listing) | absent | 0 |
| RC-29 | Earlier record cites the Dash deprecation warning for issue 4826 | specs/numbered/0/0/1/2/3/0/1/3/4758-strict-pyright-repairs/analysis.md | main | ff4b1274a1da13f2da93a86d6fdce416af9807f0 | present | 340 |
| RC-30 | Reference record spec exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| RC-31 | Development setup names the conftest environment check | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 370 |
| RC-32 | Development setup holds no Dash or warning policy | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | absent | 0 |
| RC-33 | Architecture guide names no pytest or Dash term | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | absent | 0 |
| RC-34 | Operator guide names no pytest or Dash term | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| RC-35 | Container guide shows a pytest command for a test container | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 155 |
| RC-36 | Contract module reads the CI workflow for the coverage gate | tests/contract/test_pytest_coverage_gate.py | main | b005cf31893ac69a7c365c775f0d03a460ce616c | present | 18 |
| RC-37 | Contract folder holds 17 children | tests/contract | main | none (tree listing) | present | 0 |
| RC-38 | Guardrails folder holds 79 children | tests/guardrails | main | none (tree listing) | present | 0 |
| RC-39 | Guard file from closed PR 4831 is absent on main | tests/guardrails/test_pytest_startup_removal_warning.py | main | none (tree listing) | absent | 0 |
| RC-40 | Sibling project filters DeprecationWarning | mist-ops-platform/pyproject.toml | main | 64162dd141653bfe00c0962a3137569352ee8f8b | present | 126 |
| RC-41 | Legacy plan shows the pytest -p no:dash command | specs/431-arch-delegate-cleanup/plan.md | main | b59448d8f1be08fa70308aa23f63d6bd41815349 | present | 264 |
| RC-42 | Constitution names Windows 11 local development in a venv | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 363 |
| RC-43 | Installed Dash plugin uses the old-style marker on pytest_addhooks | .venv\Lib\site-packages\dash\testing\plugin.py | local .venv, Dash 4.5.1 | 1b917d7657b308a208a57ec72966131642b920a1 | present | 104 |
| RC-44 | Installed Dash registers the pytest11 entry point | .venv\Lib\site-packages\dash-4.5.1.dist-info\entry_points.txt | local .venv, Dash 4.5.1 | 669586b9f6d4ebc6adfd94e2cd85a3d8728b253e | present | 7 |
| RC-45 | Installed Dash has no testing extra packages | .venv\Lib\site-packages (distribution listing) | local .venv | none (listing) | absent | 0 |
| RC-46 | Installed pytest 9.2.0 defines PytestRemovedIn10Warning | .venv\Lib\site-packages\_pytest\warning_types.py | local .venv, pytest 9.2.0 | c5b339dec4c280011014cea998d40f17df5b23f7 | present | 53 |
| RC-47 | Installed pytest 9.2.0 emits the old-style message | .venv\Lib\site-packages\_pytest\deprecated.py | local .venv, pytest 9.2.0 | 98b7e112bf616ebf280ce4a244d5afc63f972ffb | present | 58 |
| RC-48 | Dash v4.5.1 plugin keeps the old-style marker at line 104 | https://api.github.com/repos/plotly/dash/contents/dash/testing/plugin.py?ref=v4.5.1 | v4.5.1 | 1b917d7657b308a208a57ec72966131642b920a1 | present | 104 |
| RC-49 | Dash dev plugin uses pytest.hookimpl at line 104 | https://api.github.com/repos/plotly/dash/contents/dash/testing/plugin.py?ref=dev | dev | 5146fc31a658a806c9c36bf077280bc3f1cdea9f | present | 104 |
| RC-50 | Dash v4.5.1 registers the pytest11 entry point | https://api.github.com/repos/plotly/dash/contents/setup.py?ref=v4.5.1 | v4.5.1 | 2716cc0eb7a3f6b07aabd46e5c389d3785c59727 | present | 54 |
| RC-51 | Dash dev registers the pytest11 entry point | https://api.github.com/repos/plotly/dash/contents/setup.py?ref=dev | dev | 612f7b7737c053c3d8436e14f8c978c76691796c | present | 54 |
| RC-52 | Upstream fix commit 1ed9150a exists on dev | https://api.github.com/repos/plotly/dash/commits/1ed9150a667f631aa7115ae4eab2b25d1a59bcae | 1ed9150a667f631aa7115ae4eab2b25d1a59bcae | none | present | 0 |
| RC-53 | Latest Dash release is v4.5.1 | https://api.github.com/repos/plotly/dash/releases/latest | v4.5.1 | none | present | 0 |
| RC-54 | PyPI project page shows dash 4.5.1 | https://pypi.org/project/dash/ | PyPI | none | present | 0 |
| RC-55 | Dash dev diverges from v4.5.1 | https://api.github.com/repos/plotly/dash/compare/v4.5.1...dev | v4.5.1...dev | none | present | 0 |
| RC-56 | Issue 4826 is open with labels chore and tests | https://github.com/jmorrison-juniper/MistHelper/issues/4826 | main | none | present | 0 |
| RC-57 | Owner comment reports the test failure with -p no:dash | https://github.com/jmorrison-juniper/MistHelper/issues/4826#issuecomment-7001491032 | comment IC_kwDOQltU8c8AAAABoVJGWA | none | present | 0 |
| RC-58 | Pull request 4831 is closed and unmerged | https://github.com/jmorrison-juniper/MistHelper/pull/4831 | fix/4826-dash-pytest-hooks | none | present | 0 |
| RC-59 | Fix branch exists at commit 725510a3 | repos/jmorrison-juniper/MistHelper/branches/fix/4826-dash-pytest-hooks | 725510a3237623e6c5a0653aea14263f4e51a94e | none | present | 0 |
| RC-60 | Issue 4832 records the failed pytest gate for PR 4831 | https://github.com/jmorrison-juniper/MistHelper/issues/4832 | closed issue | none | present | 0 |
| RC-61 | Base commit b7a18b7e exists | repos/jmorrison-juniper/MistHelper/commits/b7a18b7ead7b1de5882bcd288203c015b1eef792 | b7a18b7ead7b1de5882bcd288203c015b1eef792 | none | present | 0 |
| RC-62 | Main head is f03c6c9b | repos/jmorrison-juniper/MistHelper/commits/main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | none | present | 0 |
| RC-63 | Open pull request 4888 touches requirements-dev.txt | repos/jmorrison-juniper/MistHelper/pulls (open list) | dependabot/pip/mando-0.8.2 | none | present | 0 |
| RC-64 | Installed Dash plugin registers fixtures without the testing extra | .venv\Lib\site-packages\dash\testing\plugin.py | local .venv, Dash 4.5.1 | 1b917d7657b308a208a57ec72966131642b920a1 | present | 142 |

Result counts: 64 rows. Present: 55. Absent: 9. Partial: 0. Stale: 0.

Local rows use the path under the checkout. The Git blob SHA for each local file came from `git hash-object` with no write option.

## Sources

### Local paths

- `AGENTS.md` (repository root), read in full.
- `.github/copilot-instructions.md`, read in full. The local gates table starts at line 50.
- `.specify/memory/constitution.md`, read in full.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`, read in full.
- `documentation/development-setup.md`, `documentation/architecture.md`, `documentation/operator-guide.md`, and `documentation/container-deployment.md`. Each was searched for pytest and Dash terms. `documentation/quality-gates.md` was searched for the same terms, and its matches describe CI jobs.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (reference record). Its headings were used for shape. Its content was not copied.
- `.venv\Lib\site-packages\dash\testing\plugin.py`, lines 1 to 211, read in full.
- `.venv\Lib\site-packages\dash-4.5.1.dist-info\entry_points.txt` and `METADATA`.
- `.venv\Lib\site-packages\_pytest\warning_types.py` lines 40 to 60, and `_pytest\deprecated.py` lines 44 to 64.
- `.venv\Lib\site-packages\pytest-9.2.0.dist-info\METADATA`.

### Remote paths and GitHub reads

- The `main` tree of `jmorrison-juniper/MistHelper`, fetched once with the recursive tree endpoint. The tree held 11404 entries and was not truncated.
- Contents of the files named in the table, read through the contents endpoint at `ref=main`.
- Issues #4826, #4832, #4758, #4731, #4825, #4828, and #4911. Pull request #4831 changed `pyproject.toml` (+5, -1) and added `tests/guardrails/test_pytest_startup_removal_warning.py` (+44). Its branch head and state appear in RC-58 and RC-59. The open pull request list.

### Upstream sources

- `https://api.github.com/repos/plotly/dash/contents/dash/testing/plugin.py?ref=v4.5.1` (RC-48).
- `https://api.github.com/repos/plotly/dash/contents/dash/testing/plugin.py?ref=dev` (RC-49).
- `https://api.github.com/repos/plotly/dash/contents/setup.py?ref=v4.5.1` and `ref=dev` (RC-50, RC-51).
- `https://api.github.com/repos/plotly/dash/commits?sha=dev&path=dash/testing/plugin.py` (commit history for RC-52).
- `https://api.github.com/repos/plotly/dash/releases/latest` and `releases` (RC-53).
- `https://api.github.com/repos/plotly/dash/compare/v4.5.1...dev` (RC-55).
- `https://pypi.org/project/dash/` read with the web fetch tool (RC-54).

### Fetch failure

The web fetch tool blocked `https://raw.githubusercontent.com/plotly/dash/dev/dash/testing/plugin.py`. The block came from a private-address rule. The GitHub contents endpoint returned the same blob SHA as the local file (RC-43 and RC-48).

## Skills

No skill was loaded. The topic covers pytest plugin loading and Dash packaging. No listed skill covers that topic. The issue has no Podman or Juniper device question.

## Mist API and mistapi

Not applicable. The issue names no Mist API endpoint and no mistapi function. The record makes no OpenAPI or mistapi claim.

## Unverified

1. The owner observation that `-p no:dash` changes `test_complete_offline_journey` (RC-57). Reason: this record runs no tests. The reproduction command in the issue is also not run.
2. The issue claim "Current tests pass." Reason: this record runs no tests.
3. The PR #4831 body claims `8 passed` for the unit file plus the guard. It also claims pytest exited with code 3 before the fix. Reason: main's unit file defines 16 test functions (RC-01). The count does not match. No run was made.
4. The inference that the marker warning fires even when `_installed` is False (plugin line 53). Reason: the decorator at line 104 runs at module load, but no run confirms it. Evidence: RC-43, RC-44, RC-45.
5. The behavior of `dash[testing]` on Dash 4.5.1. Reason: the extra is absent here, and no run used it.
6. Whether a later Dash release changes the entry point again. Reason: no release after 4.5.1 exists on 2026-11-26 (RC-53, RC-54). Task T008 checks each release.
7. The status of pull request #4888 after this record. Reason: the pull request was open at the time of the check (RC-63).
