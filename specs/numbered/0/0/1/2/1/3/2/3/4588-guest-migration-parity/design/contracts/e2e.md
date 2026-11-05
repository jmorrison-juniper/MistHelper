# Original-versus-target E2E acceptance

## Evidence classes

Source template inspection proves declared controls and code paths.
Fresh source screenshots prove rendering with synthetic fixtures.
Source offline tests prove mocked route behavior under the target environment.
None of these proves live cloud semantics or target visual equivalence.

The current target guest UI is absent.
All target screenshot, browser workflow, and migration runtime acceptance remains **UNVERIFIED**.
The current offline projection has executed evidence under TEST-029 only.

## Deterministic paired setup

Use the pinned source and target commits for each comparison report.
Record browser version, operating system, font set, scale 1, fixture digest, mock version, locale, timezone, and theme.
Freeze the observation clock at `2030-01-01T00:00:00Z` for future paired fixtures.
Use UTC and `en-US`.
Do not use production credentials, client identifiers, or a live Mist request.

Render both interfaces with the same synthetic organization, two sites, duplicate-name variants, applicable site/org WLANs, and client records.
Include active, near-expiry, expired, unauthorized, unknown, empty, denied, and failed response fixtures.
Use fictitious MACs starting with `02`, `example.invalid` addresses, and documentation IP ranges.
Permit only local browser assets and deterministic mocked responses.
Fail on any attempted live SDK construction or unlisted outbound request.
Persist request counts, status assertions, console errors, screenshot hashes, and Playwright traces.

Use viewports 1440x1080, 1024x768, and 390x844.
The source theme is dark magenta. D5 selects the target paired theme and approved shell differences.
Exercise supported additional target themes for accessibility, not as source parity claims.
Disable finite animation and wait for fonts, layout, and data readiness before future baseline capture.
Fresh planning captures waited for animations and fonts but were not created as frozen-clock pixel baselines.

## Paired screenshot scenario matrix

Each row requires source reference and target capture, interaction assertions, and reviewer disposition.
Do not substitute a template or a mockup for an actual target screenshot.

| Pair ID | Scenario and fixture/state | Assertions and comparison regions |
| --- | --- | --- |
| VIS-001 | Initial unavailable, testing, connected, and failed connection | Header state, disabled selectors/actions, safe error text. |
| VIS-002 | Site name/address filter, no match, selected site | Selector order, placeholders, exact scope, keyboard behavior. |
| VIS-003 | Site/org WLANs, duplicate SSID, no-portal, denied discovery | Org labels, banner/help/link, no scope expansion. |
| VIS-004 | Mixed authorization list and statistics | Card order, totals, badges, detail hierarchy, unknown deviations. |
| VIS-005 | Guest details and filtered/no-match/true-empty lists | Search behavior, privacy, empty states, long and escaped values. |
| VIS-006 | Blank and filled add dialogs | Three-column relationships, fields, presets, focus and errors. |
| VIS-007 | Client search short/loading/results/empty/failed | MAC/hostname/IP/SSID matching, selection, panel scrolling. |
| VIS-008 | Edit details and extension | Fixed MAC, fields, duration explanation, read-only deviations. |
| VIS-009 | Confirmed/canceled/wrong/stale grant/edit/extend/revoke | Exact scope summary, typed word, no-write negative cases. Source lacks confirmation, so mark an approved difference. |
| VIS-010 | Write rejection/rate limit/timeout/unknown/audit failure | Truthful results and persistent actionable errors. |
| VIS-011 | CSV dialog, download, upload, one-row and six-row preview | Ten headers, aliases, first-five preview, full row accounting, table overflow. |
| VIS-012 | CSV malformed/duplicate/ambiguous/oversize/changed file | Row errors, limits, scope resolution, disabled dispatch. |
| VIS-013 | Batch progress/full success/partial/all rejected/unknown/canceled | Per-row accounting, progress, errors, recovery, no replay. |
| VIS-014 | Scope switch during request/dialog/batch and browser restart | Invalidated controls, stale result rejection, approved restart recovery. |
| VIS-015 | Keyboard, reduced motion, narrow layouts, long content | Focus order, labels, announcements, contrast, noncolor status, reachable controls. |

