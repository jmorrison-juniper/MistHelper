# Research: Firmware Monitor Treats Failed Stats Pages as Failed Checks

## Procedure Log

- Read in full: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the four templates in `.specify/templates/`.
- Read the reference record headings and shape in `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. Its content was not copied.
- Read the issue with `gh issue view 4710` (body, labels, and four comments). Read the related issues #4709, #1910, and #2753 with `gh issue view`.
- Ran `gh pr list --search 4710` (empty result). Searched `specs\` for folders starting with `4710-` (none).
- Fetched the remote tree of `main` once with `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The tree holds 11,404 entries and is not truncated. Filtered it in PowerShell with the same regular expression as the brief.
- Decoded remote file bodies with `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main --jq .content`. Decoded the base64 text in PowerShell and searched it for each symbol.
- Compared the baseline with the compare endpoint, using base commit 3964d21d and head main. Read commit records with the commits endpoint. Read the label list with `gh label list`.
- Read local git data with `git -C <repo> rev-parse HEAD:<path>`, `git -C <repo> ls-files -s`, and `git -C <repo> log -- <path>`. These commands are read-only.
- Read the installed SDK in `.venv\Lib\site-packages\mistapi` with read-only views and searches.
- Ran no build, test, lint, formatter, package install, container, or repository script. Wrote files only in `DRAFT_DIR` and `META_DIR`.
- Used `tool_search_tool` once to list GitHub read tools. The brief requires `gh` for GitHub reads, so the GitHub MCP tools were not used.
- Loaded no skill. No listed skill covers Python HTTP status handling or Mist stats pagination. The Podman and `juniper-*` skills do not apply to this change.
- Did not use `web_fetch`. Each claim has a local file or a GitHub source.

## Decisions

Each decision names the chosen option, the alternatives, the reason, and the risk. None of the decisions needs a human decision under brief section 6.

### D-1: Walk stats pages with `mistapi.get_next`, and check each page

- Decision: Request each later page with `mistapi.get_next`. Check the status and the body of each page before its rows enter the result.
- Alternatives: (a) Keep `mistapi.get_all` and check only the first page. (b) Call `listOrgDevicesStats` with explicit `page` numbers and read the headers. (c) Wrap `get_all` in `try` and `except`.
- Reason: `get_all` never checks a later page status (RC-57). It returns the rows it collected (RC-57). It cannot see a failed page that returns an empty body without an exception (RC-58). Option (b) copies the SDK link logic (RC-59). Option (c) does not catch a failed page that returns no exception.
- Risk: The SDK link logic stops the walk silently when `X-Page-Page` is not an integer (RC-59). Decision D-4 closes that gap.

### D-2: Strict HTTP status, and no change to `_response_status_code`

- Decision: A page passes only when `status_code` equals the integer `_HTTP_OK` (200). Keep `_response_status_code` unchanged.
- Alternatives: (a) Change the helper default for a missing status to `None`. (b) Reuse `_response_status_code` with a `>= _HTTP_ERROR_MIN` test, as at `firmware_manager.py` lines 3498 and 3519.
- Reason: The helper returns 200 for a missing or non-integer status (RC-37). Option (b) would accept a missing status as success. Option (a) changes every caller of the helper, and issue #2753 owns that audit.
- Risk: Other callers keep the masked default. Follow-up F-02 and issue #2753 cover it.

### D-3: Raise `RuntimeError` in the fetch method

- Decision: Raise `RuntimeError` when a page fails. The existing `except Exception` in `_execute_monitoring_check` returns no count (RC-45). The retry policy then counts the failure (RC-38).
- Alternatives: (a) Return `None` from the fetch method. (b) Add a new exception class and a new exit code.
- Reason: Option (a) needs a new return contract for the caller. Option (b) adds a module-level class, which the five-item rule forbids in this module (plan, Five-Item Record). A new exit code breaks FR-011.
- Risk: `logging.exception` writes a traceback for each failed check. That behavior exists today.

### D-4: Check the announced row total

