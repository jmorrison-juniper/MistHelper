# Research: Menu 304 serial number browser test (issue #4603)

This file holds the evidence, the root-cause candidates, the decisions, and the remote verification table for issue #4603. Each remote claim cites the blob SHA on `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Each local claim cites a path and a line range.

## R1. Issue facts

- Title: `Test failure: menu 304 serial number browser test`. State: OPEN.
- Created 2026-11-06T06:44:42Z. Last update 2026-11-10T08:02:09Z. Author: `jmorrison-juniper`.
- Labels: `bug`, `needs-investigation`, `tests`, `web-portal`.
- The body names the failing test, the assertion, CI run 42173674615, and PR #4601. The body states that no repair was attempted.
- Four owner comments report local probes. The probes did not reproduce the failure. Comment IDs: IC_kwDOQltU8c8AAAABjiFSGA, IC_kwDOQltU8c8AAAABjivr-A, IC_kwDOQltU8c8AAAABkivnLw, IC_kwDOQltU8c8AAAABkw8gIA.

## R2. CI reproduction (read-only)

Read-only commands used: `gh issue view 4603`, `gh run view 42173674615 --log-failed`, and `gh run view 42173674615 --job 127747809271 --log`. No write command ran.

- Failing test: `tests/e2e/web_portal/test_juniper_menus_browser.py::TestTheJuniperMenusAreReadableInTheBrowser::test_menu_304_waits_for_serial_numbers_then_saves_each_asset[chromium]`.
- Failing assertion: line 323 of the test module, `expect(page.locator("#param-serial_numbers")).to_be_visible()`.
- Error text from the log:
  - `AssertionError: Locator expected to be visible`
  - `Actual value: None`
  - `Error: element(s) not found`
  - `Expect "to_be_visible" locator("#param-serial_numbers") with timeout 5000ms`
- Failing job: `E2E shard (web-portal)`, job ID 127747809271, step `Run E2E smoke tests`.
- Run summary: `1 failed, 452 passed, 2 warnings in 755.05s`. The test line shows FAILED at 2026-11-06T06:28:22Z.

## R3. Browser state and request log at failure

The aria snapshot in the log shows these facts:

- The Operations heading and its default text appear. No operation is selected.
- The group `Juniper RMA ( 11 )` is expanded.
- Rows 294 to 304 are listed. Row 304 reads `Look up Juniper warranty, contract, and status data for serial numbers (read-only)`.

The server log captured during the test shows these requests, all with status 200:

- `GET /operations` at 06:28:15.
- `GET /api/operations/list` at 06:28:15.
- `GET /api/operations/active` at 06:28:15 and at 06:28:20.

The server log shows no `GET /api/operations/parameters/304`.

Inference, not confirmed. The click on row 304 did not start `selectOperation`:

1. `selectOperation` calls `loadParameters` (`web_portal/static/js/operations.js`, line 192).
2. `loadParameters` shows `#parameterLoading` (line 278) and sends the parameter request (line 282) in one synchronous path.
3. The failure reached line 323 of the test, so the wait at line 186 returned.
4. That wait returns at once while `#parameterLoading` stays hidden.

## R4. Linked pull requests and overlap

| PR | State | Head branch | Files that matter | Role for #4603 |
| - | - | - | - | - |
| #4601 | MERGED 2026-11-06T08:30:05Z | `chore/3400-dependency-bounds` | `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `uv.lock` | Head `1b8c06a8a0d15abbbe1ae8edb840dd0dd81e1bb6` ran the failing job. Head `4b8948ca4f08de1888ca6ccdf05b734c407de367` passed the web-portal E2E job. |
| #4358 | MERGED 2026-11-13T19:33:49Z | `jmorrison-juniper-4142-test-package-deconfliction` | `tests/e2e/web_portal/test_juniper_menus_browser.py` (commit `2a6a58446`, one import line changed) and `tests/e2e/web_portal/juniper_browser_harness.py` | The issue says PR #4358 owns the browser test and `pyproject.toml`. The file list confirms the browser test. It does not list `pyproject.toml`. |

