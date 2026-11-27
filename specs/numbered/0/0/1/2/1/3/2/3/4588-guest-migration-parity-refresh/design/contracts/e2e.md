# Source-to-target acceptance (E2E contract)

## Evidence classes

- Source template and script inspection proves the declared controls and code paths (S03, S01, S02).
- The planning run did not render the source or the target. No screenshot exists for this record.
- Source offline tests exist (S11). This run did not run them.
- No evidence in this record proves live cloud behavior or target visual equivalence.

The current target guest UI does not exist. Target screenshot, browser, and migration runtime acceptance is **UNVERIFIED**. The current offline projection has executed evidence under TEST-029 only.

## Deterministic paired setup

- Use the pinned source commit and the target commit for each comparison report.
- Record the browser version, operating system, font set, scale factor, fixture digest, mock version, locale, time zone, and theme.
- Freeze the observation clock at `2030-01-01T00:00:00Z`. Use UTC and `en-US`.
- Use no production credential, no client identifier, and no live Mist request.
- Use fictitious MAC addresses that start with `02`. Use `example.invalid` addresses and documentation IP ranges.
- Permit only local browser assets and deterministic mocked responses.
- Fail on any live SDK construction or any unlisted outbound request.
- Keep request counts, status assertions, console errors, screenshot hashes, and traces.

## Viewports and theme

- Use three viewports: 1440 by 1080, 1024 by 768, and 390 by 844.
- The source theme is dark magenta (S03 L10 to L25). The target theme is the portal magenta theme (T05 L80 to L81). D-13 approves each deviation.
- Wait for fonts and layout before each capture. Disable finite animation.

## Paired scenario matrix

Each row needs a source reference, a target capture, an interaction assertion, and a reviewer disposition.

| Pair ID | Scenario and fixture | Assertions and comparison regions |
| --- | --- | --- |
| VIS-001 | Initial, testing, connected, and failed connection states | Header state, disabled selectors and actions, safe error text. |
| VIS-002 | Site name and address filter, no match, and selected site | Selector order, placeholders, exact scope, and keyboard behavior. |
| VIS-003 | Site and organization WLANs, duplicate SSIDs, no portal WLAN, and denied discovery | Organization label, banner, help text, and no scope expansion. |
| VIS-004 | Mixed authorization list and statistics | Card order, totals, badges, and detail hierarchy. |
| VIS-005 | Guest details, filtered results, no-match results, and true-empty results | Search behavior, privacy, empty states, and long or escaped values. |
| VIS-006 | Blank and filled add dialogs | Region relationships, fields, presets, focus, and errors. |
| VIS-007 | Client search in short, loading, result, empty, and failed states | Field matching, selection, and panel scrolling. |
| VIS-008 | Edit details and extension | Fixed MAC, fields, duration explanation, and read-only deviations. |
| VIS-009 | Confirmed, canceled, wrong, and stale grant, edit, extension, and revoke | Scope summary, typed word, and zero-write negative cases. |
| VIS-010 | Rejection, rate limit, timeout, unknown outcome, and audit failure | Truthful results and actionable errors that persist. |
| VIS-011 | CSV dialog, template download, file upload, one-row preview, and six-row preview | Ten headers, aliases, first-five preview, and full row accounting. |
| VIS-012 | Malformed, duplicate, ambiguous, oversize, and changed CSV files | Row errors, limits, scope resolution, and disabled dispatch. |
| VIS-013 | Batch progress, full success, partial success, all rejected, unknown, and canceled | Per-row accounting, progress, errors, and no replay. |
| VIS-014 | Scope switch during a request, a dialog, or a batch, and browser restart | Invalidated controls, rejected stale results, and approved recovery. |
| VIS-015 | Keyboard use, reduced motion, narrow layouts, and long content | Focus order, labels, announcements, contrast, noncolor status, and reachable controls. |

Run all 15 families at the three viewports when their controls exist. Keep full screenshots for review. Do not crop away an error, a navigation item, a confirmation, or an overflow defect.

## Stable selector contract

Use semantic roles and labels. Back them with stable `data-testid` values. Planned values for the page are `guest-tab`, `guest-scope`, `guest-connection`, `guest-site-search`, `guest-site-select`, `guest-wlan-select`, `guest-add`, `guest-import`, `guest-refresh`, `guest-total`, `guest-active`, `guest-expiring`, `guest-expired`, `guest-unknown`, and `guest-search`. Planned values for record and dialog flows are `guest-record`, `guest-add-dialog`, `guest-edit-dialog`, `guest-client-search`, `guest-client-result`, `guest-duration`, `guest-preset`, `guest-confirmation`, `guest-confirm-word`, and `guest-result`. Planned values for imports and batches are `guest-csv-download`, `guest-csv-file`, `guest-csv-preview`, `guest-csv-row`, `guest-batch-progress`, and `guest-batch-outcome`.

Use opaque row references in selectors, not full MAC addresses or names. Each selector must be unique.

## Acceptance families

