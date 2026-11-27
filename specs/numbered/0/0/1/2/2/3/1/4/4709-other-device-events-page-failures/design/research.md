# Research: Other-Device Event Export Fails Closed on Failed Pages

**Issue**: #4709. **Date**: 2026-11-26. **Base**: `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## 1. Method

1. Read issue #4709 with `gh issue view`. The issue has three owner comments. Read the related issues #1794, #4707, and #4710. Searched for linked pull requests with `gh pr list --search 4709`. The search returned no pull request.
2. Read the governing documents in full or in ranges: `AGENTS.md`, `.github/copilot-instructions.md`, the constitution, the four Spec Kit templates, `documentation/quality-gates.md`, `architecture.md`, `development-setup.md`, `container-deployment.md`, and the operator guide (searched).
3. Fetched the remote tree of `main` once with `git/trees/main?recursive=1`. The tree holds 11,404 entries and is not truncated. Read the blob SHA of each cited file from that tree.
4. Decoded the remote bodies of the exporter, its test file, the owner candidate commit, and each cited symbol. Each symbol match gives the remote line number.
5. Method note: `git hash-object` of each cited repository file in the local checkout matched its remote blob SHA for all 24 checked files. For these files, local line numbers equal remote line numbers.
6. SDK claims cite the installed `mistapi` 0.64.1 files in `.venv\Lib\site-packages\mistapi`. Their blob SHAs come from `git hash-object --no-filters`.
7. Mist API claims cite `documentation/mist-api-openapi31yaml.yaml`, as the brief requires.
8. No skill was loaded. The issue concerns no Podman behavior and no Juniper device behavior.
9. No URL was fetched. No source in this research uses a web page.
10. No live Mist call, no test run, and no gate run took place. The brief forbids them for this task.

## 2. Findings

**F-1 First page.** `other_device_events` passes the SDK response to `mistapi.get_all` with no status check (RC-02, exporter line 76). A 403 or 503 JSON error gives `data` as a dict with no `results` key. `get_all` then returns an empty list (RC-66, `__pagination.py` lines 65 and 74). The exporter prints the no-data message (RC-03, lines 30 to 34). This is the issue's first case.

**F-2 Later page, list shape.** `get_all` adds each later page's `data` to the rows (RC-65, `__pagination.py` line 62). A page with an empty body keeps `data` as `{}` and `next` as `None` (RC-68, `__api_response.py` lines 39 and 41, and the parse path at lines 55 to 57). The list branch adds no rows, and the export reports success. This is the issue's second case.

**F-3 Later page, dict shape.** The documented search response is a dict with `results` (OpenAPI schema lines 94488 to 94511, RC-23 and RC-24). For a later dict page with no `results` key, `get_all` evaluates `response.data["results"]` (RC-66, line 71). The `KeyError` reaches the exporter outer guard (RC-04, lines 83 to 89). The read then fails with no file, but the message names a key and omits the HTTP status.

**F-4 Completeness.** `get_all` follows only `next` values. When a page reports `total` above its row count and has no `next` value, the read ends short. The owner comment reports this case (RC-61). The schema defines `total` as the count across all pages (RC-23). A non-integer `X-Page-Page` header also stops pagination silently (RC-69, `__api_response.py` lines 75 to 80).

**F-5 Transport failure.** A connection failure returns an `APIResponse` with status `None` (RC-72, `__api_request.py` lines 225 and 258). The request layer does not raise. A missing status must therefore count as a failure (FR-003).

**F-6 Retries.** The request layer retries HTTP 429 inside `__api_request.py`, starting at line 228. The exporter adds no retry (C-4).

**F-7 Owner candidate.** Commit `196af800` adds per-page status and cursor checks (RC-05, lines 56 to 98 in the candidate). It has no `total` check and no header check (RC-06). Both owner commits are ancestors of the archive branch head (RC-51, RC-52, RC-53). The owner comment that calls the candidate unpublished is stale (RC-60).

**F-8 In-repo pattern.** The wifi exporter requests later pages with `mistapi.get_next` (RC-16, line 205). It validates each page before it accepts rows (RC-17, line 250). It uses the shared integrity checker for malformed bodies (RC-18, line 266). Its test module holds one parameterized test for the four failure shapes (RC-20, line 51). This change follows that pattern, without the wifi partial-read branch (D-3).