- Decision: After the walk, compare the number of collected rows with `X-Page-Total` from the last page. Raise when the count is lower. A non-integer header raises `ValueError` through `int()`. The status check handles both as failures.
- Alternatives: (a) Trust the next link only. (b) Count pages instead of rows.
- Reason: The SDK reads `X-Page-Total` as the item total (`__api_response.py` line 84). A next link can be missing while the total says more rows exist. The comment on issue #4709 dated 2026-11-09T15:12:00Z reports one row with a total of two and no next link.
- Risk: The meaning of the header comes from SDK code only (item U-02).

### D-5: Guard against a repeated next link, without a page-count constant

- Decision: Keep a set of followed next links. Raise when a link repeats. Use no page-count constant.
- Alternatives: (a) A module-level page cap. (b) No guard.
- Reason: A module-level constant adds a direct child to a grandfathered module, which the constitution forbids. A repeated link is a clear signal of a stopped cursor.
- Risk: A server that never repeats a link and never ends the walk runs forever. The SDK `get_all` has the same property (RC-57). Follow-up F-02 covers it.

### D-6: Edit the existing method in place

- Decision: Edit `_fetch_device_stats_for_monitoring` only. Add no module, class, method, or constant. Record the grandfathered debt. Remediation R-01 is a separate issue.
- Alternatives: (a) A new module under `src/operations/execution/firmware/`. (b) A new package under `src/operations/`, `src/mist/`, or `src/operations/execution/`. (c) Helper methods in class `FirmwareManager`.
- Reason: Each option adds a direct child to a noncompliant parent (research R-06). The constitution forbids that (`constitution.md` line 42). Option (a) and option (c) are the only options that keep the code near its caller.
- Risk: The grandfathered class grows by one changed method body. Remediation R-01 removes the debt.

### D-7: Add the tests to the existing test module

- Decision: Add tests N1 to N14 to the existing test module. Put them in the existing classes for fetch, status check, and loop retry. Update tests U1 and U2.
- Alternatives: (a) A new test module under `tests/unit/firmware/`. (b) A new test package.
- Reason: The folder `tests/unit/firmware/` holds 9 children (R-06). The issue comment dated 2026-11-09T15:15:42Z reserves the existing module for these regression tests.
- Risk: The module and its classes grow. The growth is recorded as debt in the plan.

### D-8: Keep `needs-human-review`, and do not add `auto-merge`

- Decision: Keep the `needs-human-review` label. Do not add the `auto-merge` label. Merge waits for a human review and for the orchestrator authorization.
- Alternatives: (a) Enable auto-merge after the remote CI passes. (b) Record the review as a human decision under brief section 6.
- Reason: The issue requires human review (issue body, "requires human review"). `AGENTS.md` line 230 bars `auto-merge` on a pull request that changes a destructive operation. Menu 137 is not destructive (RC-27), so the review is a process gate. Brief section 6 does not list process gates, so option (b) does not apply.
- Risk: Merge waits for review. The wait is accepted.

### D-9: Keep the other defects out of this change

- Decision: Keep the pin text, the site field set, the other `get_all` call sites, and the exporter of issue #4709 out of this change. File follow-up issues F-02, F-03, and F-04.
- Alternatives: (a) Fix them in this change. (b) Leave them undocumented.
- Reason: `AGENTS.md` line 185 says that one issue holds one subject. A combined change would be hard to review and harder to revert.
- Risk: The same defect class remains in other flows until F-02 completes.

## Evidence

### R-01: Path from menu 137 to the API call

- Menu 137 (`MistHelper.py` lines 5192 to 5202, RC-24, RC-25) calls `_build_firmware_manager` and then `check_firmware_upgrade_status`.
- `check_firmware_upgrade_status` (`firmware_manager.py` line 318, RC-31) resolves the scope. Scope 5 calls `_continuous_monitoring_mode` (lines 365 to 369, RC-32).
- `_continuous_monitoring_mode` (line 377) calls `_run_monitoring_loop` (line 417, RC-33).
- The loop calls `_execute_monitoring_check` (line 702). That method calls `_fetch_device_stats_for_monitoring` (line 637, RC-41).
- The fetch method calls `listSiteDevicesStats` for a site (line 640, RC-42) or `listOrgDevicesStats` for the org (line 644, RC-43). It returns `mistapi.get_all` output (line 647, RC-44).