| Test ID | Observable acceptance and negative cases | Paired scenarios |
| --- | --- | --- |
| TEST-001 | Portal navigation reaches only registered guest routes and keeps the other pages. | VIS-001 |
| TEST-002 | Connection states are truthful. Missing credentials and several organizations never select a scope automatically. | VIS-001 |
| TEST-003 | Applicable enabled WLANs, templates, groups, duplicate names, denied reads, and failed pages are correct. | VIS-002, VIS-003 |
| TEST-004 | Site filtering and scope switches invalidate every dependent state and every late response. | VIS-002, VIS-014 |
| TEST-005 | The exact-scope list, stable sort, record opening, and malformed responses keep their meaning. | VIS-004, VIS-005 |
| TEST-006 | Known and unknown status, counts, time thresholds, expiry boundaries, and UTC conversion are accurate. | VIS-004 |
| TEST-007 | Each approved field is searchable without exposing unapproved data in HTML, JSON, selectors, or logs. | VIS-005 |
| TEST-008 | Client searches for MAC, hostname, IP, and SSID handle short input, debounce, races, keyboard selection, and failures. | VIS-007 |
| TEST-009 | Add validation, client entry, cancel, confirmed dispatch, missing MAC, escaped text, and failures pass. | VIS-006, VIS-009 |
| TEST-010 | Company, custom, sponsor, and creator fields keep approved meaning. Client text cannot forge the actor. | VIS-005, VIS-006, VIS-008 |
| TEST-011 | Each preset and each integer boundary passes or rejects explicitly. An invalid value never becomes one day. | VIS-006, VIS-008 |
| TEST-012 | The edit MAC stays fixed. Read-only fields send nothing. A detail-only edit does not extend access. | VIS-008, VIS-009 |
| TEST-013 | An extension uses the verified duration origin and the observed outcome. A stale observation blocks dispatch. | VIS-008, VIS-009 |
| TEST-014 | A verified revoke, cancel, denial, timeout, ineffective 2xx response, and unknown observation stay distinct. | VIS-009, VIS-010 |
| TEST-015 | CSV headers, two fictional examples, aliases, duration, and the download type are exact. | VIS-011 |
| TEST-016 | Quoted commas, doubled quotes, newlines, BOM and CRLF, malformed rows, unknown headers, and the preview account for every row. | VIS-011, VIS-012 |
| TEST-017 | A scope map revision, duplicate names, equal SSIDs, unauthorized rows, and stale assignments cannot select a wrong target. | VIS-012, VIS-014 |
| TEST-018 | D-11 bounds pass at limit minus one, limit, and limit plus one. The duplicate rule and formula handling pass. | VIS-012 |
| TEST-019 | Full, partial, all-failed, unknown, and unstarted batch outcomes partition every row. Restart and cancel never replay an ambiguous row. | VIS-013, VIS-014 |
| TEST-020 | Access checks, missing identity, denied scope, forged headers, and CSRF failures send zero writes. | VIS-001, VIS-009 |
| TEST-021 | The typed word binds actor, action, scope, payload, and revision. Wrong, canceled, reused, and stale confirmations send zero writes. | VIS-009, VIS-014 |
| TEST-022 | Explicit SDK signatures, exact-site scope, supported payloads, 4xx, 429, and 5xx responses, SDK retries, and no organization fallback pass. | VIS-003, VIS-010 |
| TEST-023 | Reads and writes separate unavailable, rejected, rate-limited, malformed, unknown, and successful results. No expiry is invented. | VIS-010 |
| TEST-024 | Durable intent and outcome records, audit failures before and after dispatch, retention, redaction, restart, and reconciliation follow D-12. | VIS-010, VIS-014 |
| TEST-025 | Store isolation, transactions, backup shape, scoped keys, and no added database, Redis service, or Compose service pass. | VIS-014 |
| TEST-026 | Existing dependencies, session, configuration, and local assets are reused without downgrade or a second credential. | VIS-001, VIS-015 |
| TEST-027 | Every paired screenshot passes the approved difference rules, or the release stops for review. | VIS-001 to VIS-015 |
| TEST-028 | Keyboard use, labels, focus trapping and restoration, live status, contrast, reduced motion, and responsive reachability pass. | VIS-015 |
| TEST-029 | The exact three-key offline projection, masking, nonmutation, and invalid input pass. Existing: 22 cases in the repository. This run did not execute them. | No target guest UI yet |
| TEST-030 | Every inventory row and requirement maps to executed acceptance before release. Skipped or stale results do not count. | All |
| TEST-031 | Operator documents, supported fields, cutover, recovery, unknown outcome response, and approval match the delivered behavior. | VIS-010, VIS-014 |
| TEST-032 | Approved reuse keeps source credit, license and change notices, noncommercial terms, and share-alike terms. | Reviewer record |
| TEST-033 | Initial, loading, empty, canceled, error, and stale states reset every button and dialog. | VIS-001 to VIS-014 |
| TEST-034 | Notification stays off unless D-10 changes with verified support. | VIS-006 |
| TEST-035 | Existing app health, services, other pages, shutdown and restart, required status names, and release ownership stay intact. | VIS-014, VIS-015 |

## Difference and regression acceptance

- The reviewer approves the comparator tolerance and the excluded chrome regions before baseline acceptance.
- No numeric pixel tolerance appears in this record. The planning run did not measure one.
- Compare state semantics and text separately from pixel results.
- Require accessible names, labels, keyboard actions, focus restoration, and status announcements for each interactive surface.
- Record each difference with its inventory ID, reason, screenshot pair, approver, date, and affected tests.
- Fail on browser console errors, unmocked requests, missing selectors, broken layout, and incomplete result accounting.

Warning: a visual approval that hides a safety defect can allow a wrong write. Review the safety rows separately from the style rows.

## Final original-versus-target review

- Task T038 compares every inventory row against the pinned source and the implemented target.
- Task T039 rehearses cutover and recovery with isolated evidence.
- Task T040 requires operator approval of functional, visual, scope, privacy, and recovery acceptance.
- Unresolved decisions, skipped tests, missing screenshots, stale commits, or unknown production effects prevent approval.