**F-9 Entry points.** Menu 258 registers the exporter handler (RC-10, `MistHelper.py` line 4998). The web portal lists menu 258 as a site-only operation (RC-11, line 452). Both entry points reach the same function.

**F-10 Keys.** The endpoint key strategy uses the composite key `mac` and `timestamp` (RC-12, line 529). The writer contract stays unchanged (RC-13).

**F-11 Gates.** The CI path variables set the gate scope (RC-26 to RC-30). The test quality row names the gate command (RC-42). The copilot-instructions rule requires HTTP 4xx and 5xx tests for an API client test module (RC-74).

**F-12 Scope.** The organization audit log export has the same first-page-only pattern (RC-21). It stays out of scope under FR-022 (D-14).

**F-13 GitHub state.** Issue #4709 is open (RC-59). Issues #1794, #4707, and #4710 are open (RC-56, RC-57, RC-58). Seven pull requests are open, and none touches an owned file (RC-55). The owner comment that names 27 open pull requests is stale (analysis A-10).

**F-14 SDK window.** The SDK search docstring states the `duration` default as `1d` (RC-71). The exporter sends no duration. The API default window applies (A-4).

**F-15 Existing record.** No folder named `4709-*` exists under `specs`, `finished-specs`, `abandoned-specs`, `docs`, or `changelog.d`. The route folder `specs/numbered/0/0/1/2/2/3/1/4` is absent on `main` (RC-44, RC-45). This record creates both.

## 3. Decisions

Each decision applies to the issue scope. No decision needs a human decision under brief section 6, so the human count is zero.

**D-1 Base and reference.** Base the change on `main`. Use commits `63dd076` and `196af800` as reference evidence only.
- Alternatives: (a) Continue the owner archive branch. (b) Rebase the owner candidate onto `main`.
- Rationale: AGENTS.md requires a branch from `main` (RC-78). The candidate has no total or header check (RC-06). The archive branch is not `main` (RC-51 to RC-53).
- Risk: The owner may repeat the work. Mitigation: the handoff names the methods that this change can reuse (U-3).
- Human decision required: no.

**D-2 Handoff gate.** Make no edit to the exporter or its test before the #1794 owner posts a file-scoped handoff.
- Alternatives: (a) Edit now and resolve conflicts at merge. (b) Ask the owner to land the candidate first.
- Rationale: The issue body states: "Do not start a second source edit until that owner provides a file-scoped handoff" (RC-76).
- Risk: The work waits. Mitigation: the record stays complete, and task T001 checks the gate.
- Human decision required: no.

**D-3 Fail closed.** Any rejected page ends the read with no writer call and no partial file.
- Alternatives: (a) Write rows from the pages that passed, as the wifi exporter does for transport failures. (b) Write and warn.
- Rationale: The issue body says no complete export may follow a failed page (RC-76). A partial file looks complete to an operator.
- Risk: One bad page blocks the export. Mitigation: the operator reruns menu 258, as the plan caution states.
- Human decision required: no.

**D-4 Pagination method.** Request later pages with `mistapi.get_next`. Stop calling `mistapi.get_all`.
- Alternatives: (a) Keep `get_all` and check only the first response. This misses F-2. (b) Wrap the session to record each page. AGENTS.md forbids wrappers and adapters (RC-79). (c) Call `mist_get` with each `next` value. This repeats SDK URL logic.
- Rationale: `get_next` requests one page from the `next` value (RC-67). The wifi exporter uses it (RC-16). The constitution requires a mistapi method when one exists (RC-37).
- Risk: `get_next` returns `None` when `next` is absent. Mitigation: the loop checks `next` before it calls the helper.
- Human decision required: no.

**D-5 Completeness rules.** Accept a read only when every page passes, each `next` value is new, `total` equals the row count when present, and each `X-Page-*` header is an integer when present.
- Alternatives: (a) Use `next` only. This misses F-4. (b) Reject a read that has no `total`. The schema does not require `total` (RC-23, U-2), so this could reject valid exports. (c) Add a page cap now. A page cap is a follow-up candidate.
- Rationale: The schema defines `total` as the count across all pages (RC-23). The owner lists both missing cases (RC-61).
- Risk: Live pages without `total` depend on `next` alone (U-2).
- Human decision required: no.