### R-02: Why the current code reports completion

- A 403 with a JSON body on the first page gives `data` as a dictionary without `results`. `get_all` returns an empty list (`__pagination.py` lines 55 to 74, RC-57).
- An HTTP 503 with an empty body gives `data` as `{}`. The JSON decode fails (`__api_response.py` lines 39 and 55 to 68, RC-58). `get_all` returns an empty list.
- An empty list gives a count of zero (`_execute_monitoring_check` line 721, `len(active_upgrades)`).
- A count of zero prints the completion banner (line 511, RC-40) and returns `True`. The loop then returns `MONITOR_EXIT_COMPLETE` (line 435, RC-39), which is 0 (line 56, RC-36).

### R-03: SDK pagination facts (installed mistapi 0.64.1)

- `mistapi/__init__.py` lines 15 and 16 export `get_all` and `get_next` (RC-55).
- `get_next` returns `mist_session.mist_get(response.next)` when `response.next` is set (`__pagination.py` lines 33 and 34, RC-56).
- `get_all` returns collected rows and never checks the status of a later page (lines 55 to 74, RC-57).
- `APIResponse.__init__` takes a `requests.Response` (lines 27 to 29). It copies the status and headers (lines 46 to 48). It keeps `data` as `{}` and `next` as `None` by default (lines 39 and 41). It sets `status_code` to `None` by default (line 43, RC-58).
- An HTTP status of 400 or more only logs an error (lines 60 to 64). It raises nothing.
- `_check_next` reads `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` (lines 75 to 78). It sets `next` only when `limit * page < total` (line 84). A non-integer header raises `ValueError`, which is logged and leaves `next` unset (lines 83 and 96, RC-59).
- `listOrgDevicesStats` accepts `page` (line 411, RC-60). It sends the request with `mist_get` (`orgs/stats.py` line 484).
- `listSiteDevicesStats` has no `fields` parameter (`sites/stats.py` line 1051, RC-61).

### R-04: OpenAPI facts for the endpoints

- `listOrgDevicesStats` is the operation at `/api/v1/orgs/{org_id}/stats/devices`, line 21390 (`operationId` at line 21396, RC-18).
- Its response codes are 200, 400, 401, 403, 404, and 429 (lines 21444 to 21456). No 503 response is documented (RC-19).
- Its 200 response references `DevicesArrayStatsOrg`, which references `stats_devices` (lines 21445 to 21446 and 62199 to 62200). The `stats_devices` schema is an array (line 107508, RC-20).
- The site operation `listSiteDevicesStats` (line 39555) returns `DevicesArrayStatsSite`. That component references `stats_devices` (line 62223, RC-21).
- The description of the org operation says that pagination uses the response headers (lines 21392 to 21395). The OpenAPI file does not name the headers. A search for `X-Page` in the file found no match.
- The `fields` parameter is described as additional fields (lines 59673 to 59675).
- The `fwupdate` field appears in the typed schemas `stats_ap` (line 105513), `stats_gateway` (line 107593), and `stats_switch` (line 109864).
- The `stats_device` schema holds a `mac` field at line 107198. The natural key of a device row is the `mac` value.
- The Mist endpoint table lists `listOrgDevicesStats` at `documentation/MIST_API_GET_ENDPOINTS.md` line 895 (RC-22).

### R-05: Retry policy and wait times

- `MonitoringRetryPolicy` (class at line 144) holds `consecutive_failures`. `record_success` (line 159) resets it. `record_failure` (line 163) increments it.
- `exhausted` (line 173) becomes true at `MONITOR_MAX_CONSECUTIVE_FAILURES` (5, line 52).
- `next_delay_seconds` (line 177) returns 7 for a healthy check. After `n` failures it returns `min(7 * 2 ** (n - 1), 60)`.
- The waits between checks are 7, 14, 28, and 56 seconds. The fifth failure stops the loop with no wait, so the total wait is 105 seconds.
- The current code never reaches this path for an HTTP 403 or 503 (R-02).

### R-06: Five-item evidence and folder counts

