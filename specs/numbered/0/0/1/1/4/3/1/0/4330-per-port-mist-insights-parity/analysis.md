# Analysis: Per-port Mist Insights parity in the WAN dashboard

This review checks the spec, plan, and tasks against the remote code on `main`. Each finding cites the remote check ID from `design/research.md`. The local working tree differs from `main` in five files. This review cites no local-only code as proof.

## Consistency Review

| Check | Result | Evidence |
| - | - | - |
| Each FR maps to a task | Pass | FR-001 to FR-017 map to T001 to T011 and the T-gates (plan.md, File-by-File Change Map). |
| Each FR maps to a test | Pass | TC-01 to TC-25 cover FR-001 to FR-017. TC-25 is the change-set review check for FR-015 and FR-016. The mapping appears in the checklist `design/checklists/requirements.md`. |
| Each task names exact paths | Pass | Each task in tasks.md names one or more repository paths. T003 and T011 name new paths. |
| Each task has one verification command | Pass | Each task names one command from the local gates table or one remote check. T-REMOTE-CI and T-MERGE use remote checks because local commands cannot prove CI state. |
| Each directory holds five children or fewer | Pass with recorded debt | `changelog.d/` (R-81) and `tests/e2e/web_portal/` (R-80) are noncompliant parents. This change adds no child to either one. A fragment is a required process record. |
| Sentence limits in the spec and plan | Pass | Each sentence stays at 25 words or fewer, and each instruction at 20 words or fewer. The word count check ran on every record file during self-review. |

## Findings

### A-01 Per-port data has no writer on main (defect, high)

The traffic route and the insight route return cached data only (R-03, R-04). The refresh worker calls no per-port read method (R-06). The live methods `get_traffic`, `get_insights`, and `get_hourly_export` have no caller in the searched code (U-10). The port view therefore shows `unavailable` in production. Action: T005 and T006 add the only writer. The change adds no second writer.

### A-02 Site-scoped reads fail closed under shared admission on main (defect, high)

`RequestLedger._organization` raises when a site path has no organization (R-22). The session setup connects the ledger without an organization (R-25). The shared adapter is enabled for each session when the ledger is enabled (R-24). A per-port call therefore fails before transport. The existing site-scoped live methods have the same problem. The local uncommitted change adds `organization_scope` to fix this (A-11). It is not on `main`. Action: T002, after D-12.

### A-03 Overview copy misstates the counters (defect, medium)

The overview template says RX and TX values show seven-day totals (R-14). The OpenAPI port search says Tx and Rx counters are cumulative since the last device reboot (R-41). Operators can read a reboot counter as a seven-day total. Action: FR-013, T008, and T009.

### A-04 Response key names conflict (conflict, high)

The OpenAPI metric response names `results` and `rt` (R-39). The canonical code and its tests name `timestamps` and named rate arrays (R-31). The `wan_performance` tests name `rt` and named rate arrays (R-32). The source worker reads named rate arrays (R-77 and R-55). The live shape is unverified (U-2). The parser follows the source and the canonical code, and it fails closed on any other shape (D-4, TC-03, TC-04). A live shape check needs owner approval before release.

### A-05 Default page size can truncate the window (risk, high)

The SDK documents a default limit of 100 (R-46). The OpenAPI limit parameter defaults to 100 (R-43). The OpenAPI example pairs interval 3600 with limit 168 (R-40). The source sends no limit (R-56). A 168-sample window can therefore lose samples. The request sets `limit` to 168 and `page` to 1. A `next` value or a short series marks the series partial (FR-003, TC-09).

### A-06 Source replaces missing samples with zero (source defect, not copied, medium)

The source worker uses zero for an index that has no sample (R-61). Zero is a measured value in the dashboard and is not a missing value. The product keeps missing samples absent (FR-011, TC-08).

### A-07 Source uses direct HTTP (source defect, not copied, high)

The source worker uses a direct HTTP client with a built URL (R-57). The constitution forbids direct HTTP when a working mistapi method exists (R-69). The product uses the SDK method only (FR-006).

### A-08 Raw VPN peer path (existing debt, medium)

The peer insight module builds a raw path and sends it through the session transport (R-28). The SDK has no method for that path (R-50). The org-level VPN peer count path exists in the SDK (R-63). Its path differs from the per-device path, and it is not verified as equivalent. This debt has a separate issue. This change does not touch the module.

### A-09 Gateway insight collector omits the port (existing debt, medium)

The `wan_performance` gateway insight request omits `port_id` (R-26). Its result sets `port_id` to None (R-27). Local search finds no portal import of that collector outside its package (U-10). This change does not use that collector.

### A-10 Pull request #4208 overlaps this change (coordination, high)

