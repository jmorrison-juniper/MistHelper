# Research: Isolate Network Routing Support Modules

## R1. Issue Facts

- Issue #4006 is open. Title: "Refactor: isolate network routing support modules". Labels: `refactor`, `networking`, and `src`. Created 2026-10-06. Last updated 2026-11-11.
- Parent issue #3824 is open. Its labels include `refactor` and `in-progress`.
- Required outcomes: move three modules into `support/`. Keep five network children and three support children. Update active imports, mock targets, logger names, source links, and one active documentation path. Add no compatibility wrapper. Do not edit historical specifications or performance inventory records. Add a focused structure guard. Regenerate menu API links. Run the focused and required gates.
- Ten owner comments from 2026-10-06 to 2026-11-11 record the following facts. They cover the local commit `1d2b6e50`, freshness checks, three failing catalog tests, and queue holds. They also cover the hold on `tests/unit/test_routing_utils.py` for issue #4728 and the instruction to keep the candidate local.

## R2. Linked Work

- Commit `1d2b6e5051225f7a60d5764538e4ab839080c6e9` ("refactor(network): isolate routing support modules", "Closes #4006") exists on GitHub. It is diverged from `main` (ahead 1, behind 402). It is on archive branch `archive/laptop-20261121/jmorrison-juniper-network-routing-support-4006`. Branch `archive/laptop-20261121/jmorrison-juniper-refactor-4006-network-routing-support` holds commit `1a8536660d86a49711c55f4ee43a49b596bf7ee8` with the same subject.
- The commit changes 17 paths. This list matches the issue. The three moved modules show 0 insertions and 0 deletions, which is a pure rename. `tests/unit/test_routing_utils.py` shows 29 insertions and 23 deletions.
- Pull request search for `4006` returns only PR #3873. It merged on 2026-10-06 and updates an OpenAI dependency. No open or merged pull request closes #4006.
- PR #4607: merged 2026-11-13. It changes the symbol guard, the catalog CSV under `specs/2448`, and troubleshooting modules.
- PR #4557: merged 2026-11-05. It changes the symbol guard.
- PR #4125: merged 2026-10-10. It adds the nested-package guard and baseline.
- PR #4122: merged 2026-10-10. It changes the performance catalog guard.
- PR #4107: merged 2026-10-13. It changes RRM code and holds no file in this set.
- PR #4208: open, draft, base `main`, updated 2026-11-22. It changes `tests/guardrails/test_src_public_symbol_preservation.py`.
- Open pull requests: 7 in total. Only PR #4208 changes a file in this set.

## R3. Legacy Record (Steps 3 and 4)

- Step 3: No folder under `specs/` on `main` starts with `4006-`. The working tree has none. The legacy record exists only in commits `1d2b6e5051225f7a60d5764538e4ab839080c6e9` and `1a8536660d86a49711c55f4ee43a49b596bf7ee8`. The folder is `specs/numbered/0/0/1/1/2/0/1/1/4006-network-routing-support/` with `spec.md`, `plan.md`, and `tasks.md`.
- Step 4: Each legacy file blob matches the commit contents (R-03 to R-05). The commit exists (R-01). The commit is not in `main` (R-02).
- Legacy claim audit, 17 claims in total: verified 7, stale 6, absent 4.
- Verified claims:
  1. The network root holds seven structural children before the move (R-19 and the tree listing).
  2. After the move, the root holds five children and the support package holds three (commit file list).
  3. A symbol guard mapping exists at the commit (candidate patch).
  4. A structure guard exists at the commit (R-37).
  5. A changelog fragment exists at the commit (R-35).
  6. The commit exists (R-01).
  7. The commit changes no file under `specs/` except its own record folder (commit file list).
- Stale claims:
  8. Tasks T001 to T014 are marked done. Owner comments of 2026-10-07 report failing catalog tests, and later comments report holds.
  9. `plan.md` names Python 3.13. `pyproject.toml` line 23 requires 3.15 (R-43).
  10. `spec.md` status says "Implemented". The issue says the work remains local.
  11. The claim "no overlap with open pull requests" predates PR #4208 (R-51).
  12. The claim that the payload move keeps content predates change `5e890ed6` (R-10, R-52).
  13. The claim that the five-item rule passes ignores the nested baseline entry (R-26).
