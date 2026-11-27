# Research: SpecKit Task Audit Link and Legend Classification

**Date**: 2026-11-26

**Method**: Each remote claim uses a read-only `gh` call (GET). Each row in the remote table below comes from a `gh api` contents, tree, or commit call. Upstream rows use the `misthelper-devtools` repository. No row relies on the local checkout.

## R1. Failure reproduction from the CI logs

The check is the job `speckit_task_audit`, named `SpecKit task audit (advisory)`, in the workflow `Quality Gates` (`.github/workflows/ci.yml`). The job runs one install step and one audit step. The audit step ends with `|| true` (RC-01).

**Mode A (the defect in issue #4703).** The audit counts links and legends as malformed markers.

- Run 42589635262 (push to `main`, commit `3964d21`, created 2026-11-09T08:56:53Z), job 129067813179.
- The step `Report unchecked SpecKit tasks` printed: `Examined 884 feature record(s), 405 task file(s), and 10942 task marker(s): 7512 checked, 3394 unchecked, 36 malformed.`
- The job concluded `success`, because the step ends with `|| true`.
- The command `gh run view 42589635262 --log-failed` printed no line for this job, because the job passed. The job log came from `gh run view --job 129067813179 --log`, which is a GET request.
- The failing rule is the malformed-marker rule. At commit `e8e093d`, the rule matches any bullet that starts with a bracketed label (RC-20).

**Mode B (a second failure of the same check, out of scope).** The install step fails before the audit runs.

- Run 45064243269 (branch `dependabot/pip/mando-0.8.2`, commit `e86098cd`, created 2026-11-22T20:03:36Z), job 137336719307, concluded `failure`.
- The failing step is `Run python -m pip install -r requirements-dev.txt`. It prints `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.`
- The log names the conflict. `radon 6.0.1` depends on `mando<0.8` and `>=0.6`. The branch requests `mando==0.8.2` at line 179 (RC-16) and `radon==6.0.1` at line 365 (RC-17).
- The command `gh run view 45064243269 -R jmorrison-juniper/MistHelper --log-failed` shows the same conflict in other jobs of that run.
- The failing rule is pip dependency resolution. The malformed-marker rule did not run.

**Current state (Mode A resolved on `main`).**

- Run 45774119357 (`workflow_dispatch` on `main`, head `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, created 2026-11-26T07:16:40Z), job 139753527621.
- The step printed: `Examined 922 feature record(s), 442 task file(s), and 11681 task marker(s): 8177 checked, 3504 unchecked, 0 malformed.`
- The job concluded `success`. The step still lists unchecked tasks and missing task files. Those findings are out of scope.

## R2. Pin history of misthelper-devtools in MistHelper

The table lists each commit that changed or kept the pin. Each commit exists on GitHub (`gh api repos/jmorrison-juniper/MistHelper/commits/<sha>`).

| Commit | Date (UTC) | Pin in `requirements-dev.txt` | Meaning |
|--------|-----------|-----------------------------------------|---------|
| `52fe6883` (PR #4790) | 2026-11-13T03:59:18Z | `e8e093d` | Issue-time pin is still active. |
| `816f42ba` | 2026-11-13T14:34:23Z | `79a5e459` (v0.6.4, dated 2026-11-05) | The pin moves to v0.6.4. That release lacks the repair. |
| `26ac2613` (PR #4836) | 2026-11-19T18:11:17Z | `2239e7bd` | The pin moves to upstream `main` at 2026-11-19T17:46:41Z. The repair is included (RC-13). |
| `05cafda7` (PR #4806) | 2026-11-21T18:54:40Z | `2239e7bd` | The pin is kept. |
| `23379f0e` (PR #4871) | 2026-11-21T21:39:15Z | `2239e7bd` | The pin is kept. |
| `f03c6c9b` (`main` head of run 45774119357) | 2026-11-26 | `2239e7bd` | The pin is kept. The blob equals `main` (RC-14). |

The issue-time pin appears at `3964d21` (RC-12). Pull request #4836 uses branch `fix/4765-devtools-pin-bump` and closes the pin work of issue #4765 (closed).

## R3. Upstream repair in misthelper-devtools

- Issue #88 (bug, "exclude Markdown links and legends from task audit") is closed.
- Pull request #89 (title "fix(speckit-task-audit): ignore links and legends, report malformed lines") is merged as commit `da96d6e57a9bba7c7824f703c7cd722732010655`, at 2026-11-16T04:48:51Z.
- Commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (2026-11-19T17:46:41Z, title "fix(test-quality): scan full gate scope when changed tests are excluded (#95)") is upstream `main`. The comparison of `da96d6e` and `2239e7bd` reports status `ahead`, `ahead_by` 2, and `behind_by` 0. The repair is therefore in the history of the pin.
- The file `src/misthelper_devtools/speckit_task_audit.py` has the same blob at `da96d6e` and at `2239e7bd` (RC-26, RC-23). No later commit changed that file.
- Upstream CI run 44580808631 on `2239e7bd` concluded `success` (run-level read only, U3).

**Old logic at `e8e093d`.** The rule at line 297 matches any bullet that starts with `- [` and a closing bracket. That rule catches the `P` legend bullet and the `Issue #3300` link line (RC-18, RC-19). `TaskCounts` at line 112 has no `malformed_lines` field (RC-21). The method `_count_line` at line 291 holds the rule (RC-22).

**New logic at `2239e7bd`.** The file defines the link and legend exclusions in `_is_malformed` at line 318 (RC-23). `TaskCounts` records the line numbers at line 122 (RC-24). The report prints each malformed marker with its path and line at line 428 (RC-25). The method `_count_line` is absent. Its replacement is `_count_lines` at line 285 (RC-27). The exit code is 1 only for a complete record with open tasks or bad citations, at line 355 (RC-28).

**Upstream tests at `2239e7bd`.** The file `tests/unit/tools/test_speckit_task_audit.py` defines 32 test functions. The link and legend test is at line 66 (RC-29). The file and line report test is at line 89 (RC-30). The missing citation test is at line 155 (RC-31). The unchecked task in a complete spec test is at line 25 (RC-32).

## R4. Consumer state in MistHelper

- The job definition on `main` is at `ci.yml` lines 734 to 750. The job sets `continue-on-error: true` at line 738 (RC-02). The step is at line 750 (RC-01).
- The issue-time job definition is at `3964d21`, line 723 (RC-03).
- The sample lines exist on `main`. Line 363 holds the legend bullet (RC-18). Line 707 holds the link line (RC-19).
- Guard tests import the upstream scanner. `test_process_folder_structure.py` imports `TaskFileScanner` at line 11 (RC-33) and asserts the counts at line 228 (RC-34). `test_spec_route_contract.py` runs the command at line 207 (RC-36) and asserts the summary and completion lines at lines 224 and 237 (RC-37, RC-38).
- The quality gates document names the audit job at line 14 (RC-39). It has no row for the job in its table, so T005 adds one.
- The contributor guide lists the command at line 40 (RC-40).
- The changelog rules name the issue file form at line 27 of the README (RC-42). The policy test defines the issue pattern at line 39 and the change type words at line 45 (RC-43, RC-44).

## R5. Gate scope for the changed files

- The mypy path list excludes tests (RC-04). The pydocstyle path list excludes tests (RC-05). The interrogate path list excludes tests (RC-06).
- Bandit scans the whole repository (RC-08). Citation lint scans the tests directory (RC-09). The changelog policy test runs in CI (RC-07). Guard tests run inside the test shards (RC-10).
- The container build runs for product file changes only (RC-41). Steps 10 to 12 of the constitution do not apply to this change.

## R6. Sources not used for claims

- **Mist API and mistapi**: No claim in this record concerns a Mist endpoint or an SDK function. The OpenAPI files and the `.venv\Lib\site-packages\mistapi` package were not read.
- **Skills**: No skill was loaded. No claim concerns Podman, Juniper devices, or the containers.
- **Documents searched by term**: `documentation/architecture.md`, `documentation/development-setup.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md` contain no mention of the audit command or the audit job. No claim depends on them. They were not read in full.
- **Web**: `web_fetch` was not used. Every upstream fact came from the GitHub API, as listed under Sources.

## R7. Route, legacy record search, and record layout

- Legacy record search: No folder under `specs` starts with `4703-` in the local checkout. The remote tree holds no entry under the route folder either (RC-46). No legacy record exists, so no record needs verification before reuse.
- The issue number 4703 equals `122303` in base five. Padded to eight digits, it is `00122303`. That equals the route `0/0/1/2/2/3/0/3` (RC-45).
- The route folder is absent on `main` (RC-46).
- The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` has the same five root children and the same `design/` layout (RC-47).

## Decisions

### D-1. Keep the devtools pin at `2239e7bd`

- Alternatives: (a) pin `da96d6e`, the merge commit of PR #89. (b) keep `79a5e459`, the v0.6.4 release. (c) keep `2239e7bd`.
- Chosen: (c).
- Reason: Commit `2239e7bd` contains `da96d6e` (R3). It also contains the test-quality fix that issue #4765 needed. Option (a) drops that fix. Option (b) lacks the repair.
- Risk: The upstream `main` branch moves. The pin stays fixed until a reviewed update.
- Human decision required: no.

### D-2. Keep the audit job advisory

- Alternatives: (a) keep `continue-on-error: true` and the `|| true` step. (b) remove `|| true` and keep `continue-on-error`. (c) make the job blocking.
- Chosen: (a).
- Reason: Issue #4703 states that the job is advisory. Option (b) marks the job as failed for findings that the advisory design allows. Option (c) blocks merges on existing findings in the repository. The defect sits in the classifier, and this change fixes the classifier only.
- Risk: The masked exit code hides blocking findings in complete records. T005 documents the masking.
- Human decision required: no.

### D-3. Put the regression tests in the existing guard file

- Alternatives: (a) a new file in `tests/guardrails`. (b) a new file in `tests/unit`. (c) two functions in `tests/guardrails/test_process_folder_structure.py`.
- Chosen: (c).
- Reason: Constitution Principle I forbids a new direct child in a noncompliant parent. The folder `tests/guardrails` holds 79 entries on `main` (RC-48). Option (b) repeats upstream unit coverage. The existing file already imports `TaskFileScanner` (RC-33) and asserts counts (RC-34).
- Risk: The file grows by about 30 lines. The growth is acceptable.
- Human decision required: no.

### D-4. Name the changelog fragment for the issue

- Alternatives: (a) `pr-<number>.md`. (b) `<YYYY-MM-DD>-<slug>.md`. (c) `issue-4703-speckit-audit-markdown-links.md`.
- Chosen: (c).
- Reason: The pull request does not exist when the fragment is written. The README table names the issue form for that case (RC-42). The policy test accepts the issue form (RC-43).
- Risk: The README asks authors to keep the first name after the pull request opens. The implementer keeps this name.
- Human decision required: no.

### D-5. Keep the spec status at Draft

- Alternatives: (a) `Draft`. (b) `Implemented`. (c) `Complete`.
- Chosen: (a).
- Reason: The audit rule fails a complete record with open tasks or bad citations (RC-28). This record keeps open tasks until the merge, so the rule must not apply to it. The reference record also uses `Draft` (RC-47).
- Risk: The status stays `Draft` after the merge. The owner can change it in a later change.
- Human decision required: no.

### D-6. Gate closure on orchestrator authorization

- Alternatives: (a) treat pull request #4836 as authorized without evidence. (b) reopen the pin change for a new review. (c) gate closure on orchestrator authorization at T-MERGE.
- Chosen: (c).
- Reason: No comment on issue #4703 or issue #4765 authorizes the pin update (U1). A new review repeats work that the merged pin already covers. The gate adds no code.
- Risk: Closure waits for the orchestrator. The orchestrator confirms the authorization at T-MERGE.
- Human decision required: no.

### D-7. Track the `mando` conflict in a separate issue

- Alternatives: (a) fix the conflict in this change by moving the radon or mando pin. (b) close pull request #4888. (c) keep pull request #4888 open and ask for a separate issue.
- Chosen: (c).
- Reason: The conflict belongs to the dependency update in pull request #4888. Issue #4703 states that existing dependency ownership stays unchanged (comment of 2026-11-16). This agent cannot create GitHub issues, so the orchestrator files the issue.
- Risk: The audit job fails on the Dependabot branch until the separate issue resolves the conflict.
- Human decision required: no.

## Remote Verification Table

Each row is one remote check. The `remote_checks` array in the status file repeats these rows. The count is 48 in both places.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|----|-------|------|-----|----------|--------|------|
| RC-01 | Job step runs the audit with the exit code masked | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 750 |
| RC-02 | Job sets continue-on-error to true | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 738 |
| RC-03 | Issue-time commit runs the same masked step | .github/workflows/ci.yml | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | 1dd9fe495f894259354b28b30154e7a4a12da05b | present | 723 |
| RC-04 | MYPY_PATHS holds no test directory | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-05 | PYDOCSTYLE_PATHS holds no test directory | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-06 | INTERROGATE_PATHS holds no test directory | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-07 | Changelog policy test runs in CI | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 298 |
| RC-08 | Bandit scans the whole repository | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| RC-09 | Citation lint scans the tests directory | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 702 |
| RC-10 | Shard test paths include tests/guardrails | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| RC-11 | Main pins misthelper-devtools to commit 2239e7bd | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| RC-12 | Issue-time commit pins misthelper-devtools to commit e8e093d | requirements-dev.txt | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | b89886bab1f22365f9c2175a67b1fc2dc0fb748c | present | 197 |
| RC-13 | Commit 26ac2613 moves the pin to 2239e7bd | requirements-dev.txt | 26ac261392ac29119fa4f83e30c6ce9a0df12ab3 | ace270ae59effa5677494e3bdd90f3932c35e540 | present | 197 |
| RC-14 | Run head f03c6c9b pins 2239e7bd | requirements-dev.txt | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| RC-15 | Main pins mando 0.7.1 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| RC-16 | Dependabot branch pins mando 0.8.2 | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| RC-17 | Dependabot branch pins radon 6.0.1 | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 365 |
| RC-18 | Sample legend bullet on line 363 | specs/001-mist-ops-platform/tasks.md | main | 4b9e42a719112ecbf8e33ffe9ecc735093e6a2fb | present | 363 |
| RC-19 | Sample link line on line 707 | specs/3300-selective-insight-definitions/tasks.md | main | e676d0f69c9a162411d6786847cfa35ec1b42037 | present | 707 |
| RC-20 | Issue-time rule matches any bracketed bullet | misthelper-devtools:src/misthelper_devtools/speckit_task_audit.py | e8e093d205428b5503887267b6a9751fa7354be7 | 3340adac4de4a23ab82f26fab4163f783bfe0706 | present | 297 |
| RC-21 | Issue-time TaskCounts has no malformed_lines field | misthelper-devtools:src/misthelper_devtools/speckit_task_audit.py | e8e093d205428b5503887267b6a9751fa7354be7 | 3340adac4de4a23ab82f26fab4163f783bfe0706 | absent | 112 |
| RC-22 | Issue-time method _count_line exists | misthelper-devtools:src/misthelper_devtools/speckit_task_audit.py | e8e093d205428b5503887267b6a9751fa7354be7 | 3340adac4de4a23ab82f26fab4163f783bfe0706 | present | 291 |
| RC-23 | Pinned commit computes the exclusions in _is_malformed | misthelper-devtools:src/misthelper_devtools/speckit_task_audit.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a00b367af777c8be44fbe9a0dcbdce5043937216 | present | 318 |
| RC-24 | Pinned TaskCounts records malformed_lines | misthelper-devtools:src/misthelper_devtools/speckit_task_audit.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a00b367af777c8be44fbe9a0dcbdce5043937216 | present | 122 |
| RC-25 | Pinned report prints the path and line of each malformed marker | misthelper-devtools:src/misthelper_devtools/speckit_task_audit.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a00b367af777c8be44fbe9a0dcbdce5043937216 | present | 428 |
| RC-26 | Merge commit da96d6e holds the same file blob as the pin | misthelper-devtools:src/misthelper_devtools/speckit_task_audit.py | da96d6e57a9bba7c7824f703c7cd722732010655 | a00b367af777c8be44fbe9a0dcbdce5043937216 | present | 318 |
| RC-27 | Pinned commit has no _count_line method | misthelper-devtools:src/misthelper_devtools/speckit_task_audit.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a00b367af777c8be44fbe9a0dcbdce5043937216 | absent | 285 |
| RC-28 | Pinned exit code is 1 for a complete record with open tasks | misthelper-devtools:src/misthelper_devtools/speckit_task_audit.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a00b367af777c8be44fbe9a0dcbdce5043937216 | present | 355 |
| RC-29 | Pinned test file names the link and legend test | misthelper-devtools:tests/unit/tools/test_speckit_task_audit.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 336f030ae5fd37b4512f89d7bc4ffbf3fb6afaee | present | 66 |
| RC-30 | Pinned test file names the file and line report test | misthelper-devtools:tests/unit/tools/test_speckit_task_audit.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 336f030ae5fd37b4512f89d7bc4ffbf3fb6afaee | present | 89 |
| RC-31 | Pinned test file names the missing citation test | misthelper-devtools:tests/unit/tools/test_speckit_task_audit.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 336f030ae5fd37b4512f89d7bc4ffbf3fb6afaee | present | 155 |
| RC-32 | Pinned test file names the unchecked complete spec test | misthelper-devtools:tests/unit/tools/test_speckit_task_audit.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 336f030ae5fd37b4512f89d7bc4ffbf3fb6afaee | present | 25 |
| RC-33 | Guard file imports TaskFileScanner | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 11 |
| RC-34 | Guard file asserts the counts of a grouped task file | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 228 |
| RC-35 | Guard file ends with the duplicate identity test, at 278 lines | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 254 |
| RC-36 | Command test runs speckit-task-audit | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 207 |
| RC-37 | Command test asserts the summary line | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 224 |
| RC-38 | Command test asserts the completion line | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 237 |
| RC-39 | Quality gates document names the audit job | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 14 |
| RC-40 | Contributor guide lists the speckit-task-audit command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 40 |
| RC-41 | Container build table row limits runs to product file changes | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| RC-42 | Changelog README names the issue file form | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-43 | Changelog policy defines the issue name pattern | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| RC-44 | Changelog policy defines the change type words | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 45 |
| RC-45 | Spec route script sets the base to five | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-46 | Route folder for issue 4703 is absent | specs/numbered/0/0/1/2/2/3/0/3 | main | none | absent | 0 |
| RC-47 | Reference record status line reads Draft | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 7 |
| RC-48 | Guard folder holds 79 direct entries | tests/guardrails | main | none | present | 0 |

## Sources

**Local, read-only (repository root `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`)**

- `AGENTS.md`, `.github\copilot-instructions.md`, `.specify\memory\constitution.md`, and the four templates in `.specify\templates\`.
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv\` (reference record), read for shape only.
- `documentation\quality-gates.md`, `changelog.d\README.md`, `tests\guardrails\test_process_folder_structure.py`, and `tests\guardrails\test_changelog_fragment_policy.py`. Local copies informed the search. Each claim cites the remote row above.
- `.venv\Lib\site-packages\misthelper_devtools\speckit_task_audit.py` (local-only, not proof). It holds the repair at lines 122, 288 to 299, 318, and 427.

**Remote, GitHub API through `gh` (GET only)**

- MistHelper: `gh issue view 4703`, `4765`, and `4806`. `gh pr list --search 4703` (empty result). `gh pr view 4836`, `4871`, `4806`, and `4888`. `gh pr list --search "misthelper-devtools in:title,body"`. `gh run list` for workflow `Quality Gates`. `gh api repos/jmorrison-juniper/MistHelper/actions/runs/<id>/jobs`. `gh run view <id> --job <id> --log` and `--log-failed`.
- MistHelper contents: `https://api.github.com/repos/jmorrison-juniper/MistHelper/contents/<path>?ref=<ref>`, for each row above.
- MistHelper tree: `https://api.github.com/repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`.
- Upstream contents: `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/contents/src/misthelper_devtools/speckit_task_audit.py?ref=<ref>` for refs `e8e093d205428b5503887267b6a9751fa7354be7`, `da96d6e57a9bba7c7824f703c7cd722732010655`, and `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- Upstream test file: `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/contents/tests/unit/tools/test_speckit_task_audit.py?ref=2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- Upstream comparisons: `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/compare/da96d6e57a9bba7c7824f703c7cd722732010655...2239e7bd468fd27e40c43f2b87fcd35a2e49672b` and `.../compare/e8e093d205428b5503887267b6a9751fa7354be7...2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- Upstream pull request and issue: `gh pr view 89` and `gh issue view 88` in `misthelper-devtools`. `gh pr view 84` returned no pull request.
- Commit existence: each commit in R2 and R3 returned its SHA. The unpublished local commits `bf4b6c8654311e067a6db194df3e8c0880ad16bc`, `e1d14724c3b095c308636ebc2c73b4fc8196fa3b`, and `235bba537aeda7eb0e37f203f88dd731886b993a` returned HTTP 422, so they are absent from GitHub.

## Unverified

- **U1. Authorization of the pin update.** Pull request #4836 merged the pin change on 2026-11-19. No comment on issue #4703 or issue #4765 authorizes that change. Reason: the issue trail holds no explicit approval. The orchestrator confirms it at T-MERGE.
- **U2. The 27 and nine split of the 36 markers.** Reason: the CI log at `3964d21` shows only the total. The split needs a scan of 405 task files at that commit, which this phase does not run.
- **U3. Test execution.** Reason: the rules forbid running tests in this phase. The upstream CI run on `2239e7bd` shows success at the run level. Its job logs were not read.
- **U4. Failure of the negative regression test under `e8e093d`.** Reason: this is a static proof from RC-20 and RC-21. The implementer may confirm it with a temporary local install of `e8e093d`.
- **U5. The pull request number in PR #4836.** Reason: the PR body names misthelper-devtools PR #84, and GitHub returns no pull request for that number. The commit message names PR #95. The reason for the mismatch is unknown.
- **U6. Version of the local `.venv` copy.** Reason: the local copy has no version metadata that this phase read. The copy is local-only evidence (A7).