Run all 15 scenario families at the three declared viewports when their controls are present.
Modal and table captures may add cropped content regions, but retain full screenshots for review.
Do not crop away an error, navigation, confirmation, or overflow defect.

## Stable selector contract

Use semantic roles and labels, backed by stable `data-testid` identifiers.
Planned selectors include `guest-tab`, `guest-scope`, `guest-connection`, `guest-site-search`,
`guest-site-select`, `guest-wlan-select`, `guest-add`, `guest-import`, `guest-refresh`,
`guest-total`, `guest-active`, `guest-expiring`, `guest-expired`, `guest-unknown`,
`guest-search`, `guest-record`, `guest-add-dialog`, `guest-edit-dialog`, `guest-client-search`,
`guest-client-result`, `guest-duration`, `guest-preset`, `guest-confirmation`,
`guest-confirm-word`, `guest-result`, `guest-csv-download`, `guest-csv-file`,
`guest-csv-preview`, `guest-csv-row`, `guest-batch-progress`, and `guest-batch-outcome`.
Use opaque row references, not full MACs or names, in selectors.
Add distinct stable selectors for each field, cancel, close, and confirmed submit control.
Tests must verify selector uniqueness, accessible names, focus, Escape/cancel behavior, and disabled states.

## Acceptance families

All families are future acceptance contracts unless explicitly marked executed.
Unit, contract, integration, and browser evidence must cover each relevant family, including its failure variants.