- Absent claims:
  14. "Focused routing tests pass" has no reproducible output.
  15. "Final guards passed 26" has no reproducible output.
  16. "Regenerate both WebSocket pages" has no generator output. The commit shows hand edits.
  17. "Focused tests passed 195" conflicts with a later owner comment that reports 199 collected, 196 passed, and 3 failed.
- Decision D-15 applies. The new record reuses only verified facts.

## R4. Remote Verification Table

Each row is one check. The STATUS file `remote_checks` array holds the same 52 rows. Line numbers come from a decoded remote body (`contents` API with `ref`) unless the row states otherwise. Local blob equality is verified with `git ls-files -s` for the files that R5 counts.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Legacy commit 1d2b6e50 exists on GitHub | commits/1d2b6e5051225f7a60d5764538e4ab839080c6e9 | 1d2b6e5051225f7a60d5764538e4ab839080c6e9 | commit object | present | 0 |
| R-02 | Legacy commit 1d2b6e50 is contained in main | compare main with commit 1d2b6e5051225f7a60d5764538e4ab839080c6e9 | main | commit object | absent | 0 |
| R-03 | Legacy spec.md exists at the commit | specs/numbered/0/0/1/1/2/0/1/1/4006-network-routing-support/spec.md | 1d2b6e5051225f7a60d5764538e4ab839080c6e9 | 47a1589f11d187c74566b9f615dd3def43575033 | present | 1 |
| R-04 | Legacy plan.md exists at the commit | specs/numbered/0/0/1/1/2/0/1/1/4006-network-routing-support/plan.md | 1d2b6e5051225f7a60d5764538e4ab839080c6e9 | 35ea2420620a1a6574ee4ed35af5c7d5bbfd0d6f | present | 1 |
| R-05 | Legacy tasks.md exists at the commit | specs/numbered/0/0/1/1/2/0/1/1/4006-network-routing-support/tasks.md | 1d2b6e5051225f7a60d5764538e4ab839080c6e9 | 16677e1f44326b4781c976cc3ba58a769d86e82b | present | 1 |
| R-06 | Legacy record folder exists on main | specs/numbered/0/0/1/1/2/0/1/1/4006-network-routing-support | main | not applicable: no entry | absent | 0 |
| R-07 | Support initializer exists at the commit | src/mist/networking/network/support/__init__.py | 1d2b6e5051225f7a60d5764538e4ab839080c6e9 | 90a84f4e03ae67bcda70779cc784ec807135b0e4 | present | 1 |
| R-08 | Support display module exists at the commit with main content | src/mist/networking/network/support/_routing_utils_display.py | 1d2b6e5051225f7a60d5764538e4ab839080c6e9 | 81619905f517792de24025d65b267bc540c158b8 | present | 0 |
| R-09 | Support parsing module exists at the commit with main content | src/mist/networking/network/support/_routing_utils_parsing.py | 1d2b6e5051225f7a60d5764538e4ab839080c6e9 | 50cd37ff14e40e0b8f1ddda896ac3a9c1ab82f86 | present | 0 |
| R-10 | Support payload module at the commit matches main | src/mist/networking/network/support/_routing_utils_payload.py | 1d2b6e5051225f7a60d5764538e4ab839080c6e9 | 8e0229b79a05cbd1fab0af56c82608ba991cf28f | stale | 0 |
| R-11 | Support directory exists on main | src/mist/networking/network/support | main | not applicable: no entry | absent | 0 |
| R-12 | Display module on main, logger line | src/mist/networking/network/_routing_utils_display.py | main | 81619905f517792de24025d65b267bc540c158b8 | present | 31 |
| R-13 | Parsing module on main, function `_finalize_dest_transition` | src/mist/networking/network/_routing_utils_parsing.py | main | 50cd37ff14e40e0b8f1ddda896ac3a9c1ab82f86 | present | 212 |
| R-14 | Payload module on main, function `_post_device_command` | src/mist/networking/network/_routing_utils_payload.py | main | 38c2458ff14370be660d956ca30c252dc4fd291c | present | 234 |
| R-15 | Forwarding orchestrator exists on main | src/mist/networking/network/_routing_utils_forwarding.py | main | 38d519ca8c293b5324ad8526fa9b5de62e358697 | present | 0 |
| R-16 | Routing orchestrator on main, payload import | src/mist/networking/network/_routing_utils_routing.py | main | bf534a37421ffac1530e3a22c4e97ea810b48e6d | present | 25 |
| R-17 | SSR orchestrator exists on main | src/mist/networking/network/_routing_utils_ssr.py | main | b4d3c54f3bcdde7dd4a040bf20666b37c90d349c | present | 0 |
| R-18 | Facade on main, display, parsing, and payload imports | src/mist/networking/network/routing_utils.py | main | 6014ce4af18ec9e98c06099038c2cb276f152f53 | present | 22 |
| R-19 | Network package docstring on main | src/mist/networking/network/__init__.py | main | 0c8af57f1ddb5c887004be59357d20aeabae0abc | present | 1 |
| R-20 | Utility selection docstring names the payload path | src/mist/resources/device/_utility_commands_selection.py | main | b2216159314a3194b99357bf12b2db111784bd8b | present | 15 |
| R-21 | Routing tests name old mock targets, first target | tests/unit/test_routing_utils.py | main | 06b1ef72bdc6cc24f3d026daea6470966e4bda49 | present | 839 |
| R-22 | Unparseable guards import the old payload path | tests/unit/test_unparseable_response_guards.py | main | 567e4f1b7174e740a516e9a4b9038b892a404c2c | present | 16 |
| R-23 | Symbol guard MODULE_PATHS block | tests/guardrails/test_src_public_symbol_preservation.py | main | 08f978e755abdf643e7a6d826811401f710883f8 | present | 43 |
| R-24 | Catalog guard move map `_HISTORICAL_PATH_MOVES` | tests/guardrails/test_performance_hook_catalog.py | main | 36593fd74460c1023614fb84e8523303c94ea507 | present | 28 |
| R-25 | Hook catalog CSV row `hook-0281` names the display module | specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv | main | ee7a997df2dba3086122086f16a21d4807b23509 | present | 282 |
| R-26 | Nested baseline network entry with child count 7 | tests/guardrails/nested_package_baseline.json | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 107 |
| R-27 | Nested guard literal report reads 33 violations and 236 total excess | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 177 |
| R-28 | Move-module guidance guard exists | tests/guardrails/test_move_module_guidance.py | main | ae163b792b330285dba7a8c32cc957a78c3838d4 | present | 0 |
| R-29 | Menu API websocket page names the payload path | documentation/menu-api/websocket.md | main | 7d8601a1fdfa8c307cb0a78e9b967e72e0c79852 | present | 77 |
| R-30 | Wiki websocket page names the payload path | documentation/wiki/Menu-API-Endpoints-Websocket.md | main | f31684b8be0c8630f1ac8c954f9223b38013d2ab | present | 77 |
| R-31 | Menu wiki generator exists | scripts/generate_menu_wiki.py | main | f959225275536743e93bc95d37cb015865a73d53 | present | 0 |
| R-32 | Menu API map package entry exists | scripts/menu_api_map/__main__.py | main | 19f72aa767a1821f2ccf88680b8778b89012873d | present | 0 |
| R-33 | CI sets the path variables for mypy, vulture, pydocstyle, and interrogate | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-34 | Route function and base five in the route script | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-35 | Changelog fragment exists at the commit | changelog.d/issue-4006-network-routing-support.md | 1d2b6e5051225f7a60d5764538e4ab839080c6e9 | 7f207d66e61d330a5d27662e6d5e7e611df9ce2a | present | 1 |
| R-36 | Changelog fragment exists on main | changelog.d/issue-4006-network-routing-support.md | main | not applicable: no entry | absent | 0 |
| R-37 | Structure guard exists at the commit | tests/guardrails/test_network_routing_support_structure.py | 1d2b6e5051225f7a60d5764538e4ab839080c6e9 | 1278e6806026c6d873f23d96f5798449a98d6773 | present | 1 |
| R-38 | Structure guard exists on main | tests/guardrails/test_network_routing_support_structure.py | main | not applicable: no entry | absent | 0 |
| R-39 | Changelog naming and content rules | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| R-40 | Reference record spec.md shows the record shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| R-41 | OpenAPI path for `show_route` | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 30981 |
| R-42 | OpenAPI path for the raw `{endpoint}` route | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 0 |
| R-43 | Python requirement is 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R-44 | SDK function `listSiteDevices` in the pinned package | .venv\Lib\site-packages\mistapi\api\v1\sites\devices.py | local worktree | fd3faa0988e688c1cac4e21f22ebe22693f77409 | present | 17 |
| R-45 | SDK function `showSiteSsrAndSrxRoutes` in the pinned package | .venv\Lib\site-packages\mistapi\api\v1\sites\devices.py | local worktree | fd3faa0988e688c1cac4e21f22ebe22693f77409 | present | 3159 |
| R-46 | SDK generic endpoint function with `{endpoint}` in the pinned package | .venv\Lib\site-packages\mistapi | local worktree | not applicable: search | absent | 0 |
| R-47 | Pinned SDK version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local worktree | not applicable: directory | present | 0 |
| R-48 | Code search finds the payload module name in active files | search/code `_routing_utils_payload` | main | not applicable: search result | present | 0 |
| R-49 | Code search finds the display module name in active files | search/code `_routing_utils_display` | main | not applicable: search result | present | 0 |
| R-50 | Code search finds the parsing module name in active files | search/code `_routing_utils_parsing` | main | not applicable: search result | present | 0 |
| R-51 | Open draft PR #4208 changes the symbol guard file | tests/guardrails/test_src_public_symbol_preservation.py | PR 4208 head | not applicable: PR file list | present | 0 |
| R-52 | Main changed the payload module after the candidate base (commit `5e890ed6`) | src/mist/networking/network/_routing_utils_payload.py | main | 38c2458ff14370be660d956ca30c252dc4fd291c | stale | 0 |

