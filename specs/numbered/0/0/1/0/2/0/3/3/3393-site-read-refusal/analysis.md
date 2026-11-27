# Analysis: Site read refusal

This review compares the spec, plan, tasks, and research with the code on GitHub `main`. It also grades each claim of the legacy record. Remote evidence uses the RC identifiers of design/research.md. Source lines come from the files of the same blob SHA on `main`.

## Remote state on 2026-11-26

| Item | State | Evidence |
| - | - | - |
| GitHub `main` | Head `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` | RC-01 |
| PR 4413, the repair | MERGED 2026-10-28T04:19:22Z. Title `fix(upgrade-portal): refuse failed multi-site cloud reads`. Body says `Refs #3393`. | RC-02 |
| PR 4413 changed paths | 13 paths: the changelog fragment, nine legacy record files, `org_upgrade.py` (+15, -2), the contract test module, and the browser test module | `gh pr view 4413 --json files` |
| PR 4413 check rollup | Read on 2026-11-26. Every reported check reads SUCCESS or SKIPPED. No check reads FAILURE. | `gh pr view 4413 --json statusCheckRollup` |
| PR 4541 | MERGED 2026-11-05. Journey harness work for issue 3200. | `gh pr view 4541` |
| PR 3426 | MERGED 2026-09-26. Issue 3389 repair. | `gh pr view 3426` |
| PR 4547 | MERGED 2026-11-13. Retry scope. Changes `org_upgrade.py`. | `gh pr view 4547 --json files` |
| PR 4701 | MERGED 2026-11-13. Site locks. Changes `org_upgrade.py`. | `gh pr view 4701 --json files` |
| Open PRs | Seven open PRs: 4890, 4889, 4888, 4887, 4886, 4813, 4208. None changes a file of this record or the route module. | `gh pr list --state open --json number,files` |

## Issue facts

- Title: `Runtime: RequestException in selected_rows answers 500 at the multi-site options save`. State: OPEN. Author: `jmorrison-juniper`. Created 2026-09-25T17:17:58Z. Updated 2026-11-11T03:32:53Z.
- Labels: `bug`, `web-portal`, `api`, `upgrade-portal`, `runtime`, `needs-human-review`.
- Requirement: a failed site read during the multi-site options save must answer a clear refusal. The status is 502 or 503, not 500. The form keeps each typed value. The portal saves no plan.
- Requirement: check whether the options page and the confirmation page also answer 500.
- Reproduction step: select two sites that hold devices. Make `listOrgSites` raise `requests.exceptions.ConnectionError`. Save the options.
- Error text reported: `{"error":{"code":"server_error","message":"The portal met an unexpected fault."}}`.
- Source: a contract probe on the branch of issue 3389 (base `b85d9118`). The issue also cites the site list cache of issue 3210.
- Comment 1, 2026-10-06, claims the issue for a read-only assessment.
- Comments 2 and 3, 2026-10-06, are two copies of an assessment at base `efd0828`. They give line numbers that are stale on `main`, and they state that the issue and issue 3394 are two defects (U-7).
- Comment 4, 2026-10-31, claims the bounded repair for issue 3393.
- Comment 5, 2026-10-31, reports that PR 4413 merged the complete repair and asks to keep the issue open.
- Comment 6, 2026-11-11, names draft PRs 4547 and 4701 as owners of `org_upgrade.py`. Both merged on 2026-11-13 (finding A-7).

## Findings

### A-1 Production path below the SDK is unproven (HIGH)

- The mistapi call `mist_get` sends each request through `_request_with_retry` (RC-69).
- The retry wrapper catches `requests.exceptions.ConnectionError` and returns an answer (RC-70). It also catches every other exception (RC-71).
- An answer built without a response has no status (RC-72). The page reader turns that into a read failed reason (RC-30, `capture/devices.py` line 265).
- The repository already records this behavior. The docstrings at `capture/devices.py` lines 250-257 and 321 say so.
- Source prediction for the options page (GET) and the confirmation page (GET): `selected_rows` raises `SiteListIncompleteError` (RC-25). The app handler answers 503 with `site_list_incomplete` (RC-26, `select.py` lines 256-257 and 268).
- Source prediction for the save (POST): the save reads the organization inventory first (RC-15). The site view is empty, and `records.refusal` raises `OrgSiteRefusal` (RC-17, RC-33). `save_options` answers a `ValueError` with 400 `options_invalid` (`org_upgrade.py` lines 1230-1231). The 400 answer is not the 503 answer of PR 4413.
- The `RequestException` handlers of PR 4413 run only for an exception raised above mistapi. The contract tests inject that exception at the reader seam (RC-37).
- A grep found no direct `requests` call in the upgrade portal, except `api/mist_client.py`. That module serves `routes/mist.py`, not this path.
- Consequence: The issue's 500 needs an exception that escapes mistapi. Source reading finds no such path for these reads.
- Status: Unproven. Warning: a wrong save plan starts firmware writes, so the production path needs proof before a further code change. T008 provides the proof.