- Decoded remote file `firmware_manager.py` holds 4,365 lines (RC-30).
- Child counts from the local checkout, excluding `__pycache__`: `src` 46, `src\operations` 5, and `src\operations\execution` 6.
- More child counts: `src\operations\execution\firmware` 12, `src\mist` 5, `src\foundation` 6, and `src\interfaces` 4.
- Test and changelog child counts: `tests\unit\firmware` 9, `tests\unit\export` 55, and `changelog.d` 335.
- Route chain counts: `specs\numbered` 1, `specs\numbered\0` 1, `specs\numbered\0\0` 2, `specs\numbered\0\0\1` 3, `specs\numbered\0\0\1\2` 5, `specs\numbered\0\0\1\2\2` 3, `specs\numbered\0\0\1\2\2\3` 3, and `specs\numbered\0\0\1\2\2\3\2` 2. The leaf `specs\numbered\0\0\1\2\2\3\2\0` is absent.
- The constitution limits are at `constitution.md` lines 77 to 85. The five-item rule is at line 38. The rule against a new child in a noncompliant parent is at lines 42 and 43. The edit allowance for an existing child is at line 53.

### R-07: Route and placement

- The route for issue 4710 comes from base 5. The digits of 4710 are 1, 2, 2, 3, 2, 0. Padded to eight digits, the route is `00122320`. The record path is `specs\numbered\0\0\1\2\2\3\2\0\4710-firmware-monitor-failed-pages`.
- The width default is 8 (`spec-route.ps1` line 7). The base is 5 (line 17). The numbered route function is at line 34.
- The reference record 4920 gives `00124140`. Its folder `specs\numbered\0\0\1\2\4\1\4\0` matches the same method.
- The destination check (`Assert-SpecFeatureDestination`, line 76) refuses a new child under a parent that already holds five children. The only new folder is the leaf. Its parent `specs\numbered\0\0\1\2\2\3\2` holds two children, so the check passes.

### R-08: Test strategy

- Tests N1 to N14 and U1 to U2 use mocked SDK objects. Each fake `get_next` counts calls and raises after 40 calls. The existing module already defines the ceiling `_CHECK_CALL_CEILING` for the same reason (line 46 area, class `_ScriptedCheck` at line 50).
- Test N14 builds a `requests.Response`, then an `APIResponse` from the installed SDK. It then calls the SDK `get_all` and records the empty list.
- Tests N9, N10, and N14 pass before the change. The other 11 new tests fail before the change, so they prove the defect.
- The existing tests that stay unchanged are `test_response_status_code_preserves_http_failure_status` (line 124), `TestRunMonitoringLoop` (line 209), `TestMonitoringRetryPolicy` (line 271), and `TestRunMonitoringLoopRetryBound` (line 315).
- The tests U1 and U2 monkeypatch `fm_mod.mistapi`. The current doubles return plain strings and use `get_all` (lines 654 and 677, RC-50 and RC-51). The updated doubles return page objects with a status, a list body, headers, and a next link.

### R-09: Local gates that apply

The local gates table is in `.github/copilot-instructions.md` lines 57 to 76 (RC-04). The table has no function-length row, so the reviewer checks the 25-line limit by reading.

- Applies, part one: Compile (line 57), Lint (58), Format (59), and Types (60). Types reads `MYPY_PATHS` (RC-05).
- Applies, part two: Tests (61), Full tests (62), Safe sweep (63), Coverage (64), Test quality (65), and Complexity (66).
- Applies, part three: Security lint (67), Code quality (69), and Dead code (70). Dead code reads `VULTURE_PATHS` (RC-06).
- Applies, part four: Docstrings (71), Symbols (73), and STE (74). Docstrings reads `PYDOCSTYLE_PATHS` (RC-07) and `INTERROGATE_PATHS` (RC-08).
- Does not apply: Dependency audit (68), because no dependency file changes. Menu reference (72), because no menu or registry file changes. Ops portal (75) and Ops platform (76), because those folders do not change.
- The safe sweep (63) runs the `safe` category only. Menu 137 is `interactive` (RC-26), so the sweep does not exercise the monitor. The unit tests carry the proof.

### R-10: Pin drift

