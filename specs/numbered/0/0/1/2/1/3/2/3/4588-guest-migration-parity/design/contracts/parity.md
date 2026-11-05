# Source-to-target parity inventory

Evidence IDs link to immutable paths in [research](../research.md#immutable-evidence-index).
M01 is the existing offline projection. M03-M07 are reusable infrastructure, not implemented guest workflows.
Every `TEST-nnn` names an acceptance family in [E2E](e2e.md#acceptance-families).
Task IDs refer to [tasks](../../tasks.md).

Status values describe current target guest functionality.
**Existing** means the current target implements that contract.
**Missing** means future work remains, even when a reusable helper exists.
**Intentional deviation** excludes unsupported or unsafe source behavior.
**Decision required** means an explicit approval or contract gate controls the final behavior.

## Page, controls, and appearance

| ID | Source feature and evidence | Current target disposition | Requirement | Tasks | Test | Acceptance evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P001 | One root dashboard, S01 L86-L90 | Missing, M03/M04 have no guest page | FR-001 | T010,T011 | TEST-001 | Guest tab reaches the shared page and marks the active scope. |
| P002 | Header title, WiFi icon, magenta gradient, S07/S08 | Decision required, target chrome differs | FR-027 | T006,T034 | TEST-027 | Approve paired header and content-region screenshots. |
| P003 | Test Connection, automatic page-load test, status dot and organization text, S08/S13 | Missing | FR-002 | T012 | TEST-002 | Offline unavailable, testing, connected, and failure states are distinct. |
| P004 | Three equal site/WLAN/action columns, S08 | Missing | FR-027 | T011,T034 | TEST-027 | Desktop regions retain order and relative hierarchy. |
| P005 | Site search input, name/address substring filter, S08/S11 | Missing | FR-004 | T012 | TEST-004 | Both fields filter without losing valid scope silently. |
| P006 | Disabled site selector and placeholder options, S08/S11 | Missing | FR-003,FR-033 | T012 | TEST-003 | Loading, unavailable, no-site, and selected options have assertions. |
| P007 | WLAN selector and guest-only help, S08/S11 | Missing | FR-003 | T012 | TEST-003 | Only enabled applicable portal WLANs appear. |
| P008 | `(Org)` option label, sorted SSIDs, S04/S11 | Missing | FR-003 | T012 | TEST-003 | Org assignment and equal-SSID fixtures resolve by IDs. |
| P009 | Add, Bulk Import CSV, Refresh Guest List buttons, S08/S13 | Missing | FR-009,FR-019,FR-033 | T014,T017,T027 | TEST-009,TEST-019,TEST-033 | Enabled states follow verified scope and access. |
| P010 | Four total/active/expiring/expired statistic cards, S08/S13 | Missing | FR-006 | T014 | TEST-006 | Counts match authoritative fixtures, including unknown observations. |
| P011 | Guest section header and search field, S08/S11 | Missing | FR-005,FR-007 | T014 | TEST-005,TEST-007 | Filtering preserves full-list totals and permitted detail access. |
| P012 | Clickable guest card opens edit, S11/S13 | Missing | FR-005,FR-028 | T014,T022,T034 | TEST-005,TEST-028 | Mouse and keyboard open the same exact record. |
| P013 | MAC/name/email/company row and custom detail row, S11 | Decision required, M01 exposes no personal fields | FR-007,FR-010 | T002,T014 | TEST-007,TEST-010 | D1 controls fields and privacy assertions. |
| P014 | Active/expired pills and green/yellow/red time badges, S07/S11 | Missing | FR-006,FR-028 | T014,T034 | TEST-006,TEST-028 | Text and noncolor cues preserve status at boundaries. |
| P015 | Card hover border/lift, rounded corners, shadows, S07 | Decision required | FR-027 | T006,T034 | TEST-027 | Approve content style and reduced-motion deviation. |
| P016 | Welcome and no-guest illustrations/help, S08 | Missing | FR-033 | T014 | TEST-033 | Initial, true-empty, filtered-empty, and unavailable states differ. |
| P017 | Red no-portal banner, dismiss control, Mist Dashboard link, S08/S11 | Missing | FR-003,FR-023 | T012,T029 | TEST-003,TEST-023 | Configuration absence differs from denied or failed discovery. |
| P018 | Success/error/warning toasts with icons, close, timed dismissal, S07/S12 | Missing | FR-023,FR-028 | T029,T034 | TEST-023,TEST-028 | Announce safe messages and retain actionable failure information. |
| P019 | Dark inputs, magenta focus, monospace MAC, uppercase labels, S07 | Decision required | FR-027,FR-028 | T006,T034 | TEST-027,TEST-028 | Paired styling and focus checks cover contrast and long values. |
| P020 | Tablet and phone breakpoints at 768/1400 and 767, S07 | Missing | FR-028 | T034 | TEST-028 | 1440x1080, 1024x768, and 390x844 retain reachable controls. |

## Single-guest workflows

| ID | Source feature and evidence | Current target disposition | Requirement | Tasks | Test | Acceptance evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P021 | Extra-large add dialog, device/details/clients columns, S09 | Missing | FR-009,FR-027 | T017,T034 | TEST-009,TEST-027 | Blank and filled paired screenshots preserve relationships. |
| P022 | Required MAC input and format help, S09; dotted MAC helper, S05/S20 | Decision required for supported format set | FR-009,FR-022 | T003,T016,T017 | TEST-009,TEST-022 | Strict normalization tests include colon, hyphen, bare, dotted, mixed, and invalid forms. |
| P023 | Guest name and email inputs, S09 | Decision required, schema name is read-only | FR-009,FR-012 | T003,T017,T022 | TEST-009,TEST-012 | Unsupported edits are explained and send no field. |
| P024 | Company, field1, field2, sponsor email inputs, S09 | Missing, subject to D1/D2 | FR-010 | T017,T022 | TEST-010 | Optional values and empty-field edits obey the approved schema. |
| P025 | Hidden field4 replaced by token name server-side, S05/S09 | Decision required, token name is not operator identity | FR-010,FR-024 | T005,T017,T030 | TEST-010,TEST-024 | Creator attribution follows approved actor policy, never client text. |
| P026 | Duration minutes, default 1440, S09/S13 | Missing | FR-011 | T016,T017 | TEST-011 | Empty, zero, negative, noninteger, and boundary values are explicit. |
| P027 | Ten add/edit presets: 60,480,1440,2880,4320,10080,43200,129600,262800,525600, S09 | Intentional deviation for values above 259200 unless verified | FR-011 | T003,T016,T022 | TEST-011 | Every preset has a supported value or disabled explanation. |
| P028 | Source five-year maximum and unbounded edit maximum, S09/S19 | Intentional deviation | FR-011 | T003,T016 | TEST-011 | No five-year promise or silent clamping exists. |
| P029 | Client MAC/hostname/IP/SSID search, two-character minimum, 300ms debounce, S06/S13 | Missing | FR-008 | T019,T020 | TEST-008 | Every search field, short input, delayed result, failure, and no-match state passes. |
| P030 | Client result MAC, hostname, SSID, IP, scrolling panel, S09/S13 | Decision required for disclosed detail fields | FR-008,FR-028 | T002,T020,T034 | TEST-008,TEST-028 | D1 limits fields and keyboard selection fills the correct device. |
| P031 | Selected client fills MAC and hostname/name, S13 | Decision required for writable name | FR-008,FR-012 | T003,T020 | TEST-008,TEST-012 | Prefill never sends a read-only field. |
| P032 | Cancel, close, authorize spinner, form reset, list refresh, S09/S13 | Missing | FR-009,FR-033 | T017,T021 | TEST-009,TEST-033 | Cancellation sends no write and confirmed results refresh exact scope. |
| P033 | Large two-column edit dialog with disabled MAC, S09/S13 | Missing | FR-012,FR-027 | T022,T034 | TEST-012,TEST-027 | MAC stays fixed and permitted fields load accurately. |
| P034 | Edit detail fields and default extension duration, S09/S13 | Decision required | FR-012,FR-013 | T003,T022 | TEST-012,TEST-013 | Detail-only change does not silently extend by one day. |
| P035 | Update button, spinner, toast, refresh, S13 | Missing | FR-012,FR-033 | T022,T024 | TEST-012,TEST-033 | Exactly one verified update occurs after fresh confirmation. |
| P036 | Revoke Access button in edit footer, S09/S13 | Missing | FR-014 | T023,T024 | TEST-014 | Cancel, deny, confirmed revoke, failed revoke, and unknown outcome remain distinct. |
| P037 | Source `minutes=0` revocation and guide DELETE claim, S05/S19 | Decision required | FR-014,FR-022 | T003,T023 | TEST-014,TEST-022 | Schema-valid zero is not accepted as proven removal. |
| P038 | Backend-only `notify`, absent from form, S01/S05 | Decision required | FR-034 | T003,T006,T017 | TEST-034 | Default sends no notification and approved support has its own acceptance. |

## CSV and shared state

| ID | Source feature and evidence | Current target disposition | Requirement | Tasks | Test | Acceptance evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P039 | Import modal instructions, two step cards, close controls, S10 | Missing | FR-019,FR-027 | T027,T034 | TEST-019,TEST-027 | Paired import views preserve order and keyboard dismissal. |
| P040 | Example CSV download and two sample rows, S02/S12 | Missing | FR-015 | T025,T027 | TEST-015 | Ten source headers are accounted for and examples use fictional data. |
| P041 | File picker `.csv`, local read and reset on close, S10/S12 | Missing | FR-016,FR-033 | T025,T027 | TEST-016,TEST-033 | Invalid type, empty file, cancel, replacement, and reopen states pass. |
| P042 | First-five-row preview, header row, total count, 200px scroll table, S10/S12 | Missing | FR-016 | T025,T027 | TEST-016 | More than five rows retain complete accounting outside the bounded visual preview. |
| P043 | Simple CSV quote parser, silently skipped short rows, S12 | Intentional deviation | FR-016 | T025,T026 | TEST-016 | Robust syntax handling rejects or reports every malformed row. |
| P044 | Case-insensitive site/SSID lookup map, S02/S12 | Missing | FR-017 | T026,T027 | TEST-017 | Duplicate names require explicit ID selection, not last-entry wins. |
| P045 | Sponsor header alias `field3_sponsor_email` or `field3`, S02/S12 | Missing | FR-015,FR-016 | T025 | TEST-015,TEST-016 | Document supported aliases and reject conflicting column values. |
| P046 | Per-row minutes defaults and payload fields, S02/S12 | Intentional deviation for silent invalid-value default | FR-011,FR-018 | T025,T026 | TEST-011,TEST-018 | Invalid values never become 1440 silently. |
| P047 | Sequential row import, percent bar, row status, S12 | Missing | FR-019 | T028 | TEST-019 | Progress represents confirmed processing and preserves unstarted rows. |
| P048 | Success/failure counts, errors, partial summary toast, S10/S12 | Missing | FR-019,FR-023 | T028,T029 | TEST-019,TEST-023 | Result totals include unknown and unstarted states and safe row references. |
| P049 | Import can span sites/WLANs, global cached map, S02/S12 | Decision required | FR-017,FR-018 | T002,T004,T026 | TEST-017,TEST-018 | Reviewed permitted row scope is bound to a fresh batch revision. |
| P050 | Repeat import button and refresh current list, S12 | Intentional deviation for unsafe repeat | FR-019,FR-021 | T028,T024 | TEST-019,TEST-021 | Already-dispatched rows cannot be blindly submitted again. |
| P051 | Site changes reset only some source actions, S13 | Intentional deviation | FR-004,FR-033 | T012,T029 | TEST-004,TEST-033 | All actions, dialogs, mappings, and stale results are invalidated. |
| P052 | Guest sort: active before expired, descending expiry, S04 | Missing | FR-005 | T013,T014 | TEST-005 | Authoritative active/expired/unknown records use documented stable order. |
| P053 | Expiring under 60 minutes, warning under 480, duration formatting, S11/S13 | Missing | FR-006 | T013,T014 | TEST-006 | Test 0,59,60,479,480,1439,1440 minutes and unknown time. |
| P054 | Guest filter searches all details and custom fields, S11 | Decision required | FR-007 | T002,T014 | TEST-007 | Privacy-approved fields work without DOM or log disclosure. |

## Backend, storage, deployment, and evidence

| ID | Source feature and evidence | Current target disposition | Requirement | Tasks | Test | Acceptance evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P055 | Auto-select first organization when unset, S03 | Intentional deviation | FR-002,FR-020 | T002,T012 | TEST-002,TEST-020 | Explicit approved organization is required. |
| P056 | Org templates/sitegroups filter and request-local lookup caches, S03 | Missing | FR-003 | T012,T019 | TEST-003 | Failed lookup is unavailable, not a false no-portal result. |
| P057 | All-org WLAN merge without exact assignment, S04 | Intentional deviation | FR-003,FR-022 | T012,T019 | TEST-003,TEST-022 | No unrelated org WLAN appears for the selected site. |
| P058 | Site list/read/write failures fall back to org scope, S04/S05 | Intentional deviation | FR-022 | T003,T019,T024 | TEST-022 | Failed site requests never issue org operations. |
| P059 | Synthesized success/expiry after SDK calls, S05 | Intentional deviation | FR-023,FR-033 | T024,T029 | TEST-023,TEST-033 | Actual status and observed record control success. |
| P060 | Source console-only read errors and empty fallbacks, S04/S06/S11 | Intentional deviation | FR-023 | T019,T029 | TEST-023 | Failed reads are visible and never equal true-empty. |
| P061 | Source personal-value logging and token-name field4, S01/S05 | Intentional deviation | FR-024 | T005,T030 | TEST-024 | Audit/log/screenshot retention follows D1/D4 and redaction tests. |
| P062 | Source process/browser caches, no database/Redis, S01-S06/S14-S16 | Missing guest coordination, reusable target infrastructure only | FR-025 | T008,T030,T031 | TEST-025 | No source DB is assumed. Existing store holds only approved coordination. |
| P063 | Target exact masked projection and unknown values, M01/M02 | Existing | FR-029 | T009,T013 | TEST-029 | All 22 current projection cases retain exact shape and behavior. |
| P064 | Standalone port 5000, app container and log mount, S15-S17 | Intentional deviation | FR-025,FR-035 | T008,T031 | TEST-025,TEST-035 | Existing MistHelper app owns the route, health, stores, and port. |
| P065 | Source runtime/dev dependencies and CDN assets, S07/S14/S23 | Missing guest asset integration, reusable shared packages only | FR-026 | T008,T010,T031 | TEST-026 | No downgrade, second token setup, remote runtime asset, or duplicate stack. |
| P066 | Source health timestamp, config host/token/org, S01/S02/S15 | Missing guest-specific acceptance | FR-026,FR-035 | T031 | TEST-026,TEST-035 | Existing session and health remain stable without a guest credential source. |
| P067 | Source build, release, CodeQL, quality, STE, dependency workflows, S23-S25 | Intentional deviation to target workflows | FR-035 | T031,T035 | TEST-035 | Retain target required status names and existing release ownership. |
| P068 | Seven source PNGs and synthetic capture helper, S21/S22 | Missing target comparison | FR-027,FR-030 | T001,T034,T038 | TEST-027,TEST-030 | Paired fixtures, screenshots, approved differences, and final review persist. |
| P069 | Source offline tests, complexity/docs tests, S20/S23 | Missing full target coverage | FR-030 | T035,T037 | TEST-030 | Every acceptance family has executed evidence before release. |
| P070 | CC BY-NC-SA-4.0 and owner authorization, S18 | Missing retention work, rights decision resolved | FR-032 | T001,T036 | TEST-032 | Preserve credit, license/change notices, and applicable distribution terms. |
| P071 | No source operator identity or typed confirmation, S01/S13 | Intentional deviation | FR-020,FR-021 | T002,T018,T024 | TEST-020,TEST-021 | Approval, identity/scope enforcement, CSRF, and typed confirmation precede writes. |
| P072 | Source setup, usage, troubleshooting, screenshots, S19/S22 | Missing integrated operator guide | FR-031 | T036,T039,T040 | TEST-031 | Guide covers supported behavior, deviations, approval, cutover, and recovery. |

## Coverage rule

Rows are the inventory units. Grouped rows name each control or variant explicitly.
No unseen server feature is inferred from a screenshot.
Additional discovery requires a new row, requirement mapping, test acceptance, and task before migration approval.
Existing infrastructure does not count as completed guest functionality.