Overlap check: seven PRs were open on 2026-11-26. PR #4888 (`dependabot/pip/mando-0.8.2`) changes `requirements-dev.txt`. PR #4208 (`jmorrison-juniper-4200-migrate-mistwanperformance`) changes two other modules in `tests/e2e/web_portal/`. No open PR changes the browser test, `operations.js`, `operations.html`, `pyproject.toml`, or `ci.yml`.

Related issues: #3519 (cited by the browser test docstring, closed). #4139 (feature issue for menus 294 to 304, closed). #3400 (dependency lock work, open) is linked from PR #4601. #4142 (test package split, open) is referenced by PR #4358. A title search for `menu 304` found no other issue about this failure.

## R5. Legacy record check

- Brief section 3, step 3: no folder under `specs\` starts with `4603-`. The search covered the full `specs` tree.
- The draft folder held no files before this run.
- `existing_record.found` is false. No record reuse happens, so step 4 has no record to verify.

## R6. Remote verification table

Each row is one check on `main`, except RV-67, which checks the local SDK file. The result uses one of present, absent, partial, or stale. The line is the line on `main`, or 0 for a file or folder check. The row count of this table equals `remote_checks` in the STATUS file.

| No. | Claim | Path | Blob SHA | Result | Line |
| - | - | - | - | - | - |
| RV-01 | Failing test is defined in the browser module | tests/e2e/web_portal/test_juniper_menus_browser.py | 3b17a8bd4fde4c41c851c6048ffd149f725a5b5b | present | 314 |
| RV-02 | Failing assertion checks the serial number control | tests/e2e/web_portal/test_juniper_menus_browser.py | 3b17a8bd4fde4c41c851c6048ffd149f725a5b5b | present | 323 |
| RV-03 | Helper waits on the loading predicate after the click | tests/e2e/web_portal/test_juniper_menus_browser.py | 3b17a8bd4fde4c41c851c6048ffd149f725a5b5b | present | 186 |
| RV-04 | Loading predicate is true when the element is absent or hidden | tests/e2e/web_portal/test_juniper_menus_browser.py | 3b17a8bd4fde4c41c851c6048ffd149f725a5b5b | present | 52 |
| RV-05 | Helper uses a fixed 500 ms sleep after the wait | tests/e2e/web_portal/test_juniper_menus_browser.py | 3b17a8bd4fde4c41c851c6048ffd149f725a5b5b | present | 187 |
| RV-06 | Harness maps menu 304 to AssetLookupWorkflow.run | tests/e2e/web_portal/juniper_browser_harness.py | f19760859f534522b2d6168558705fdb0d0a1a79 | present | 79 |
| RV-07 | E2E items skip when pytest-timeout is missing | tests/e2e/conftest.py | e450e1855770d2e0ec587935a95233262b118ae1 | present | 209 |
| RV-08 | selectOperation is defined | web_portal/static/js/operations.js | e92f687f958dcd108f1c0db30fa86511ec68b827 | present | 167 |
| RV-09 | Each row carries an inline click handler that calls selectOperation | web_portal/static/js/operations.js | e92f687f958dcd108f1c0db30fa86511ec68b827 | present | 146 |
| RV-10 | selectOperation calls loadParameters | web_portal/static/js/operations.js | e92f687f958dcd108f1c0db30fa86511ec68b827 | present | 192 |
| RV-11 | loadParameters shows the loading indicator before the fetch | web_portal/static/js/operations.js | e92f687f958dcd108f1c0db30fa86511ec68b827 | present | 278 |
| RV-12 | loadParameters fetches the parameter path | web_portal/static/js/operations.js | e92f687f958dcd108f1c0db30fa86511ec68b827 | present | 282 |
| RV-13 | showSelectedPanel writes the selected title without a guard | web_portal/static/js/operations.js | e92f687f958dcd108f1c0db30fa86511ec68b827 | present | 250 |
| RV-14 | The active-operations poll runs every 5000 ms | web_portal/static/js/operations.js | e92f687f958dcd108f1c0db30fa86511ec68b827 | present | 1410 |
| RV-15 | Template holds the parameter loading indicator | web_portal/templates/operations.html | 78589d74b9e4c253da5a2da759d5c798ad9ec106 | present | 58 |
| RV-16 | Template holds the selected title element | web_portal/templates/operations.html | 78589d74b9e4c253da5a2da759d5c798ad9ec106 | present | 41 |
| RV-17 | Parameter route is defined | web_portal/routes/operations.py | c7ef542129a0764a55ba18f2a1c9a2d6c5573754 | present | 256 |
| RV-18 | Menu 304 parameter row is defined | web_portal/services/operation.py | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 400 |
| RV-19 | Menu 304 serial_numbers parameter is a required text control | web_portal/services/operation.py | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 401 |
| RV-20 | Menu 304 category is interactive_safe | src/foundation/support/utils/operation_registry.py | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 520 |
| RV-21 | Menu 304 handler writes JuniperAssets.csv | src/operations/exporting/juniper_rma/workflows/asset_lookup.py | d4e34076440a8709c409c95a1fed81cbc0091e8a | present | 106 |
| RV-22 | Menu 304 handler class is AssetLookupWorkflow | src/operations/exporting/juniper_rma/workflows/asset_lookup.py | d4e34076440a8709c409c95a1fed81cbc0091e8a | present | 34 |
| RV-23 | Menu 304 handler imports no mistapi module | src/operations/exporting/juniper_rma/workflows/asset_lookup.py | d4e34076440a8709c409c95a1fed81cbc0091e8a | absent | 0 |
| RV-24 | Menu documentation lists menu 304 | documentation/menu-operations-294-304.md | 3743e88f98872025cd02f26860e211a0ff7812af | present | 77 |
| RV-25 | Menu documentation says the operations read Juniper service APIs | documentation/menu-operations-294-304.md | 3743e88f98872025cd02f26860e211a0ff7812af | present | 3 |
| RV-26 | Python floor is 3.15 | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| RV-27 | mistapi pin is at least 0.64.1 | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RV-28 | Copilot instructions state mistapi at least 0.64.0 | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| RV-29 | requirements.txt pins dash 4.5.1 | requirements.txt | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 45 |
| RV-30 | requirements-dev.txt pins dash 4.5.1 | requirements-dev.txt | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 76 |
| RV-31 | requirements-dev.txt pins playwright 1.65.2 | requirements-dev.txt | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 272 |
| RV-32 | pyproject.toml pins pytest-playwright 0.10.0 | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 114 |
| RV-33 | CI default Python is 3.15 | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 77 |
| RV-34 | E2E job sets up PYTHON_VERSION | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 836 |
| RV-35 | E2E job installs requirements-dev.txt | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 841 |
| RV-36 | Web-portal shard runs tests/e2e/web_portal | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 796 |
| RV-37 | E2E smoke step runs pytest with a 180 second timeout | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 909 |
| RV-38 | E2E job installs Chromium | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 887 |
| RV-39 | E2E job uploads shard diagnostics | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 942 |
| RV-40 | Gate row Compile | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| RV-41 | Gate row Lint | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 58 |
| RV-42 | Gate row Format | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 59 |
| RV-43 | Gate row Tests | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RV-44 | Gate row Full tests | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 62 |
| RV-45 | Gate row Test quality with the ratchet procedure below it | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 65 |
| RV-46 | Gate row Symbols | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| RV-47 | Types gate scope excludes the tests folder | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RV-48 | Changelog rule 4 excludes internal-only changes from fragments | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RV-49 | Changelog guard file exists | tests/guardrails/test_changelog_fragment_policy.py | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RV-50 | E2E shard partition guard file exists | tests/guardrails/test_e2e_shard_partition.py | 8d9f45db72e88e5a48d3f2e561e3e2cba9e89fd3 | present | 1 |
| RV-51 | Precedent test defers a parameter response with a window flag | tests/e2e/web_portal/test_web_interactivity_quickstart.py | 416d82de5d18f0aa62741ae8a4236f2653f7fa06 | present | 54 |
| RV-52 | Spec route base is 5 | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RV-53 | Numbered route folder for issue 4603 is absent on main | specs/numbered/0/0/1/2/1/4/0/3 | not applicable: folder absent | absent | 0 |
| RV-54 | Reference record spec.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RV-55 | Reference record plan.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 0 |
| RV-56 | Reference record tasks.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 0 |
| RV-57 | Reference record analysis.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/analysis.md | b5db89b9d0d0a4f8e725ad8e0e746c34fa1a24e7 | present | 0 |
| RV-58 | Reference record design research.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| RV-59 | Reference record requirements checklist exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/checklists/requirements.md | 4a53b89939bb523902efeaaffd1d7b12221c717b | present | 0 |
| RV-60 | Constitution Principle VI requires inline comments | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RV-61 | Constitution Principle VII requires action logging | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RV-62 | AGENTS.md holds the writing style section | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RV-63 | Spec Kit spec template exists | .specify/templates/spec-template.md | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RV-64 | Spec Kit plan template exists | .specify/templates/plan-template.md | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RV-65 | Spec Kit tasks template exists | .specify/templates/tasks-template.md | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RV-66 | Spec Kit checklist template exists | .specify/templates/checklist-template.md | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RV-67 | Installed mistapi version is 0.64.1 (local SDK source, not a repository path) | .venv\Lib\site-packages\mistapi\__version.py | not applicable: local file | present | 1 |

Count of rows in this table: 67. The local checkout matched every remote blob SHA above (`git hash-object`, no write). Remote evidence came from `gh api` calls on `main`.

## R7. Environment of each CI run

| Run | Head | Web-portal E2E job | Python | Dash | pytest-playwright plugin | Collected items |
| - | - | - | - | - | - | - |
| 42173674615 | `1b8c06a8a0d15abbbe1ae8edb840dd0dd81e1bb6` (PR #4601) | failure | 3.13.18 | 4.5.0 | playwright-0.10.0 | 453 |
| 42181849465 | `4b8948ca4f08de1888ca6ccdf05b734c407de367` (PR #4601) | success | 3.13.18 | 4.4.1 | playwright-0.10.0 | 453 |
| 42185517703 | short SHA `1efec2b8` (PR #4601 branch) | success | not checked | not checked | not checked | not checked |
| 42180496231 | short SHA `61de117c` (PR #4601 branch) | conclusion `cancelled` | not checked | not checked | not checked | not checked |
| 45774119357 | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (main) | success | 3.15.2 | 4.5.1 | playwright-0.10.0 | 456 |

Facts behind the table:

- The failing head pinned `dash>=4.4.1,<5` in `requirements.txt`. The passing head pins `dash==4.4.1`. The compare API between the two heads shows both lines.
- The failing head carried the comment `# Requires Python 3.13 or newer` in `requirements.txt`. The passing head removed it.
- The `PYTHON_VERSION` default changed from `'3.13'` to `'3.15'` in commit `8dd9998f1` on 2026-11-10. Read-only `git show` shows the change.
- The browser test file has blob `328b25be90cffbc2e308819cd113c5cdb0fd5f84` at both PR heads. Main has blob `3b17a8bd4fde4c41c851c6048ffd149f725a5b5b`. Commit `2a6a58446` changed one import line only.
- On the PR #4601 branch, the completed web-portal E2E results were one failure and two successes. On main, the 15 newest Quality Gates runs (2026-11-24 to 2026-11-26) all show success for the web-portal E2E job.