Summary: 52 rows. Present 43. Absent 7. Stale 2 (R-10 and R-52).

## R5. Counting Method and Results

Method:

- A read-only PowerShell pass reads each file with `ReadAllLines`. A function starts at a line that matches `def` or `async def`.
- Parameters exclude `self` and `cls`. Comments are removed before the parameter count.
- Span is the number of physical lines from the `def` line to the last non-blank line indented deeper than the `def` line.
- Top-level blocks count `if`, `for`, `while`, `try`, `with`, and `match` statements at the first body indent.
- Generated dataclass initializers are not counted as functions.
- The local index blob equals the `main` blob for every counted file. Rows R-12 to R-14, R-16, R-18, R-20 to R-23 confirm this.
- `routing_utils.py` was also read in full with the view tool.

| File | Lines | Functions | Max parameters | Five parameters excluding `self` | Over 25 lines | Over 5 top-level blocks |
| - | - | - | - | - | - | - |
| `src/mist/networking/network/routing_utils.py` | 358 | 18 | 4 | 0 | 0 | 0 |
| `src/mist/networking/network/_routing_utils_routing.py` | 422 | 29 | 4 | 0 | 0 | 0 |
| `src/mist/networking/network/_routing_utils_display.py` | 539 | 36 | 4 | 0 | 0 | 0 |
| `src/mist/networking/network/_routing_utils_parsing.py` | 461 | 33 | 5 | 1 (`_finalize_dest_transition`, line 212) | 0 | 0 |
| `src/mist/networking/network/_routing_utils_payload.py` | 388 | 25 | 5 | 1 (`_post_device_command`, line 234) | 0 | 0 |
| `src/mist/resources/device/_utility_commands_selection.py` | 561 | 40 | 3 | 0 | 1 (`_select_site_and_device`, line 64, 26 lines) | 0 |
| `tests/unit/test_routing_utils.py` | 2036 | 162 | 3 | 0 | 6 (lines 1476, 1550, 1769, 1829, 1865, 1902) | 0 |
| `tests/unit/test_unparseable_response_guards.py` | 211 | 12 | 2 | 0 | 0 | 0 |
| `tests/guardrails/test_src_public_symbol_preservation.py` | 702 | 36 | 2 | 0 | 3 (lines 218, 348, 403) | 0 |