- `copilot-instructions.md` line 21 says `mistapi>=0.64.0,<0.65`.
- `pyproject.toml` line 29 says `>=0.64.1,<0.65` (RC-28).
- `requirements.txt` line 129 says `==0.64.1` (RC-29).
- `constitution.md` line 279 says `0.59+`.
- The installed package is 0.64.1 (RC-54). It satisfies each statement. The drift is out of scope (decision D-9, follow-up F-04).

### R-11: Labels

- The repository has labels `feature-spec`, `firmware`, `needs-human-review`, and the pipeline labels `stage:*` and `status:*`.
- The issue has `bug`, `tests`, `in-progress`, and `needs-human-review`.
- `labels_to_add`: `feature-spec` and `firmware`. `labels_to_remove`: none. The label `stage:ste-validated` is not added, because the brief forbids the STE linter run in this session.

### R-12: Human review and merge

- `AGENTS.md` line 230 bars `auto-merge` on a pull request that changes a destructive operation. Line 233 starts the Merge section.
- The issue body says that the change requires human review. The comments of 2026-11-09 say that `needs-human-review` remains and that merge needs a review.
- Menu 137 is not destructive (RC-27). The review is a process gate.

### R-13: Issue comments used as clarifications

- Issue #4710, comment dated 2026-11-09T14:59:15Z: a missing or non-integer status is a failed check. The helper default is not proof of success.
- Issue #4710, comment dated 2026-11-09T15:15:42Z: a status check on the first page alone is not sufficient. Reserve tests in `tests/unit/firmware/test_firmware_manager_monitoring.py`.
- Issue #4710, comment dated 2026-11-09T15:29:33Z: the reserved regression tests reproduce the defect. The test file is local and uncommitted. The git history of `main` shows the file committed. Finding A-02 records the difference.
- Issue #4709, comment dated 2026-11-09T15:12:00Z: a total larger than the rows with no next link can write incomplete rows. Decision D-4 covers it.
- Issue #4709, comment dated 2026-11-09T14:55:03Z: the #1794 owner retains the exporter file. Coordinate before a second source edit. Finding A-03 records it.

### R-14: What this change does not do

- It does not change menu 137, the scope prompt, the confirmation rules, or the destructive category.
- It does not change the exit codes, the refresh cadence, the backoff constants, or the helper `_response_status_code`.
- It does not change the mistapi pins, the site field set, the exporter for #4709, or the other `get_all` call sites.
- It does not run live Mist, SSH, firmware, or database operations.

## Remote Verification Table

Rows RC-01 to RC-61 match the `remote_checks` array in `4710-STATUS.json` one for one. The method column tells how each row was checked.