## R8. Root-cause candidates (none confirmed)

| Candidate | Evidence for | Evidence against | Status | Test in this plan |
| - | - | - | - | - |
| H1. The click did not reach the row handler. | No parameter request. The title stayed empty. | Playwright reported a completed click. | Unconfirmed. | T003 names the title and request state. |
| H2. selectOperation threw before loadParameters. | An unguarded write exists at `operations.js` line 250. | The same path works for menus 294 to 303 in the same run. | Unconfirmed. | T003 captures page errors. |
| H3. Dash 4.5.0 changes the browser or the test session. | Only the failing run had Dash 4.5.0 among the three runs read. | The owner probes passed 24 of 24 with Dash 4.5.0. Fifteen recent main runs passed with Dash 4.5.1. | Unconfirmed. | T006 runs combination A. |
| H4. A race between the accordion transition and the click. | None found in this record. | The owner probes passed 24 of 24 with transitions of 0, 1.5, and 3 seconds (issue comments). | Weakened. | T006 records timing failures. |
| H5. Python 3.13.18 causes the failure. | None found in this record. | Run 42181849465 passed on Python 3.13.18. | Weakened. | T006 runs combination B. |

## R9. Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. No decision needs a human.

**D-1. Diagnose before repair.**
- Alternatives: (a) change `operations.js` now. (b) Skip or mark the test as an expected failure. (c) Lengthen the timeouts.
- Chosen: test-only diagnostic changes and a repeat matrix. Production code stays unchanged unless decision D-7 starts.
- Reason: The log shows no parameter request. No cause is proven. Options (a) to (c) guess a cause or hide the defect.
- Risk: The cause stays open. Mitigation: stop rules in T006 and T007.