### A-2 The save refusal for an unread site misleads the operator (HIGH for operators)

- The unread-site text says the portal read no device at each named site (RC-32, `org_site_records.py` lines 41-44).
- It also tells the operator to clear that site on the Sites page.
- The text does not name the Mist cloud.
- Caution: an operator might clear a healthy site after a transient cloud outage. The operator can restore the site, so the harm is recoverable.
- Status: Open. The follow-up order is in D-11.

### A-3 Eleven added lines carry no inline comment (MEDIUM)

- Lines 230 and 231 define the 503 site read constants.
- Lines 1147 to 1149, 1227 to 1229, and 1350 to 1352 hold the three handlers.
- Each line has no inline comment (checked with a grep for a trailing comment).
- Principle VI of the constitution, and the inline comment rule of AGENTS.md, require a comment on each executable line.
- Status: Open. T007 fixes this in a comment-only change.

### A-4 The retry route calls selected_rows with no handler (MEDIUM)

- `open_retry` in `org_controls.py` (lines 152 to 174) calls `selected_rows` at line 170 (RC-29).
- The route is live. The factory discovers the blueprint by name (RC-28), and the retry path is `/api/org-upgrades/<upgrade_id>/retry`.
- A `RequestException` from that call would answer the generic 500 (RC-27). Source reading also says the call does not receive one in production (A-1).
- Status: Open. D-6 moves it to a separate issue.

### A-5 Issue 3394 stays open in the save path (LOW, out of scope)

- `_complete_aggregate_options` checks only that the targets exist (RC-16, lines 695 to 704).
- `_selected_target_rows` at line 775 drops each device with no version, and it gives no message.
- The effect is a silent plan that omits a checked device family.
- Status: Out of scope. D-7 keeps it out of this record.

### A-6 The issue body is stale in five places (LOW)

- The retired path `upgrade_portal/app/routes/org_upgrade.py` is absent on `main` (RC-21). The live path is `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`.
- The line numbers are stale. `save_options` is at line 1215 now, not 863.
- The statement that no clause catches `RequestException` is stale after PR 4413 (RC-10).
- The cache wording "less than one minute" matches a TTL of 60 seconds (RC-24).
- The reproduction used an injected exception, not a live cloud (A-1).

### A-7 Comment 6 names owners that already merged (LOW)

- Comment 6, dated 2026-11-11, says that draft PRs 4547 and 4701 own `org_upgrade.py`.
- Both merged on 2026-11-13. No open PR changes a file of this record.
- The ownership claim is stale. The review hold on the issue is a human decision (D-2).

### A-8 The contract tests skip the SDK (LOW)

- The contract tests replace the reader above mistapi (contract module lines 33 to 42).
- No test runs the mistapi retry wrapper with a transport fault.
- T008 closes this gap.

### A-9 Operator documentation names no refusal (LOW)

- The README (RC-34) and the operator guide (RC-35) do not name the refusal.
- The release fragment (RC-44) names the change.
- The record adds no operator text now. The refusal text is a transient cloud answer, and T008 may change the answers. Revisit after T008.

### A-10 Legacy facts are stale (INFO)

- The plan says Python 3.13. The project requires 3.15 (RC-58).
- The research and analysis name base `9991d30`. The current base is `064cec47`, and `main` is `f03c6c9b`.
- The status reads "Approved for implementation". The PR merged.

## Legacy claim verification

Result values: `verified` means that `main` or the local source agrees with the claim. `stale` means that `main` now disagrees, or the claim describes a past state that changed. `absent` means that no remote or source evidence exists for the claim.