**D-6 Request and window.** Keep the first request as `searchSiteOtherDeviceEvents(session, site_id)`. Keep the API default window.
- Alternatives: (a) Add `limit` 1000 to reduce pages. (b) Add `duration` to widen the window.
- Rationale: The existing test asserts this call (test file, line 70). The window is an operator question, not part of the defect (U-6). The SDK default is `1d` (RC-71).
- Risk: Operators may expect a wider window (U-6).
- Human decision required: no.

**D-7 Menu contract.** The menu operation returns to the loop after any failure. It never raises to the loop.
- Alternatives: (a) Re-raise to the menu. (b) End the program.
- Rationale: Spec 894 names a logged warning, not a traceback, for an unknown site (RC-25). The retained test `test_sdk_failure_is_logged_without_raising` expects no raise (test file, line 74).
- Risk: None new.
- Human decision required: no.

**D-8 Signal and names.** Raise `RuntimeError` with an operator-safe message for an incomplete read. Add no module-level name.
- Alternatives: (a) Add a module-level exception class. The change then adds a module-level name that `symbol-diff` reports. (b) Return `None` as a sentinel. It conflicts with a complete empty read.
- Rationale: The wifi exporter raises `RuntimeError` inside its page validation (RC-17). SC-005 requires no module-level change.
- Risk: A broad guard can hide a `RuntimeError` from another cause. Mitigation: each raise carries its own message, and the outer guard logs it.
- Human decision required: no.

**D-9 Outer guard.** Keep the outer `except Exception` guard and its root `logging` calls.
- Alternatives: (a) Narrow the guard now. (b) Remove the guard.
- Rationale: The #1794 audit owns the guard (RC-04). Removing it changes the menu behavior that D-7 keeps.
- Risk: The guard can hide a defect. Mitigation: the #1794 owner narrows it.
- Human decision required: no.

**D-10 Logging.** New lines use the module logger (line 20 of the exporter). Messages use `%s` formatting, ASCII text, and no body, cursor, or URL.
- Alternatives: (a) Use the root logger, as the outer guard does.
- Rationale: The module logger exists (RC-04). The constitution requires `%s` formatting (Principle VII, RC-39).
- Risk: The file holds two logging styles until the #1794 audit ends.
- Human decision required: no.

**D-11 Tests.** Extend `tests/unit/export/test_site_other_device_events_exporter.py`. Write the 16 test cases of plan.md before the fix.
- Alternatives: (a) Create a new test module. It repeats the fixtures. (b) Test with live calls. The brief forbids live calls.
- Rationale: The file already holds the fixtures and the patch targets. The quality rule needs 4xx and 5xx cases (RC-74, RC-09).
- Risk: The test quality ratchet flags a weak assertion. Mitigation: each test asserts a writer call or a log line.
- Human decision required: no.

**D-12 Labels.** Add `src` and `severity:high`. Keep `bug`, `tests`, and `in-progress`. Do not add `needs-human-review`.
- Alternatives: (a) Add `needs-human-review`, as issues #4707 and #4710 carry. (b) Add `export`, which exists without a description.
- Rationale: `src` names the source scope (RC-62). `severity:high` matches the issue description, which says the defect "can hide a real failure or report a false success" (RC-63). The change touches no destructive operation or firmware path, so the review label does not apply (RC-80).
- Risk: A reviewer disagrees. Mitigation: the orchestrator may add the review label.
- Human decision required: no.

**D-13 Authorization gates.** The push, the pull request, and the merge wait for orchestrator authorization. The pull request body uses `Closes #4709` and names the related issues with `Refs`.
- Alternatives: (a) Close the related issues through the pull request. (b) Merge without the gate.
- Rationale: The owner comment states that no pull request, merge, or issue closure is authorized (RC-75). The related issues stay open (RC-56 to RC-58).
- Risk: The work waits. Mitigation: T-PR records the gate.
- Human decision required: no. The gate follows the orchestrator process, not a section 6 category.

**D-14 Scope and follow-ups.** Keep the organization exporters, the mistapi pin text, and any page cap out of this change. Record A-11 and A-12 for follow-up issues.
- Alternatives: (a) Fix every item in one pull request. (b) Change the pin text in this pull request.
- Rationale: AGENTS.md states that one issue holds one subject (RC-77). FR-022 forbids organization edits here.
- Risk: The defects remain until the follow-up issues land. Mitigation: the orchestrator files the follow-up issues (U-5).
- Human decision required: no.