Scope notes:

- `_routing_utils_forwarding.py` and `_routing_utils_ssr.py` are not named by the issue. They were not counted.
- The candidate structure guard has three test methods. Its class methods have at most two parameters. Its `active_old_path_violations` method spans 27 lines. Span checks on the refreshed guard are part of T013.

## R6. Decisions

Each decision has alternatives, a chosen option, a reason, and a risk. No decision requires a human decision under section 6 of the brief.

### D-1 Support package layout

- Alternatives: (a) re-export the classes in `support/__init__.py`. (b) Keep the modules at the root.
- Chosen: place the modules in `support/`, and give `__init__.py` a docstring only.
- Reason: A re-export adds module-level names to the package, and the symbol guard does not map them. A root placement misses FR-003.
- Risk: Callers must use the full module path. TC-09 finds any old path.

### D-2 No shim or alias

- Alternatives: (a) keep thin modules at old paths that re-export names. (b) keep copies at old paths.
- Chosen: remove old paths and update every active reference.
- Reason: `AGENTS.md` and `copilot-instructions.md` forbid compatibility shims. The issue requires no alias. The search finds active references in seven files only (R-18, R-16, R-20, R-21, R-22, R-29, R-30).
- Risk: An unknown external caller fails at import. TC-08 and TC-09 detect the old path.