| ID | Claim | Path | Ref | Blob or commit SHA | Method | Result | Line |
| - | - | - | - | - | - | - | - |
| RC-01 | Remote main head matches the record baseline | heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | git ref API | present | 0 |
| RC-02 | Issue baseline commit is an ancestor of main | commit 3964d21d03f9f5717cb8eafb7272ecff21f5362a | main | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | compare API, ahead 88, behind 0 | present | 0 |
| RC-03 | Rules file AGENTS.md exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | tree | present | 0 |
| RC-04 | Repository instructions hold the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | blob equal to HEAD | present | 57 |
| RC-05 | CI defines MYPY_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | decode | present | 93 |
| RC-06 | CI defines VULTURE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | decode | present | 101 |
| RC-07 | CI defines PYDOCSTYLE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | decode | present | 104 |
| RC-08 | CI defines INTERROGATE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | decode | present | 107 |
| RC-09 | Constitution Principle I exists | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | blob equal to HEAD | present | 38 |
| RC-10 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | tree | present | 0 |
| RC-11 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | tree | present | 0 |
| RC-12 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | tree | present | 0 |
| RC-13 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | tree | present | 0 |
| RC-14 | Route base is 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | decode | present | 17 |
| RC-15 | Numbered route function exists | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | decode | present | 34 |
| RC-16 | Reference record spec exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | tree | present | 0 |
| RC-17 | No record folder for issue 4710 exists under specs | specs/**/4710-* | main | none (tree filter) | tree filter, zero paths | absent | 0 |
| RC-18 | OpenAPI defines operation listOrgDevicesStats | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | blob equal to HEAD | present | 21396 |
| RC-19 | listOrgDevicesStats documents no HTTP 503 response | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | blob equal to HEAD, negative search | absent | 21444 |
| RC-20 | stats_devices schema is an array | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | blob equal to HEAD | present | 107508 |
| RC-21 | Site stats response references stats_devices | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | blob equal to HEAD | present | 62223 |
| RC-22 | Endpoint table lists listOrgDevicesStats | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | blob equal to HEAD | present | 895 |
| RC-23 | Operator guide describes no monitor exit behavior | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | blob equal to HEAD, negative search | absent | 0 |
| RC-24 | Menu 137 entry exists | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | decode | present | 5192 |
| RC-25 | Menu 137 handler builds FirmwareManager | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | decode | present | 5194 |
| RC-26 | Menu 137 category is interactive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | decode | present | 112 |
| RC-27 | Menu 137 is not destructive | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | blob equal to HEAD | present | 5202 |
| RC-28 | pyproject allows mistapi >=0.64.1,<0.65 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | decode | present | 29 |
| RC-29 | requirements.txt pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | decode | present | 129 |
| RC-30 | Monitor module exists | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | tree | present | 0 |
| RC-31 | Check entry method exists for the menu flow | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 318 |
| RC-32 | Scope 5 calls the monitor and drops the exit code | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | blob equal to HEAD | present | 367 |
| RC-33 | Monitoring loop exists | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 417 |
| RC-34 | Monitor HTTP OK constant is 200 | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 29 |
| RC-35 | Monitor failure limit is 5 | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 52 |
| RC-36 | Monitor completion exit code is 0 | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 56 |
| RC-37 | Status helper defaults a missing status to 200 | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 73 |
| RC-38 | Retry policy class exists | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 144 |
| RC-39 | Loop returns completion on handler success | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 435 |
| RC-40 | Completion banner prints when zero upgrades | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 511 |
| RC-41 | Fetch helper exists | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 637 |
| RC-42 | Fetch helper calls the site stats endpoint | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 640 |
| RC-43 | Fetch helper calls the org stats endpoint | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 644 |
| RC-44 | Fetch helper returns get_all output without a status check | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 647 |
| RC-45 | Status check returns no count on exception | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 722 |
| RC-46 | Other get_all call sites exist in the module | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | decode | present | 3526 |
| RC-47 | Monitor test module exists | tests/unit/firmware/test_firmware_manager_monitoring.py | main | a1352b35db33160e957423569aab9ac47bf3fd3a | tree | present | 0 |
| RC-48 | Monitor test module has no HTTP 403 test | tests/unit/firmware/test_firmware_manager_monitoring.py | main | a1352b35db33160e957423569aab9ac47bf3fd3a | decode, negative search | absent | 0 |
| RC-49 | Monitor test module covers the status helper with HTTP 503 | tests/unit/firmware/test_firmware_manager_monitoring.py | main | a1352b35db33160e957423569aab9ac47bf3fd3a | decode | present | 123 |
| RC-50 | Site fetch test double returns a plain string | tests/unit/firmware/test_firmware_manager_monitoring.py | main | a1352b35db33160e957423569aab9ac47bf3fd3a | decode | present | 654 |
| RC-51 | Org fetch test double returns a plain string | tests/unit/firmware/test_firmware_manager_monitoring.py | main | a1352b35db33160e957423569aab9ac47bf3fd3a | decode | present | 677 |
| RC-52 | Version test monkeypatches continuous monitoring | tests/unit/firmware/test_firmware_manager_version.py | main | 00c7815277f3a58b227a41404ce3500bb60c4500 | decode | present | 258 |
| RC-53 | Sibling exporter calls get_all (issue #4709) | src/operations/exporting/export/site_other_device_events_exporter.py | main | 60f1ac7fdd966ef4cd7b38b4e3f6cd314d1fbf3a | decode | present | 76 |
| RC-54 | Installed mistapi version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | installed mistapi 0.64.1 | none (installed file) | local read | present | 3 |
| RC-55 | SDK exports get_next | .venv\Lib\site-packages\mistapi\__init__.py | installed mistapi 0.64.1 | none (installed file) | local read | present | 16 |
| RC-56 | SDK get_next returns the next page through mist_get | .venv\Lib\site-packages\mistapi\__pagination.py | installed mistapi 0.64.1 | none (installed file) | local read | present | 17 |
| RC-57 | SDK get_all returns rows with no page status check | .venv\Lib\site-packages\mistapi\__pagination.py | installed mistapi 0.64.1 | none (installed file) | local read | present | 39 |
| RC-58 | SDK APIResponse status defaults to None | .venv\Lib\site-packages\mistapi\__api_response.py | installed mistapi 0.64.1 | none (installed file) | local read | present | 43 |
| RC-59 | SDK leaves next unset when X-Page-Page is not an integer | .venv\Lib\site-packages\mistapi\__api_response.py | installed mistapi 0.64.1 | none (installed file) | local read | present | 96 |
| RC-60 | SDK listOrgDevicesStats accepts page | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | installed mistapi 0.64.1 | none (installed file) | local read | present | 411 |
| RC-61 | SDK listSiteDevicesStats has no fields parameter | .venv\Lib\site-packages\mistapi\api\v1\sites\stats.py | installed mistapi 0.64.1 | none (installed file) | local read | absent | 1051 |

Count: 61 rows. The table has 61 rows, and `remote_checks` has 61 entries.

## Sources

- Local, read-only, governance: `AGENTS.md`, `.github/copilot-instructions.md`, `.github/workflows/ci.yml`, `.specify/memory/constitution.md`, and `.specify/templates/*.md`.
- Local, read-only, route and documents: `.specify/scripts/powershell/spec-route.ps1`, `documentation/mist-api-openapi31yaml.yaml`, and `documentation/MIST_API_GET_ENDPOINTS.md`.
- Local, read-only, monitor documents: `documentation/operator-guide.md` and `documentation/architecture.md` (monitor terms searched, no match).
- Local, read-only, code and tests: `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, and `src/operations/execution/firmware/firmware_manager.py`.
- Local, read-only, related code and tests: `src/operations/exporting/export/site_other_device_events_exporter.py`, `tests/unit/firmware/test_firmware_manager_monitoring.py`, and `tests/unit/firmware/test_firmware_manager_version.py`.
- Local, read-only, packages: `pyproject.toml` and `requirements.txt`.
- Installed SDK, read-only: `.venv\Lib\site-packages\mistapi\__init__.py`, `__pagination.py`, `__api_response.py`, `api\v1\orgs\stats.py`, `api\v1\sites\stats.py`, and `mistapi-0.64.1.dist-info\METADATA`.
- GitHub, read-only: issues #4710, #4709, #1910, and #2753. The `main` tree, contents, and ref. The compare and commit endpoints. The label list.
- Web: none.

## Unverified

- U-01: The default fields of `listSiteDevicesStats` rows, and whether `fwupdate` appears without a `fields` argument. Reason: the OpenAPI describes `fields` as additional fields (lines 59673 to 59675). The installed SDK function has no `fields` parameter (RC-61). The brief forbids a live sample.
- U-02: The meaning and presence of `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` on the stats endpoints. Reason: the OpenAPI does not document these headers. The only source is SDK code (RC-59 and `__api_response.py` line 84). The brief forbids a live sample.
- U-03: The live behavior of Mist for an HTTP 503 with an empty body. Reason: the brief forbids live Mist calls. The tests use synthetic responses that follow the SDK code.
- U-04: Whether org rows carry `fwupdate` when the request passes `fields="*"`. Reason: the typed schemas list `fwupdate` for `stats_ap` (line 105513), `stats_gateway` (line 107593), and `stats_switch` (line 109864). No live row was read.

## Validation Not Possible

- No build, test, lint, format, type check, STE check, or container run was possible in this session. Brief rule 2 forbids each of them.
- The gap is covered by the gate tasks T-LOCAL-GATES, T-REMOTE-CI, and T-MERGE in `tasks.md`. Each gate runs before the pull request merges.