## 4. Remote Verification

Each row is one remote check. The STATUS file lists the same 80 checks in the same order. Result values are `present`, `absent`, `partial`, or `stale`. Line `0` means a presence check with no line claim.

| ID | Claim | Path or source | Ref | Blob SHA or object | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Exporter defines `other_device_events` | src/operations/exporting/export/site_other_device_events_exporter.py | main | 60f1ac7fdd966ef4cd7b38b4e3f6cd314d1fbf3a | present | 56 |
| RC-02 | Exporter passes first response to `mistapi.get_all` with no status check | src/operations/exporting/export/site_other_device_events_exporter.py | main | 60f1ac7fdd966ef4cd7b38b4e3f6cd314d1fbf3a | present | 76 |
| RC-03 | Exporter prints the no-data message for an empty row list | src/operations/exporting/export/site_other_device_events_exporter.py | main | 60f1ac7fdd966ef4cd7b38b4e3f6cd314d1fbf3a | present | 30 |
| RC-04 | Exporter outer guard catches every exception | src/operations/exporting/export/site_other_device_events_exporter.py | main | 60f1ac7fdd966ef4cd7b38b4e3f6cd314d1fbf3a | present | 83 |
| RC-05 | Owner candidate exporter exists on GitHub commit 196af800 | src/operations/exporting/export/site_other_device_events_exporter.py | 196af800b88ffaf2cd8158bf09da1975d42bb69d | a0d22bada5623eec276253f3392ad2ee9a03b23f | present | 56 |
| RC-06 | Owner candidate has no total or X-Page-* metadata check | src/operations/exporting/export/site_other_device_events_exporter.py | 196af800b88ffaf2cd8158bf09da1975d42bb69d | a0d22bada5623eec276253f3392ad2ee9a03b23f | absent | 0 |
| RC-07 | Test module exists on main | tests/unit/export/test_site_other_device_events_exporter.py | main | b57852a8a8a0d81945cef5bf16b91c0d3c3aca6e | present | 0 |
| RC-08 | Existing menu test patches `mistapi.get_all` | tests/unit/export/test_site_other_device_events_exporter.py | main | b57852a8a8a0d81945cef5bf16b91c0d3c3aca6e | present | 66 |
| RC-09 | Test module has no HTTP 4xx or 5xx case | tests/unit/export/test_site_other_device_events_exporter.py | main | b57852a8a8a0d81945cef5bf16b91c0d3c3aca6e | absent | 0 |
| RC-10 | Menu 258 registers the exporter handler | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4998 |
| RC-11 | Web portal lists menu 258 as a site-only operation | web_portal/services/operation.py | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 452 |
| RC-12 | Endpoint key strategy uses composite key mac and timestamp | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 529 |
| RC-13 | Writer entry point exists | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 153 |
| RC-14 | Site resolver exists | src/operations/exporting/export/site_device_exporter.py | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 130 |
| RC-15 | Shared HTTP failure helper reports no failure for a non-integer status | src/operations/exporting/export/http_response_status.py | main | 7d511edd6de3a909093e685deed1a9d0b3b7e648 | present | 17 |
| RC-16 | Wifi exporter requests later pages with `get_next` | src/operations/exporting/export/wifi_clients_exporter.py | main | 10cb50b7745731a1be9bb9127561721c29938d73 | present | 205 |
| RC-17 | Wifi exporter validates each page before accepting its rows | src/operations/exporting/export/wifi_clients_exporter.py | main | 10cb50b7745731a1be9bb9127561721c29938d73 | present | 250 |
| RC-18 | Wifi exporter uses the shared integrity checker | src/operations/exporting/export/wifi_clients_exporter.py | main | 10cb50b7745731a1be9bb9127561721c29938d73 | present | 266 |
| RC-19 | Shared integrity checker class exists | src/mist/access/api/response_integrity.py | main | 4a1f25ce501771f2ddf2d6ceaa171ca25b49e4b0 | present | 31 |
| RC-20 | Wifi failure test module is the test pattern | tests/unit/export/test_wifi_clients_response_failures.py | main | 9a9e9b13a41a1df0176da1bee4e4239a6b927d7b | present | 51 |
| RC-21 | Organization audit logs check the first response only, then call `get_all` | src/operations/exporting/export/org_export_utils.py | main | cfe85d09447ec3be6271f2a4cb8e5ea2dac5fb81 | present | 775 |
| RC-22 | OpenAPI defines the site search operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 35577 |
| RC-23 | OpenAPI search page schema defines `total` | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94511 |
| RC-24 | OpenAPI search page schema defines `next` | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94500 |
| RC-25 | Spec 894 says an unknown site returns a logged warning | specs/894-mist-search-site-other-device-events/spec.md | main | 39cb2157edf01c7db73f28ca6f6eba580078dfd9 | present | 65 |
| RC-26 | CI MYPY_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-27 | CI VULTURE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-28 | CI PYDOCSTYLE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-29 | CI INTERROGATE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-30 | CI pylint gate uses SRC_PATH | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 529 |
| RC-31 | pyproject pins mistapi at least 0.64.1 and below 0.65 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RC-32 | pyproject requires Python 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| RC-33 | requirements pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-34 | copilot-instructions states mistapi at least 0.64.0 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| RC-35 | copilot-instructions local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-36 | AGENTS writing style rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-37 | Constitution forbids direct HTTP when a mistapi method exists | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 280 |
| RC-38 | Constitution Principle VI requires inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RC-39 | Constitution Principle VII requires action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC-40 | Spec template has a Mist Cloud transport section | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 102 |
| RC-41 | Changelog rule names the issue fragment form | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-42 | Quality gate table row for test quality | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 63 |
| RC-43 | Container revision check section | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 268 |
| RC-44 | Route folder for issue 4709 is absent | specs/numbered/0/0/1/2/2/3/1/4 | main | not a blob: no object | absent | 0 |
| RC-45 | Legacy record folder for issue 4709 is absent | specs (any path with a 4709- folder) | main | not a blob: no object | absent | 0 |
| RC-46 | Reference record spec exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-47 | Reference record contract exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/contracts/cli-menu.md | main | e91b5f8642c06f1eb54d6b68ccc751b928d77798 | present | 0 |
| RC-48 | SDK compatibility test exists | tests/integration/test_mistapi_sdk_compatibility.py | main | cab2d602113012729f6c392dff43197d05913a38 | present | 0 |
| RC-49 | Test quality preflight test exists | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 0 |
| RC-50 | Issue baseline commit 3964d21 exists | commits/3964d21d03f9f5717cb8eafb7272ecff21f5362a | GitHub API | not a blob: commit 3964d21d03f9f5717cb8eafb7272ecff21f5362a | present | 0 |
| RC-51 | Owner commit 63dd076 is an ancestor of the archive head | compare 63dd076 with the archive head | GitHub API | not a blob: commit 3da1f066c2df5d86a00ea857cf566c9135bdc693 | present | 0 |
| RC-52 | Owner candidate 196af800 is an ancestor of the archive head | compare 196af800 with the archive head | GitHub API | not a blob: commit 3da1f066c2df5d86a00ea857cf566c9135bdc693 | present | 0 |
| RC-53 | Archive branch head commit | heads/archive/laptop-20261121/jmorrison-juniper-other-device-event-audit | GitHub API | not a blob: commit 3da1f066c2df5d86a00ea857cf566c9135bdc693 | present | 0 |
| RC-54 | Main head commit | heads/main | GitHub API | not a blob: commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-55 | No open pull request changes the owned files | open pull requests (7 listed) | GitHub API | not a blob: none | absent | 0 |
| RC-56 | Issue 1794 is open | issue 1794 | GitHub API | not a blob: issue | present | 0 |
| RC-57 | Issue 4707 is open | issue 4707 | GitHub API | not a blob: issue | present | 0 |
| RC-58 | Issue 4710 is open | issue 4710 | GitHub API | not a blob: issue | present | 0 |
| RC-59 | Issue 4709 is open with labels bug, tests, and in-progress | issue 4709 | GitHub API | not a blob: issue | present | 0 |
| RC-60 | Owner comment says the candidate is unpublished | issue 4709 comment IC_kwDOQltU8c8AAAABkfIV2g | GitHub API | not a blob: comment | stale | 0 |
| RC-61 | Owner comment lists two pagination metadata cases | issue 4709 comment IC_kwDOQltU8c8AAAABkfIV2g | GitHub API | not a blob: comment | present | 0 |
| RC-62 | Label src exists | label src | GitHub API | not a blob: label | present | 0 |
| RC-63 | Label severity:high exists | label severity:high | GitHub API | not a blob: label | present | 0 |
| RC-64 | Local SDK distribution is mistapi 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local .venv | not a blob: local directory | present | 0 |
| RC-65 | SDK get_all adds a later list page without a status check | .venv\Lib\site-packages\mistapi\__pagination.py | local .venv | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 62 |
| RC-66 | SDK get_all reads results of a later dict page with no guard | .venv\Lib\site-packages\mistapi\__pagination.py | local .venv | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 71 |
| RC-67 | SDK get_next sends the next value through mist_get | .venv\Lib\site-packages\mistapi\__pagination.py | local .venv | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 34 |
| RC-68 | SDK response defaults to empty data and no next value | .venv\Lib\site-packages\mistapi\__api_response.py | local .venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 39 |
| RC-69 | SDK reads X-Page-Total for header pagination | .venv\Lib\site-packages\mistapi\__api_response.py | local .venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 76 |
| RC-70 | SDK search function sends a GET to the site search path | .venv\Lib\site-packages\mistapi\api\v1\sites\otherdevices.py | local .venv | 6e71befb7392a24fef1291f4faae9a72d01be165 | present | 221 |
| RC-71 | SDK search default duration is 1d | .venv\Lib\site-packages\mistapi\api\v1\sites\otherdevices.py | local .venv | 6e71befb7392a24fef1291f4faae9a72d01be165 | present | 115 |
| RC-72 | SDK request layer returns an APIResponse after a connection failure | .venv\Lib\site-packages\mistapi\__api_request.py | local .venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 258 |
| RC-73 | SDK exports get_all and get_next publicly | .venv\Lib\site-packages\mistapi\__init__.py | local .venv | f6fca30f4088d763e76f3072d02a3095d46852b9 | present | 15 |
| RC-74 | Copilot instructions require HTTP 4xx and 5xx tests for an API client test module | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 253 |
| RC-75 | Owner comment states that no pull request, merge, or issue closure is authorized | issue 4709 comment IC_kwDOQltU8c8AAAABkfhU5w | GitHub API | not a blob: comment | present | 0 |
| RC-76 | Issue body requires a handoff before edits and no complete export after a failed page | issue 4709 body | GitHub API | not a blob: issue body | present | 0 |
| RC-77 | AGENTS rule: one issue holds one subject | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 185 |
| RC-78 | AGENTS rule: branch from main only | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 197 |
| RC-79 | AGENTS rule: no wrapper, adapter, or shim during a refactor | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 87 |
| RC-80 | Label needs-human-review means a human must review a destructive or safety change | label needs-human-review | GitHub API | not a blob: label | present | 0 |