### D-3 Move with git

- Alternatives: (a) create new files and delete old ones. (b) cherry-pick the candidate rename.
- Chosen: `git mv` from the current `main` content.
- Reason: Git records a rename and keeps history. Blob equality proves that the content is unchanged (TC-11).
- Risk: Git may not detect a rename if the content changes too much. TC-15 reviews the rename statistics.

### D-4 Rebuild from current main

- Alternatives: (a) rebase the candidate. (b) cherry-pick the candidate. (c) rebuild from current `main`.
- Chosen: option (c).
- Reason: The candidate payload blob `8e0229b7` predates change `5e890ed6` (PR #4317). A replay can revert that change. The symbol and structure guards also changed on `main`.
- Risk: Manual edits can drop a line. TC-11, TC-04, and TC-14 detect content and symbol changes.

### D-5 Structural child rule

- Alternatives: (a) count every entry. (b) count only modules.
- Chosen: count direct Python modules except `__init__.py`, plus direct directories. Never count `__pycache__`.
- Reason: The issue count of seven uses this rule. The candidate guard and the nested ratchet use it.
- Risk: A future package with a non-Python child is undercounted. The guard prints the child set, so a reviewer can see it.

### D-6 Nested-package baseline

- Alternatives: (a) keep the stale entry. (b) add an allowance for the support package.
- Chosen: remove the network entry and change the literal at line 177 to 32 violations and 234 total excess.
- Reason: The ratchet rejects stale entries (guard lines 137 and 148 to 149). An allowance adds debt, which the constitution forbids.
- Risk: The new total is inferred from the baseline arithmetic (236 minus 2). TC-06 prints the measured report (U-11).

### D-7 Performance catalog map

- Alternatives: (a) edit `hook-catalog.csv`. (b) delete the three hook rows. (c) skip the test.
- Chosen: add three entries to `_HISTORICAL_PATH_MOVES`.
- Reason: The CSV artifacts are performance inventory records, which the issue forbids editing. The guard already uses this map for approved moves (guard lines 28 to 38 and 46 to 59).
- Risk: A symbol missing from a moved module fails its row. This failure is intended. The `Old paths` gate in `.github/copilot-instructions.md` also reports this file, because its keys name historical paths. The pull request body records that exception.

### D-8 Symbol guard map

- Alternatives: (a) add a separate guard. (b) add no entry.
- Chosen: add three `MODULE_PATHS` entries after line 43.
- Reason: The symbol test reads `MODULE_PATHS` (guard lines 36 to 97). No entry leaves a moved module unchecked.
- Risk: PR #4208 changes the same file. D-13 holds publication.

### D-9 Test strings and logger names

- Alternatives: (a) keep old test strings. (b) hard-code logger names in the moved modules.
- Chosen: change the test strings to canonical paths. Keep `getLogger(__name__)` in the modules.
- Reason: Six modules already use `getLogger(__name__)` (R-12, R-15, R-16, R-17, R-18, R-20). A hard-coded name drifts.
- Risk: Test logger names change. TC-02 and TC-03 detect a broken target.

### D-10 Structure guard

- Alternatives: (a) use only the nested ratchet. (b) keep the candidate text unchanged.
- Chosen: add the candidate guard, refreshed from current `main`. Split its 27-line function. Add inline comments. Print counts on success. Exclude the catalog move map from the active-path scan.
- Reason: The nested ratchet does not check the support package. The repository guard rule requires counts on success. Principle VI requires comments.
- Risk: The guard reads `git ls-files`. TC-01 runs in the worktree.

### D-11 Generated pages

- Alternatives: (a) hand-edit both pages, as the candidate does. (b) update only the menu-API page.
- Chosen: regenerate both pages with the generator and treat both as the active documentation set.
- Reason: The wiki page carries the same old path (R-30). The generator keeps the link format stable, as the menu reference gate requires.
- Risk: The generator may format links differently from the candidate. TC-10 detects drift.

### D-12 Branch, commit subject, and fragment name

- Alternatives: (a) branch `refactor/4006-network-routing-support`. (b) name the fragment `pr-<number>.md` before the pull request exists.
- Chosen: branch `chore/4006-network-routing-support`. Commit subject `refactor(network): isolate network routing support modules`. Fragment `issue-4006-network-routing-support.md`. Add the `in-progress` label and keep the existing labels.
- Reason: `AGENTS.md` lists `feat`, `fix`, `chore`, and `docs` for branches. The constitution lists `refactor` for commits. The changelog README allows an issue-based name before the pull request exists.
- Risk: The scope label `src` is not in the scope list of `copilot-instructions.md` (F-13). The labels stay as they are.

### D-13 Publication gate

- Alternatives: (a) publish now and rebase later. (b) wait without stated conditions.
- Chosen: publish only when five conditions record as met. The conditions are in `design/checklists/publication.md`.
- Reason: `AGENTS.md` allows one open pull request for each file. The issue requires a handoff before changes to `tests/unit/test_routing_utils.py`. The issue also requires a serial slot.
- Risk: Publication waits for owners outside this run. Each condition names the owner action.
- Human decision required: no. The conditions use the coordination rules of the repository. They do not fall under the four human categories of section 6.

### D-14 Existing debt and raw HTTP call

- Alternatives: (a) fix the violations in this change. (b) replace the raw `requests.post` call with an SDK method.
- Chosen: record each item. Change none of them in this change.
- Reason: FR-018 keeps function bodies unchanged. The installed SDK has no generic endpoint function (R-46). A replacement changes behavior without proof.
- Risk: The debt stays in the code. The orchestrator files a separate remediation issue.

### D-15 Legacy record

- Alternatives: (a) copy the legacy files and edit them. (b) ignore the legacy commit.
- Chosen: write a new record that reuses only verified facts (R3).
- Reason: Seven of 17 legacy claims are verified. Six are stale, and four are absent.
- Risk: The new record can drift from the commit. R4 cites each blob.

## R7. Mist API and SDK Evidence

- Routing code calls the Mist API in three places on `main`. `routing_utils.py` line 201 calls `mistapi.api.v1.sites.devices.listSiteDevices`. `_routing_utils_payload.py` line 336 calls `mistapi.api.v1.sites.devices.showSiteSsrAndSrxRoutes`. `_routing_utils_payload.py` line 250 calls `requests.post` for the raw device command path. Lines 201, 336, and 250 are local line numbers from the blob-equal file.
- Installed SDK, version 0.64.1, file `.venv\Lib\site-packages\mistapi\api\v1\sites\devices.py`. `listSiteDevices` is defined at line 17 (R-44). `showSiteSsrAndSrxRoutes` is defined at line 3159 (R-45). The file hash is computed with `git hash-object` without a write.
- Search of the installed package for `{endpoint}` returns no match (R-46). No working SDK function for the raw path was found in 0.64.1.
- Local OpenAPI file `documentation\mist-api-openapi31yaml.yaml` has the path `/api/v1/sites/{site_id}/devices/{device_id}/show_route` at line 30981 (R-41). Its hash equals the `main` blob. The raw path `/api/v1/sites/{site_id}/devices/{device_id}/{endpoint}` has no match (R-42).
- No Juniper device behavior is claimed. No skill was loaded.

## R8. Skills

No skill was loaded. The change makes no device behavior claim, and no container skill applies to this change.

## R9. Sources

Local files read:

- `AGENTS.md` (full view).
- `.github/copilot-instructions.md` (lines 1 to 600, in ranges). The local gates table and the move-module rules come from this file.
- `.specify/memory/constitution.md` (lines 1 to 562, in ranges).
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md` (full view).
- `.specify/scripts/powershell/spec-route.ps1` (lines 1 to 140 by view). Function lines come from R-34.
- `src/mist/networking/network/routing_utils.py` (full view).
- Named modules and tests (search, line numbers, and span measurement in R5).
- `pyproject.toml` (search and hash, R-43).
- Installed SDK under `.venv\Lib\site-packages\mistapi` (search and hash, R-44 to R-47).
- OpenAPI file `documentation\mist-api-openapi31yaml.yaml` (search and hash, R-41, R-42).
- Reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` (heading search, shape only).
- Documentation files named in the brief: line counts only (quality-gates 292, architecture 299, development-setup 377, container-deployment 431, operator-guide 753).

GitHub reads (`gh`, read-only):

- Issues 4006, 3824, and 4728, and issue comments 6755844523 and 6755904711 (issue #2711 records).
- Pull requests 4607, 4557, 4125, 4122, 4107, and 4208 (state and file lists). Open pull request list for overlap.
- Commit `1d2b6e5051225f7a60d5764538e4ab839080c6e9` (metadata, files, and patches). Commit `52e6fe39493fcec567c2a42e490b76c40b9576dd` (exists, not used).
- Compare `main` with commit `1d2b6e50`. List branches. Read the recursive tree and file contents of `main`. Read the payload module history. Run code search.

Web sources: none fetched.

## R10. Unverified

- U-1: No test, guard, or gate ran in this authoring run. Test results and counts are unverified.
- U-2: The menu generator and `scripts/menu_api_map` did not run. Their output is unverified.
- U-3: `test_summary_artifacts_match_catalog_tables` may check hook counts by file. It did not run after the map change.
- U-4: Ruff ordering for the moved import block is unverified.
- U-5: Black formatting of parenthesized map values is unverified.
- U-6: The raw `requests.post` route may have an SDK equivalent in a later version. The check covered version 0.64.1 only.
- U-7: The SDK function `showSiteSsrAndSrxRoutes` and the OpenAPI path `show_route` name the same operation. The mapping is not checked line by line.
- U-8: The Juniper documentation URLs in the menu pages were not fetched.
- U-9: GitHub code search can lag behind the default branch. Search results prove presence only.
- U-10: The state of PR #4208 can change before publication.
- U-11: The total of 234 excess is inferred from the baseline arithmetic. The guard run confirms it.
- U-12: `pyproject.toml` names `PLR0913` only in a comment (line 235). It is not confirmed whether the linter counts `self`.
- U-13: `documentation/quality-gates.md`, `architecture.md`, `development-setup.md`, `container-deployment.md`, and `operator-guide.md` were not read in full.
- U-14: The #2861 branch hold was not inspected.