| Test ID | Observable acceptance and negative cases | Paired scenarios |
| --- | --- | --- |
| TEST-001 | Existing portal navigation reaches only registered guest routes and preserves other pages. | VIS-001 |
| TEST-002 | Connection states are truthful. Missing credentials and multiple organizations never select a scope automatically. | VIS-001 |
| TEST-003 | Applicable enabled portal WLANs, templates, groups, duplicate names, denied reads, and failed pages are correct. | VIS-002, VIS-003 |
| TEST-004 | Site name/address filtering and scope switches invalidate every dependent state and late response. | VIS-002, VIS-014 |
| TEST-005 | Exact-scope list, stable sorting, record opening, pagination, and malformed responses preserve data meaning. | VIS-004, VIS-005 |
| TEST-006 | Known/unknown status, counters, time thresholds, expiry boundaries, and UTC conversion are accurate. | VIS-004 |
| TEST-007 | Every approved guest field is searchable without exposing unapproved data in HTML, JSON, selectors, or logs. | VIS-005 |
| TEST-008 | MAC/hostname/IP/SSID client searches, short input, debounce, race, keyboard selection, and empty/failure states pass. | VIS-007 |
| TEST-009 | Add field validation, client entry, cancel, confirmed dispatch, missing MAC, escaped text, and failures pass. | VIS-006, VIS-009 |
| TEST-010 | Company/custom/sponsor/creator fields retain approved semantics and cannot accept forged actor attribution. | VIS-005, VIS-006, VIS-008 |
| TEST-011 | Every preset and integer boundary passes or rejects explicitly. Invalid input never silently becomes one day. | VIS-006, VIS-008 |
| TEST-012 | Edit MAC stays fixed. Read-only fields send no write. Detail-only edits do not implicitly extend. | VIS-008, VIS-009 |
| TEST-013 | Extension uses the verified duration origin and authoritative outcome. Stale observation prevents dispatch. | VIS-008, VIS-009 |
| TEST-014 | Verified revoke, cancel, denied response, timeout, ineffective 200, and unknown observation remain distinct. | VIS-009, VIS-010 |
| TEST-015 | CSV headers, two fictional examples, aliases, duration, and download MIME/disposition are exact. | VIS-011 |
| TEST-016 | Quoted commas, doubled quotes, newlines, BOM/CRLF, malformed rows, unknown headers, and six-row preview account for every row. | VIS-011, VIS-012 |
| TEST-017 | Scope map revision, duplicate names, equal SSIDs, unauthorized rows, and stale assignments cannot select a wrong target. | VIS-012, VIS-014 |
| TEST-018 | Approved byte/row/field/request bounds at limit-1, limit, and limit+1. Approved duplicate policy and formula handling pass. | VIS-012 |
| TEST-019 | Batch full/partial/all-failed/unknown/unstarted outcomes partition every row. Restart and cancel never replay ambiguous rows. | VIS-013, VIS-014 |
| TEST-020 | D1-approved access checks, missing identity, denied scope, forged headers, and CSRF failures send zero writes. | VIS-001, VIS-009 |
| TEST-021 | Typed confirmation binds actor/action/scope/payload/revision. Wrong/canceled/reused/stale confirmations send zero writes. | VIS-009, VIS-014 |
| TEST-022 | Explicit SDK signatures, exact-site scope, supported payloads, 4xx/429/5xx, SDK retries, no org/direct HTTP fallback pass. | VIS-003, VIS-010 |
| TEST-023 | Reads and writes distinguish unavailable, rejected, rate limited, malformed, unknown, and successful results. No invented expiry. | VIS-010 |
| TEST-024 | Durable intent/outcome, audit failures before/after dispatch, retention, redaction, restart, and reconciliation follow D4. | VIS-010, VIS-014 |
| TEST-025 | Existing store isolation, transactions, backup shape, scoped keys, and no duplicate database/Redis/Compose service pass. | VIS-014 |
| TEST-026 | Existing dependency/session/configuration/local asset reuse works without downgrade or duplicate credentials. | VIS-001, VIS-015 |
| TEST-027 | All paired screenshots pass approved difference rules or stop release for explicit review. | VIS-001 through VIS-015 |
| TEST-028 | Keyboard, labels, focus trapping/restoration, live status, contrast, reduced motion, and responsive reachability pass. | VIS-015 |
| TEST-029 | Current exact three-key offline projection, masking, nonmutation, and invalid/unknown inputs pass. Executed: 22 existing tests. | No current target guest UI |
| TEST-030 | All inventory rows and requirements map to executed acceptance before release. No skipped or stale result counts as proof. | All |
| TEST-031 | Operator docs, supported fields, cutover, recovery, unknown outcome response, and approval procedure match delivered behavior. | VIS-010, VIS-014 |
| TEST-032 | Approved reuse retains source attribution, license/change notices, noncommercial, and share-alike obligations. | Reviewer record |
| TEST-033 | Initial/loading/empty/canceled/error/stale states and button/dialog resets are complete. | VIS-001 through VIS-014 |
| TEST-034 | Notification stays off unless D6 and verified support approve a visible workflow. | VIS-006 |
| TEST-035 | Existing app health, services, other pages, shutdown/restart, target required checks, and release ownership remain intact. | VIS-014, VIS-015 |

## Difference and regression acceptance

D5 must approve the comparator tolerance and excluded chrome regions before baseline acceptance.
No numeric pixel tolerance is invented here.
Preserve the source content hierarchy and relationships unless a row records an approved deviation.
Compare state semantics and text independently of pixel results.
Require accessible names, labels, keyboard actions, focus restoration, and status announcements for every interactive surface.
Use the existing browser tooling. Add an accessibility scanner only through a reviewed dependency change if existing assertions are insufficient.

Record each difference with inventory ID, reason, screenshot pair, approver, date, and affected tests.
Safety deviations include exact scope, typed confirmation, unknown status, unsupported fields, escaped text, and improved accessibility.
A safety objective does not authorize arbitrary visual redesign.
Every unrelated portal workflow must retain its existing regression tests.
Fail on browser console errors, unmocked requests, missing selectors, broken layout, and incomplete result accounting.
Keep failed-flow screenshots and traces as CI artifacts with approved retention and privacy.

## Final original-versus-target review

T038 compares every inventory row against the pinned original and implemented target.
T039 rehearses cutover and recovery using offline and isolated evidence.
T040 requires operator approval of functional, visual, scope, privacy, and recovery acceptance.
Unresolved decisions, skipped tests, missing screenshots, stale commits, or unknown production effects prevent approval.
No source screenshot or successful mock call proves the full migration is implemented.