Pull request #4208 is an open draft. Its head changes `request_admission.py` (R-51). It deletes the legacy snapshot test path (R-52). It changes `snapshot_client.py` (R-53). It also changes `deploy/.env.example` by seven lines (gh output). This change edits `request_admission.py` and `deploy/.env.example`. The admission edit waits for D-12.

### A-11 Local uncommitted changes differ from main (coordination, high)

`git status` lists five modified files: `logger_utils.py`, `request_admission.py`, the subscription expiry client, and two test files. The local `request_admission.py` differs from the committed version and adds `organization_scope`. The committed version has no such scope (R-23). The spec cites `main` only. The owner reviews the local change before T002.

### A-12 Output backend debt (constitution debt, medium)

The constitution requires data collection and export operations to use `DataExporter.write_with_format_selection()` (R-70). The WAN worker writes Redis, not an export. The portal CSV exports predate that rule (U-10). This change adds no export. A separate issue records the remediation.

### A-13 Worker method exceeds the function limit (structure debt, medium)

`collect_worker_snapshot` starts at line 502 (R-62) and returns at line 557 (R-73). It holds four reads, page callbacks, and a shaping step. It exceeds the 25-line limit in the constitution (R-79). This change reads its datasets through the worker and does not widen the method. A separate issue records the remediation.

### A-14 Browser test folder is noncompliant (structure debt, low)

`tests/e2e/web_portal/` has 32 direct children (R-80). The browser tests extend an existing file in that folder. No new child is added.

### A-15 Changelog folder is noncompliant (structure debt, low)

`changelog.d/` has 335 direct children (R-81). The fragment is one required process record, as the constitution allows.

### A-16 Documentation gaps (documentation gap, medium)

The environment example has no WAN dashboard setting (R-35). The operator guide has no WAN dashboard section (R-36). T007 and T010 close both gaps for the new setting and the new behavior. The existing `WAN_DASHBOARD_*` settings stay undocumented in the example. A separate issue records that gap.

### A-17 Issue 4224 and its record (context, low)

Issue #4224 is open and concerns the Mist Cisco config converter (gh output). No 4224 record exists in the spec drafts. The spec reuses no context from issue #4224.

### A-18 Issue 4634 context (context, low)

The 4634 summary in the spec drafts describes a contract evidence record. The 4634 record folder is absent on `main` (R-60). The spec reuses its evidence style only.

### A-19 Dependency on issue 4220 (dependency, low)

Issue #4220 closed on 2026-10-20 (gh output). Its follow-up pull requests #4332 and #4364 merged on 2026-10-20 (gh output). The dependency is satisfied.

### A-20 Issue comment line range (verified, low)

The issue cites `snapshot_client.py` lines 267 to 310. The class starts at line 267 (R-26). Line 310 returns `port_id` as None (R-27). The citation is correct.

### A-21 Rate limit text (verified, low)

The issue says the current Mist documentation states 5,000 calls per hour for each token. The local OpenAPI file states the same figure (R-42). The live upstream page is unverified (U-8).

### A-22 SDK retry multiplier (risk, medium)

The SDK retries HTTP 429 three times by default, so one logical call can make four attempts (R-49). The runner clone sets the retry count to zero (R-11). A direct SDK call outside the runner would not have that protection. Every port series call uses the runner.

### A-23 Source totals are not comparable (unverified, medium)

The source derives totals from hourly rates (R-55). The Mist port counters are cumulative since reboot (R-41). The two totals measure different things. The product labels its seven-day totals as derived from hourly samples (FR-010). Whether source totals match production totals is unverified (U-5).

## Requirement Coverage for Issue Acceptance Criteria

| Issue acceptance criterion | Where the spec covers it |
| - | - |
| Source-specific per-port behavior and provenance are documented | research.md, sources, R-54 to R-59, D-11 |
| SDK request and response contract is verified | R-37 to R-46, TC-01 to TC-06, D-3, D-4 |
| Bounded request budget for the production site, gateway, and port bands | D-8, plan.md Risks, U-1, SC-005 |
| Shared Mist session and admission path, no direct HTTP | FR-006, D-7, TC-13, TC-14 |
| Canonical worker and cache, no duplicate collection | D-1, D-2, FR-004, TC-15 |
| Mocked tests for valid, malformed, rate-limited, and failed responses | TC-03 to TC-06, TC-16, TC-22 |
| No second portal, cache writer, database, service, or published port | FR-015, plan.md File-by-File Change Map |

## Unresolved Items

- U-1: Production counts. The owner must provide an authorized production scope or keep the budget unmeasured.
- U-2: The live response key names. The owner must approve a live shape check.
- D-11: The attribution text for the source license needs human approval.
- D-14: Production enablement needs human approval after measured counts exist.
- A-10 and A-11: The owner decides the order of the admission edit.
