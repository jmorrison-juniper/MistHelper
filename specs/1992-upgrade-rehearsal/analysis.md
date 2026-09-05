# Analysis of the upgrade rehearsal harness

Run 2026-09-04 by the `speckit.analyze` step, against commit `cfb91902`.

This file holds the report word for word. It found two findings of high severity,
and the feature is not ready for a pull request until F1 and F2 are closed.

---

## What I did

Read every artifact under `specs/1992-upgrade-rehearsal/`, the 7 harness modules, the 4 test modules, the shipped `gate`/`phase_gate`/`driver`/`events`/`stop`/`upgrade_service` seats, and sections 5 and 6 of `specs/1823-upgrade-capture-portal/quickstart.md`. I re-ran the suite: **48 passed in 4.73 s**, longest test 0.59 s.

I changed one file: `specs/1992-upgrade-rehearsal/quickstart.md` section 13, which held corrupted text — `holds <TAB>ests` (a lost backslash in `\tests`) and `xplicit_package_bases` (a lost `\e`). Both are now correct and fenced in backticks. Nothing else was touched; the tree is otherwise clean.

## 1. Coverage

| Requirement | Cover | Verdict |
| - | - | - |
| FR-001, FR-002 | `harness.start` → `driver.RunDriver.start`; `_phase_gate` builds shipped `SettleGate`/`PhaseSettleGate` | Covered |
| FR-003 | `test_rehearsal_stop` → `stop.stop_run_and_record`, `stop.stop_run`, `stop.read_last_status` | Covered |
| FR-004 | No test. Structural claim, enforced only by review | **No automated cover (LOW)** |
| FR-005 | `test_the_resolver_refuses_every_firmware_write` + both guard tests | Covered |
| FR-006 – FR-009 | `cloud.py` + `test_every_cloud_call_carries_the_keyword_names_of_the_contract`, `..._page_guard`, `..._short_page...` | Covered |
| FR-010 | `test_the_event_search_always_names_the_device_family`; the `ap` default proven end to end by drill 1 | Covered |
| FR-011 – FR-013 | `test_rehearsal_support` (version, uptime, catalogue, page fields); `_status` answers | Covered |
| FR-014 – FR-016 | `clock.py` + 4 clock tests + measured 4.73 s | Covered |
| FR-017 – FR-026 | `test_rehearsal_cascade` (order, guard, settle window, AP window, post-check, status read) and `test_rehearsal_stop` (cancel, mid-write, message) | Covered |
| FR-027 | Half. The org-scope call is proven (`calls_of("cancelOrgSsrUpgrade") == 1`). The second clause, "the run record shows `scope: "org"`", is asserted as `router_plan().route.scope == "org"` — the test's own fixture | **Half covered, circular assertion (HIGH)** |
| FR-028 | 3 drills + summary test | Covered |
| FR-029 – FR-031 | `live-checklist.md` | Covered by prose |
| FR-032 | STE linter: every file 95–99, floor 80 | Covered |

Success criteria: SC-002 (4.73 s), SC-003 (0.59 s), SC-004, SC-005, SC-006, SC-007 (5 items), SC-008 all hold and I re-measured each. **SC-001 does not hold** — see item 4.

Edge cases of `spec.md`: the phase timeout, the version change with no earlier uptime, the stale record, the early stop and the late stop are each covered. **"A statistics read fails for one poll round → mark the round partial and continue" is not covered.** The delivered test uses a page whose `total` overstates its `results`, not a failed read; no stand-in answer ever carries a non-200 status, though `data-model.md` §4 rule 1 promises one.

Tests that satisfy no functional requirement (all legitimate, listed for completeness): `test_the_run_reaches_the_complete_state`, `test_the_run_record_holds_the_stop_outcome`, `test_the_stopped_run_reaches_the_stopped_state`, `test_a_stop_with_the_wrong_text_reaches_no_cloud_call` (asserts FR-038b of feature 1823, not of this spec), `test_the_fleet_holds_two_devices_of_each_phase_family`.