**D-2. Wait on the parameter response and the selected title.**
- Alternatives: keep the loading-indicator wait. Use a fixed sleep. Wait on the title only.
- Chosen: register `page.expect_response` for the parameter path before the click. Require HTTP 200. Then wait until the title text appears. Then keep the loading check after the response.
- Reason: The loading check passes before a request starts. A fixed sleep depends on timing. A title check alone does not prove the request.
- Risk: A missing response now fails after 15 seconds. This delay is intended.

**D-3. Put page and console errors into the failure message.**
- Alternatives: rely on the CI trace artifact. Enable verbose Playwright logs.
- Chosen: capture `pageerror` and `console` events inside the helper. Attach up to five entries to the failure message.
- Reason: The artifact `e2e-diagnostics-web-portal` returned HTTP 403 for the owner. The message must be readable in the log.
- Risk: Low. Extra text appears only when a wait fails.

**D-4. Keep the current dependency pins on main.**
- Alternatives: pin Dash 4.4.1, as in the passing run. Return to a version range.
- Chosen: no change to `pyproject.toml`, `requirements.txt`, or `requirements-dev.txt`.
- Reason: No proven link ties Dash 4.4.1 to the pass. The range let Dash 4.5.0 install in the failing run. PR #4888 changes `requirements-dev.txt`.
- Risk: A later Dash release can change behavior. Mitigation: the matrix in T006 and the E2E run for each dependency update.