| ID | Legacy file and claim | Result | Evidence |
| - | - | - | - |
| L01 | spec: feature branch `jmorrison-juniper-fix-org-upgrade-cloud-read` | verified | PR 4413 head branch |
| L02 | spec: created 2026-10-23 | verified | PR 4413 createdAt 2026-10-23T20:43:38Z |
| L03 | spec: status "Approved for implementation" | stale | PR 4413 merged 2026-10-28 |
| L04 | spec: repair excludes issue 3394 and firmware starts | verified | RC-16, contract store checks |
| L05 | spec, story 1, scenario 1: save answers 503 with a cloud-read message | verified | RC-10, RC-37 |
| L06 | spec, story 1, scenario 2: values remain and no plan exists | verified | RC-38, contract lines 56 to 62 |
| L07 | spec, story 1, scenario 3: repeated save saves the validated plan | verified | contract lines 98 to 111 |
| L08 | spec, story 2, scenario 1: both pages answer 503 | verified | RC-09, RC-11 |
| L09 | spec, story 2, scenario 2: confirmation failure keeps the plan | verified | contract lines 79 to 96 |
| L10 | spec edge: connection error and timeout get one refusal | verified | contract lines 48 and 80 |
| L11 | spec edge: refused replacement keeps the earlier plan | verified | contract lines 64 to 77 |
| L12 | spec edge: missing sites keep the 404 refusal | verified | `org_upgrade.py` line 1151, `test_org_site_records_routes.py` line 246 |
| L13 | spec edge: invalid options keep the 400 refusal | verified | `org_upgrade.py` lines 1226 and 1231 |
| L14 | spec edge: successful reads keep the confirmation flow | verified | contract lines 98 to 111 |
| L15 | spec edge: transport text stays out of the response | verified | RC-37, contract lines 39, 59, and 93 |
| L16 | spec: transport uses listOrgSites and listOrgSiteStats | verified | RC-22, RC-66, RC-68 |
| L17 | spec: no transport or SDK change | verified | PR 4413 changed no `select.py` or SDK file |
| L18 | plan: Python 3.13 | stale | RC-58 requires 3.15 or newer |
| L19 | plan: dependencies are Flask, requests, and mistapi | verified | `requirements.txt`: flask 3.1.3, requests 2.34.2, mistapi 0.64.1 (RC-59) |
| L20 | plan: no additional cloud request | verified | PR 4413 adds 15 lines and removes 2. The new handlers add no call. |
| L21 | plan: broad handlers stay in place | verified | `org_upgrade.py` lines 1230 and 1231 |
| L22 | plan: worktree, branch hook, and feature.json behavior | absent | Process claims with no remote evidence (U-3) |
| L23 | plan: the managed route resolves through create-new-feature.ps1 | verified | RC-50 (the script exists, and the dry run is unverified, U-3) |
| L24 | plan: the route module exceeds the top-level limit | verified | The module defines more than five top-level names (grep) |
| L25 | plan: some route functions exceed 25 lines | verified | `_aggregate_saved_options` spans lines 1273 to 1305 (33 lines) |
| L26 | plan: the contract-test and changelog folders exceed five children | verified | Tree: 66 children and 335 children |
| L27 | plan: the commit uses Conventional Commits | verified | Commit 3d2e538 title (gh api) |
| L28 | research: 503 and the save check before any session write | verified | RC-10, `org_upgrade.py` lines 1232 to 1234 |
| L29 | research: only the selected_rows call of each page route is protected | verified | RC-09, RC-11 |
| L30 | research: current main is 9991d30a1 | stale | RC-01 shows `f03c6c9b` |
| L31 | research: the assessment matches all three affected calls | verified | `selected_rows` calls at lines 1146, 1280, and 1349 |
| L32 | research: sibling cloud-status failures answer 503 | verified | RC-20 |
| L33 | research: the browser keeps values after an error | verified | RC-38, browser test lines 70 to 76 |
| L34 | research: the site read precedes the plan build and the write | verified | RC-13, RC-14 |
| L35 | research: the artifact list endpoint answers HTTP 404 | absent | Service state (U-5) |
| L36 | research: all 11 open PRs had no path ownership | absent | Historical count (U-6) |
| L37 | analysis: 11 tasks, 8 requirements, and 4 success criteria | verified | Legacy tasks and spec files |
| L38 | analysis: ten issue-specific contract cases | verified | Ten cases in the contract module (lines 48 and 80) |
| L39 | analysis: 106 passed tests and 96 existing contracts | absent | Test output (U-2) |
| L40 | analysis: lint, type, and symbol gate outputs | absent | Tool output (U-2) |
| L41 | analysis: feature commit 3d2e538 | verified | RC-04 |
| L42 | analysis: base remained 9991d30a | stale | RC-05 is the PR base, and RC-01 is main |
| L43 | analysis: no closure, merge, or auto-merge | stale | RC-02 shows PR 4413 merged |
| L44 | tasks: all 11 tasks complete | verified | Every task line carries `[x]`. The file blob matches `main`. |
| L45 | tasks: the delivered paths exist | verified | RC-07, RC-36, RC-44 |
| L46 | quickstart: the three commands name existing test targets | verified | RC-36, RC-38, RC-41 |
| L47 | data model: no model or schema change | verified | PR 4413 file list |
| L48 | contract: the POST and GET paths | verified | RC-18 |
| L49 | contract: code `org_upgrade_site_read_failed` | verified | RC-08 |
| L50 | contract: the message text | verified | RC-08 |
| L51 | checklist: no clarification marker remains | verified | Grep of the legacy checklist |
| L52 | checklist: the scope excludes issue 3394 | verified | RC-16 |