## 2. Consistency

The contract is honest about the calls it names, and `test_every_cloud_call_carries_the_keyword_names_of_the_contract` enforces it at run time. I found no case of the #1991 shape — no stand-in answering a call the caller never makes. The four clock seats are correct, including `phase_gate.py:264`, which is the `clock` parameter of `CloudReconnectReader` (the class opens at 246). But the contract table omits one endpoint the code really resolves: `upgrade_service.py:1550` resolves `listOrgDevicesStats` for the SSR org read. The stand-in handles it; the contract's nine-row table does not name it.

The plan is stale in two named places, and both point at the same missing piece: `RunDriverDeps.submit` is `None` in the harness, so no `UpgradeSubmitter` double exists, and no `StandInSession` object exists — the harness passes `None`.

## 3. The unticked task

**There is none.** All 53 tasks in `tasks.md` carry `[X]`, and I re-verified the work behind the ones that are easy to over-claim: T042 (durations recorded), T043–T050 (gates), T053 (CHANGELOG names #1992 and #2007). Two ticked tasks are not fully true, though:

- **T051** is ticked, but its stated command, `python -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal`, fails with `Error: file not found` — the linter takes files, not a directory. Run per file (quickstart §9 does), and every file passes. The result stands; the recorded command does not run.
- **T052** asks for the inline comment on every executable line. Spot checks pass, but `quickstart.md` §9 grades only 6 of the 10 Markdown files — `spec.md`, `tasks.md`, `live-checklist.md` and `checklists/requirements.md` are missing from the list. I graded them: all pass.

## 4. Honesty of SC-001

**The claim does not hold. The suite proves 8 of the 9, and the ninth only in part — call it 7.5.**

Scenario C, five conditions: C2 (cascade order), C3 (three settle signals plus the AP's extra minute), C4 (status read under 1 second) and C5 (automatic post-check) are all proven. **C1 — "the portal refuses to start the upgrade when no verified pre-check exists" — is not proven and cannot be.** The harness hands the driver a record that already carries `pre_capture_id: "capture-rehearsal-0001"` and starts the thread below the route that would refuse. No functional requirement of `spec.md` even names C1, so it fell through the whole chain. It is also fair to say C1 is not "driven by the answers of the cloud", which is SC-001's own qualifier — but then the total is 8, not 9, and the sentence is still wrong.

Scenario D, four conditions: D1, D2 and D3 are proven. **D4 is proven only in its first half.** The org-scope cancel call really happens. The second sentence, "the run record shows `scope: "org"` for that device", is never read out of a run record. The record can hold it — `wiring._submission_row` writes `"scope"` into the submission row — but that row is written at submit time, and the rehearsal skips submission entirely (`submit=None`, exactly the double `plan.md` design decision 5 promised and no one built). The test asserts the scope of the plan object it constructed itself two functions earlier, which passes whatever the portal does.

That last one is the finding I would not ship without. It is the same family as #1991: not a stand-in answering the wrong shape, but an assertion reading a value from the test's own hand instead of from the artefact the requirement names.

## 5. Scope

**Confirmed. Nothing in the delivered code can reach the Mist cloud or write firmware.** Four independent barriers, and each is real:

1. `_resolve_endpoint` is the single door to every upgrade endpoint (`upgrade_service.py:547`), and the stand-in raises `RehearsalFirmwareError` for `upgradeSiteDevices`, `upgradeDevice`, and `upgradeOrgSsrs` before any call is made.
2. An **autouse** fixture in `conftest.py` blocks `socket.socket.connect` and `socket.create_connection` for the whole package, so the block is not limited to the two tests that count attempts.
3. Every shipped reader receives `session=None`; the org and site identifiers are the obviously fake `...0992` / `...1992`. An escaped call would raise, not dial.
4. `driver.data_root` is redirected to `tmp_path` in every test that starts a run, so no rehearsal writes into the repository.

## Findings

| ID | Finding | Severity |
| - | - | - |
| F1 | SC-001 claims 9 of 9 portal pass conditions. The suite proves 8, and one of those only in part. C1 (refuse the start with no verified pre-check) has no requirement, no test, and no reachable path in the harness. | **HIGH** |
| F2 | FR-027 / US2 scenario 6 / scenario D condition 4: `test_the_router_cancel_travels_the_organization_scope_call` asserts `router_plan().route.scope == "org"` — its own fixture, not the run record. The record never carries a scope because the rehearsal skips submission. | **HIGH** |
| F3 | `plan.md` design decision 5 describes a `StandInSession` object and an `UpgradeSubmitter` double that write the upgrade identifiers into the run record. Neither exists; the harness passes `None` for both. This is the direct cause of F2. | **MEDIUM** |
| F4 | Spec edge case "a statistics read fails for one poll round" is untested. `data-model.md` §4 rule 1 promises a fault answer; no stand-in answer ever leaves status 200. | **MEDIUM** |
| F5 | `spec.md` Key Entities says the stop outcome holds "the unknown list". Shipped `StopOutcome` holds `cancelled`, `already_writing`, `no_cancel_available`, `message`. The unreadable router lands in `already_writing`. Spec is factually wrong about the shipped record. | **MEDIUM** |
| F6 | `contracts/rehearsal-cloud.md` §5 omits `listOrgDevicesStats`, which `upgrade_service.py:1550` really resolves for the SSR org read. Same section claims "the stand-in sets `status_known` to false"; the stand-in returns `StandInResponse([])` and the shipped normalizer derives it. | **MEDIUM** |
| F7 | `data-model.md` drift: `DeviceScript` has 9 fields, not 7 (`uptime_reset_at` and `model` are missing, and drill 2 depends on `uptime_reset_at`); `_calls` is `list[CallRecord]` plus a separate `_counts`, not `dict[str, int]`; §6 names the record field `current_state`, the code writes `state`; §2 rule 3 cites an edge case test using equal versions that does not exist. | **MEDIUM** |
| F8 | `plan.md` project structure lists 6 harness files and 3 test modules. Delivered: 7 and 4 (`errors.py`, `test_rehearsal_support.py`). The Constitution Check row still says "the new package holds 5 modules". | **LOW** |
| F9 | T051 is ticked, but its recorded command fails — the STE linter takes files, not a directory. Per-file runs pass (95–99). | **LOW** |
| F10 | `quickstart.md` §9 grades 6 of the 10 Markdown files; FR-032 covers all. All 10 pass when run. | **LOW** |
| F11 | FR-004 ("the harness holds no copy of any settle or stop rule") has no automated check. It holds today by inspection. | **LOW** |
| F12 | `.spec-context.json` still reads `currentStep: tasks`, `status: ready-to-implement`, and `spec.md` is still `Status: Draft`, although the feature is delivered. | **LOW** |
| F13 | `quickstart.md` §13 held corrupted escape text. **Fixed in this pass.** | LOW (resolved) |

## Is it ready for a pull request?

**Not yet — but it is close, and the gap is narrow and specific.**

The harness is sound. It drives the shipped path, the clock seats are real, the drills assert genuine divergence, the scope guard is airtight, and the budgets are met with room to spare. Nothing here needs redesign.

Two things must change before you open the PR, and neither is large:

1. **Fix F2.** Either give `RunDriverDeps.submit` the double that `plan.md` already specifies, so the run record carries the submission row and the test can read `scope: "org"` out of the record — or amend FR-027 and the quickstart to state plainly that the rehearsal proves the org-scope *call* and that the record field stays a live-run check. The first is better; the second is honest. What you cannot keep is an assertion that reads the test's own fixture while the requirement says "the run record".
2. **Fix F1.** Correct SC-001 to the number the suite actually proves, and say which condition is not proven and why. If C1 matters, add it to the live checklist — the item is under 5 today, so there is room.

F3 through F7 are document corrections that should ride the same commit; each is a sentence or two, and F4 is the only one that may want a small extra test. F8 through F12 are tidying.