**D-5. Add a changelog fragment for this change.**
- Alternatives: add no fragment, because `changelog.d/README.md` line 58 excludes internal-only changes.
- Chosen: add `changelog.d/issue-4603-menu-304-serial-browser-test.md`.
- Reason: The constitution requires one fragment for each change. The constitution supersedes other practice documents in its governance section.
- Risk: Low. The release coordinator reviews one more fragment.

**D-6. Keep module-level names unchanged in the test module.**
- Alternatives: add a module-level constant or a module-level helper function.
- Chosen: all changes stay inside `select_menu`, inside the menu 304 test, and inside one new method of the existing test class.
- Reason: The Symbols gate requires `no module-level name changed` (`.github/copilot-instructions.md` line 73).
- Risk: `select_menu` can exceed 25 lines. Mitigation: use a nested function and count the lines before the push.

**D-7. Trigger for a production repair.**
- Alternatives: no production path. Always repair `operations.js`.
- Chosen: start task T007 only when combination A fails and the message shows no parameter request or a page error.
- Reason: Production changes must follow evidence. The trigger keeps the repair tied to a measured failure.
- Risk: A repair can hide a test defect. Mitigation: TC-1 and TC-2 stay in the change.

**D-8. Use local repeats as the main stability evidence.**
- Alternatives: three green CI runs on the pull request head. One green CI run only.
- Chosen: one green web-portal E2E job on the pull request head. One green web-portal E2E job on the first main run after merge. Twenty local runs under combination D.
- Reason: The AGENTS rules discourage repeat CI runs. The failure occurred once in three completed branch runs. Local repeats cover intermittent behavior at lower cost.
- Risk: A rare failure can pass both CI runs. Mitigation: the 20 local runs and the stop rules in T006.