Row count: 80. Result count: 74 present, 5 absent (RC-06, RC-09, RC-44, RC-45, RC-55), and 1 stale (RC-60).

## 5. Sources

Local line ranges come from files whose checkout blob equals the remote blob (method note 5).

- `AGENTS.md`: line 40 (writing style), 87 to 88 (no wrapper or adapter), 157 (safety), 172 (secrets), 185 (one subject per issue), 197 (branch from main), 345 (specifications).
- `.github/copilot-instructions.md`: lines 8 (repository scope), 21 (language and mistapi pin), 50 (local gates), 159 (Spec Kit records), 253 (test quality), 431 (git and GitHub).
- `.specify/memory/constitution.md`: lines 204 (Principle VI), 235 (Principle VII), 274 to 280 (technology constraints).
- `.specify/templates/spec-template.md`: line 102 (transport section). The plan, tasks, and checklist templates were read and followed.
- `documentation/quality-gates.md`: lines 8, 23, and 63.
- `documentation/container-deployment.md`: lines 222 and 268.
- `changelog.d/README.md`: line 27 (file names) and lines 53 to 65 (five rules).
- `documentation/operator-guide.md`, `README.md`, and `documentation/*.md`: a search for the no-data and failure messages found no match. The operator guide has no text for menu 258.
- `specs/894-mist-search-site-other-device-events/spec.md`: lines 64 and 65.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`: shape reference only. Content was not copied.
- `.venv\Lib\site-packages\mistapi\__init__.py`: lines 15 and 16.
- `.venv\Lib\site-packages\mistapi\__pagination.py`: lines 17, 34, 39, 56 to 74.
- `.venv\Lib\site-packages\mistapi\__api_response.py`: lines 22, 27, 39, 41, 43, 55 to 58, 70 to 80.
- `.venv\Lib\site-packages\mistapi\__api_request.py`: lines 225, 228, 250, 258, and 260 (`mist_get`).
- `.venv\Lib\site-packages\mistapi\api\v1\sites\otherdevices.py`: lines 115, 144, 186, 199, and 221 to 222.
- `documentation/mist-api-openapi31yaml.yaml`: line 35577 (path), 59742 to 59747 (limit default 100), 60227 (`search_after`), 62357 to 62364 (response), and 94488 to 94520 (schema).
- `src/mist/access/api/response_integrity.py`: lines 31 to 61.
- `src/operations/exporting/export/http_response_status.py`: lines 14 to 19.
- `src/operations/exporting/export/site_other_device_events_exporter.py`: lines 20 (logger), 27 to 53 (`_persist_events`), 56 to 89 (`other_device_events`).
- `tests/unit/export/test_site_other_device_events_exporter.py`: lines 21, 28, 38, 52, 66, 70, 71, and 74.
- `tests/unit/export/test_wifi_clients_response_failures.py`: lines 12, 51, and 78.
- `src/operations/exporting/export/wifi_clients_exporter.py`: lines 12 to 13, 190, 205, 250, and 266.
- `src/operations/exporting/export/org_export_utils.py`: lines 766 to 775.
- `MistHelper.py`: lines 692 to 694 (import) and 4996 to 5002 (menu entry).
- `web_portal/services/operation.py`: lines 440 to 461 (list), and 452 (menu 258).
- `src/foundation/support/refactors/endpoint_primary_key_strategies.py`: lines 527 to 532.
- `src/operations/exporting/export/data_exporter.py`: line 153.
- `src/operations/exporting/export/site_device_exporter.py`: line 130.
- `.github/workflows/ci.yml`: lines 78, 93, 101, 104, 107, 122, 123, 127, and 529.
- `pyproject.toml`: lines 23 and 29. `requirements.txt`: line 129.
- URLs: none. No web page was fetched.

## 6. Unverified

- **U-1 Handoff.** The #1794 owner has not posted the handoff. Reason: the process step is outside this record. T001 checks it.
- **U-2 Live `total`.** Live search pages may omit `total`. Reason: the issue and the brief forbid live calls, and the schema does not require `total` (RC-23).
- **U-3 Owner correction.** The owner comment that mentions a later local correction names no commit. Reason: no commit on GitHub matches it (comment IC_kwDOQltU8c8AAAABkfhU5w).
- **U-4 Transport exceptions.** Exceptions that escape the request layer are not verified. Reason: RC-72 covers the returned path only. Test 5 and the outer guard cover the rest.
- **U-5 Follow-up issues.** The follow-up issues for A-11 and A-12 are not filed. Reason: this record makes no GitHub write.
- **U-6 Default window.** Operators may expect a window longer than the API default. Reason: a product question outside this issue (RC-71).
- **U-7 Mistapi upstream.** No upstream report exists for the SDK defects. Reason: no upstream URL was fetched, and this record makes no web read.

## 7. Skills

No skill was loaded. The issue does not concern Podman behavior or Juniper device behavior. The container and Juniper skills therefore do not apply.

## 8. Decision Index

| ID | Decision | Human decision required |
| - | - | - |
| D-1 | Base on `main`. Use owner commits as reference only. | no |
| D-2 | Gate edits on the #1794 handoff. | no |
| D-3 | Fail closed on any incomplete read. | no |
| D-4 | Use `mistapi.get_next`. Stop using `mistapi.get_all`. | no |
| D-5 | Apply the completeness rules. | no |
| D-6 | Keep the request and the API default window. | no |
| D-7 | Return to the loop after any failure. | no |
| D-8 | Raise `RuntimeError`. Add no module-level name. | no |
| D-9 | Keep the outer guard. | no |
| D-10 | Use the module logger with ASCII text and no secrets. | no |
| D-11 | Extend the existing test module with the 16 test cases, written first. | no |
| D-12 | Add `src` and `severity:high`. Keep `bug`, `tests`, and `in-progress`. | no |
| D-13 | Gate the push, the pull request, and the merge. | no |
| D-14 | Keep organization exporters and pin text out of scope. | no |