The legacy record has 52 claims. Of these, 42 are verified, 5 are stale, and 5 are absent.

## Requirement, task, and test mapping

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 save and page 503 for transport faults | T001, T002, T008 | Contract `test_failed_save_creates_no_plan` (3 cases), `test_failed_page_read_preserves_the_plan` (4 cases), and T008 cases |
| FR-002 names the cloud read and the recovery | T001, T005 | Contract envelope check (line 59 and line 93), browser flash check (line 73) |
| FR-003 no plan, nonce, or saved options | T003 | `test_failed_save_creates_no_plan` store and session checks |
| FR-004 form keeps every value | T004 | `test_cloud_read_refusal_keeps_each_entered_option` (lines 50 to 76) |
| FR-005 refused replacement and failed page keep state | T002, T003 | `test_failed_replacement_preserves_the_previous_plan`, `test_failed_page_read_preserves_the_plan` |
| FR-006 successful, validation, and 404 answers unchanged | T006 | `test_empty_selection_keeps_the_validation_refusal`, `test_a_site_removed_before_save_returns_sites_required_without_a_plan` |
| FR-007 local mocks only and no firmware start | T006, T-LOCAL-GATES | Every contract test uses the local fake reader and the in-memory store |
| FR-008 device family rules of issue 3394 unchanged | T006 | `test_a_site_with_no_checked_device_type_stops_the_save`, `test_no_planned_device_at_any_site_keeps_the_old_refusal` |
| FR-009 inline comments on each added line | T007, T-LOCAL-GATES | Regression tests after the comment-only change. No automated check reads comments, so the symbol gate and a line review also apply. |
| FR-010 no transport text in the response | T001 | Contract envelope equality with the raised text `private-transport-detail` (lines 39 and 59) |
| FR-011 documented answer below the SDK boundary | T008, T-REMOTE-CI, T-LOCAL-GATES | T008 cases for the save, the options page, and the confirmation page |

Every requirement maps to at least one task and at least one test. Success criteria SC-001 to SC-004 map to T001, T002, T008, T003, T004, and T006.

## Consistency review

- The spec, plan, and tasks use the same requirement IDs. The plan names each file that the tasks change.
- The tasks use only verification commands from the local gates table of `.github/copilot-instructions.md` (RC-56) or the gate map in plan.md.
- The plan keeps the change to two files. `org_upgrade.py` carries the comments, and the contract test module carries T008.
- The spec states that no product code change happens for the repair itself. The repair is already on `main`.
- The record reuses the legacy folder. The stale facts above appear in the spec and plan text only as corrections.

## Unresolved items

- U-A: The production answers for a transport fault below mistapi (A-1). Owner: the test in T008.
- U-B: The misleading unread-site text (A-2). Owner: a follow-up issue, ordered by D-11. HUMAN-DECISION-REQUIRED applies to the order.
- U-C: The retry caller (A-4). Owner: a follow-up issue (D-6).
- U-D: Issue 3394 (A-5). Owner: the existing issue 3394 (D-7).
- U-E: The review hold on issue 3393 (A-7). Owner: a human reviewer (D-2).