**D-9. Use an HTTP 503 response for the negative test.**
- Alternatives: abort the request, which waits until the timeout ends. Use no route, which uses the real server.
- Chosen: `page.route` fulfills the parameter path with status 503.
- Reason: The response arrives at once, so the test runs fast. The status appears in the message, as FR-004 requires.
- Risk: The no-response branch of the helper has no automated test in this change. Review covers it.

## R10. Mist API, SDK, and skills

- Mist API: not applicable. Menu 304 reads Juniper service APIs only. Evidence: RV-25 and RV-23. The handler module imports no mistapi module.
- Mist OpenAPI file (`documentation/mist-api-openapi31yaml.yaml`): not read. No Mist endpoint lies on the failure path.
- SDK: the installed `mistapi` version is 0.64.1 (RV-67). No mistapi function is in scope for this change.
- Skills: no local skill loaded. The issue has no Podman question and no Juniper device behavior question.
- Documentation read: `documentation/quality-gates.md` (E2E gate row, line 68) and `documentation/development-setup.md` (E2E section, lines 264 to 281). The development setup citation is local only, so it is not remote evidence.
- Not applicable to this failure: `documentation/architecture.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md`.

## R11. Local-only evidence

These facts come from the local checkout only. They support the plan but do not prove code on `main`.

- Local `.venv` package folders: `mistapi-0.64.1.dist-info`, `dash-4.5.1.dist-info`, `playwright-1.65.2.dist-info`, and `pytest_playwright-0.10.0.dist-info`.
- The browser module holds 18 test functions.
- `tests\e2e\web_portal` holds 33 direct children. `tests\e2e` holds 6 direct children. Both counts exceed five. Section Complexity Tracking in `plan.md` records them as existing debt.
- The local `changelog.d` folder holds 335 Markdown files.
- Local HEAD equals `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, the head of the newest main run.

## R12. Sources

- Issue #4603 body and comments: `gh issue view 4603 -R jmorrison-juniper/MistHelper --json number,title,body,state,labels,comments,createdAt,updatedAt,author` (read-only).
- CI logs: run 42173674615, job 127747809271 (`--log-failed` and `--job --log`). Run 42181849465, job 127775278965. Run 45774119357, job 139754539003.
- Remote files on `main`: blob SHAs in R6, read through `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`.
- Compare API between base `1b8c06a8a0d15abbbe1ae8edb840dd0dd81e1bb6` and head `4b8948ca4f08de1888ca6ccdf05b734c407de367` (GET request, read-only).
- Local git history (read-only): `git log`, `git show 8dd9998f1`, `git show 2a6a58446`, `git hash-object` (no write).
- Local files: `tests\e2e\web_portal\test_juniper_menus_browser.py` lines 45 to 54, 182 to 187, 314 to 330. `web_portal\static\js\operations.js` lines 60, 146, 167 to 192, 250, 270 to 282, 1239 to 1253, 1410. `web_portal\routes\operations.py` lines 256 to 263 (the route returns HTTP 404 with `{"error": "Operation not found"}` when the menu has no parameters).
- No URL was fetched. No `web_fetch` call ran.

## R13. Unverified

- U-1. Root cause of the failure. Reason: the CI log captures no browser console output and no trace text. The diagnostic artifact was not read.
- U-2. Contents of artifact `e2e-diagnostics-web-portal`. The API lists it as present, not expired, 1,871,830 bytes, created 2026-11-06T06:35:33Z. The owner reports HTTP 403 for both download methods (comment IC_kwDOQltU8c8AAAABkivnLw). This record did not retry the download.
- U-3. Python and Dash versions of run 42185517703 and run 42180496231. Reason: only the job conclusion was read.
- U-4. Behavior of combinations A, B, and C in this environment. Reason: the matrix task T006 runs them. This record did not run them.
- U-5. Results of the owner probes in the issue comments. Reason: the record reports them only and did not rerun them.
- U-6. The issue comment that names "current main" versions (Dash 4.5.0 and Playwright 1.64.1). Main pins Dash 4.5.1 and Playwright 1.65.2 (RV-29, RV-31). The comment is stale.
- U-7. Whether the failure recurs on main after 2026-11-26. Reason: the record read 15 recent runs. No later run was known.
- U-8. Timing and results on a Windows local Chromium run. Reason: the record ran no test.
