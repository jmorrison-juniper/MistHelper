# Source-to-target parity inventory

Evidence IDs (S, T, and R prefixes) resolve in [research section 4](../research.md#4-source-evidence-mistguestauthorizations-at-0213240c) and [section 5](../research.md#5-target-evidence-misthelper-at-f03c6c9b). Requirement IDs refer to [spec](../../spec.md). Task IDs refer to [tasks](../../tasks.md). Test IDs refer to [E2E acceptance](e2e.md).

## Status values

- **Existing**: The target implements the contract today.
- **Existing adjacent**: The target implements related behavior that does not replace the source workflow.
- **Missing**: Future work remains. A reusable helper may exist.
- **Intentional deviation**: The target departs from the source for a documented safety or contract reason.
- **Decision required**: A decision in the research register controls the final behavior.

| ID | Source feature and evidence | Target disposition | Requirement | Tasks | Test | Acceptance evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P001 | Root page renders the dashboard. S01 L85 to L88, S03 L6. | Missing. No guest page exists. T03 and T04 have no guest route. | FR-001 | T010, T011 | TEST-001 | The guest tab reaches the shared page and shows the active scope. |
| P002 | Title and header wording "Guest WiFi Pre-Authorization Portal". S03 L6 and L676. | Decision required. The target chrome differs. D-13 applies. | FR-027 | T006, T034 | TEST-027 | Paired header screenshots are approved. |
| P003 | Test Connection button, status text, and test on load. S03 L542 to L547 and L1792. S01 L91 to L99. | Missing. | FR-002 | T012 | TEST-002 | Unavailable, testing, connected, and failed states are distinct. |
| P004 | Three columns for site, WLAN, and quick actions. S03 L580 to L617. | Missing. | FR-027 | T011, T034 | TEST-027 | Desktop regions keep their order and relative weight. |
| P005 | Site search matches name and address without case. S03 L583 and L1060 to L1063. | Missing. | FR-004 | T012 | TEST-004 | Both fields filter without losing the valid scope silently. |
| P006 | Site selector starts disabled and loads options. S03 L584 and L1038. | Missing. | FR-003, FR-033 | T012 | TEST-003 | Loading, unavailable, empty, and selected states are asserted. |
| P007 | WLAN selector and guest-only help. S03 L593 to L596 and L1071 to L1084. | Missing. | FR-003 | T012 | TEST-003 | Only enabled applicable portal WLANs appear. |
| P008 | Organization-assigned WLANs show the label "(Org)". S03 L1101. | Missing. | FR-003 | T012 | TEST-003 | Assignment and duplicate-SSID fixtures resolve by ID. |
| P009 | Add, Bulk Import CSV, and Refresh Guest List buttons start disabled. S03 L611 to L617. | Missing. | FR-009, FR-019, FR-033 | T014, T017, T027 | TEST-009, TEST-019, TEST-033 | Enabled states follow the verified scope and access. |
| P010 | Four statistic cards. S03 L626 to L647. | Missing. | FR-006 | T014 | TEST-006 | Counts match fixtures, including unknown observations. |
| P011 | Guest section and search field. The placeholder text is Search guests followed by three dots. S03 L654 to L661 and L1133 to L1137. | Missing. | FR-005, FR-007 | T014 | TEST-005, TEST-007 | Filtering keeps the full-list total and permitted detail access. |
| P012 | Guest card hover and click opens the edit dialog. S03 L215 hover rule. Click handler not re-read. | Missing. | FR-005, FR-028 | T014, T022, T034 | TEST-005, TEST-028 | Mouse and keyboard open the same exact record. |
| P013 | Guest card detail fields for MAC, name, email, company, and custom fields. S03 L1137. | Decision required. The privacy scope is open. D-6 applies. | FR-007, FR-010 | T002, T014 | TEST-007, TEST-010 | Approved fields and privacy assertions pass. |
| P014 | Time badges use expired, under 60 minutes, and under 480 minutes. S03 L1149 to L1150 and L1497. | Missing. | FR-006, FR-028 | T014, T034 | TEST-006, TEST-028 | Text and noncolor cues keep status at each boundary. |
| P015 | Card hover effect. S03 L215. | Decision required. The style deviation needs approval. | FR-027 | T006, T034 | TEST-027 | The reviewer approves the hover treatment. |
| P016 | Empty and welcome states. Text "No authorized guests found for this WLAN." S03 L664 to L676. | Missing. | FR-033 | T014 | TEST-033 | Initial, true-empty, filtered-empty, and unavailable states differ. |
| P017 | Red no-portal banner with dismiss control and Mist Dashboard link. S03 L555 to L572. | Missing. | FR-003, FR-023 | T012, T029 | TEST-003, TEST-023 | A missing configuration differs from a denied or failed discovery. |
| P018 | Toast notifications with a close control. S03 L534, L1206, and L1214 to L1217. | Missing. | FR-023, FR-028 | T029, T034 | TEST-023, TEST-028 | Safe messages are announced. Failure details stay actionable. |
| P019 | Dark theme colors and monospace MAC style. S03 L10 to L25 and L30. | Decision required. D-13 applies. | FR-027, FR-028 | T006, T034 | TEST-027, TEST-028 | Paired styling and focus checks cover contrast and long values. |
| P020 | Responsive breakpoints at 768 to 1400 pixels and at 767 pixels and below. S03 L483 and L516. | Missing. | FR-028 | T034 | TEST-028 | The three declared viewports keep every control reachable. |
| P021 | Add dialog in an extra-large layout with device, detail, and client regions. S03 L686 to L688 and L697 to L766. | Missing. | FR-009, FR-027 | T017, T034 | TEST-009, TEST-027 | Paired blank and filled screenshots keep the region relationships. |
| P022 | Required MAC input with placeholder. S03 L701. Source normalizes MAC forms. S02 L42 to L68. | Decision required. The accepted format set needs approval. | FR-009, FR-022 | T003, T016, T017 | TEST-009, TEST-022 | Strict tests cover colon, hyphen, bare, and invalid forms. |
| P023 | Name and email inputs. S03 L706 and L710. The schema marks `name` read-only (T11). | Decision required. D-9 applies. | FR-009, FR-012 | T003, T017, T022 | TEST-009, TEST-012 | The name is not sent. The portal explains the limit. |
| P024 | Company, field1, field2, and sponsor email inputs. S03 L714, L722, L726, and L730. | Missing. | FR-010 | T017, T022 | TEST-010 | Optional values and empty-field edits follow the approved schema. |
| P025 | Field4 is set from the API token name. S02 L523 and L550 to L552. | Intentional deviation. The token name is not operator identity. D-6 applies. | FR-010, FR-024 | T005, T017, T030 | TEST-010, TEST-024 | Attribution follows the approved actor policy. |
| P026 | Duration input with default 1440 and minimum 1. S03 L736. | Missing. | FR-011 | T016, T017 | TEST-011 | Empty, zero, negative, noninteger, and boundary values are explicit. |
| P027 | Ten presets from 1 hour to 1 year. S03 L737 to L747. | Intentional deviation for values above 259200. D-7 applies. | FR-011 | T003, T016, T022 | TEST-011 | Each preset has a supported value or a disabled explanation. |
| P028 | Maximum 2628000 and the five-year promise. S03 L736 and S09 L27. | Intentional deviation. D-7 applies. | FR-011 | T003, T016 | TEST-011 | No five-year promise and no silent clamping exist. |
| P029 | Client search by MAC, hostname, IP, or SSID. Two characters minimum. Debounce of 300 milliseconds. S03 L755, L758, L1512, and L1775. | Missing. | FR-008 | T019, T020 | TEST-008 | Every field, short input, delayed result, failure, and empty result passes. |
| P030 | Client result list in a scrolling panel. S03 L756 and L1741. | Decision required. The disclosed fields need approval. D-6 applies. | FR-008, FR-028 | T002, T020, T034 | TEST-008, TEST-028 | Keyboard selection fills the correct device. |
| P031 | Selected client fills MAC and name. The source lines were not re-read in this run. | Decision required. The writable name is read-only (D-9). | FR-008, FR-012 | T003, T020 | TEST-008, TEST-012 | The prefill never sends a read-only field. |
| P032 | Cancel control, submit button, and spinner. S03 L765 to L767 and L1591. | Missing. | FR-009, FR-033 | T017, T021 | TEST-009, TEST-033 | Cancel sends no write. A confirmed result refreshes the exact scope. |
| P033 | Edit dialog with a disabled MAC display. S03 L776 to L791. | Missing. | FR-012, FR-027 | T022, T034 | TEST-012, TEST-027 | The MAC stays fixed. Permitted fields load accurately. |
| P034 | Extension field labeled "Extend Authorization (minutes)" with default 1440. S03 L823 to L824. | Decision required. The duration origin needs contract evidence (D-8). | FR-012, FR-013 | T003, T022 | TEST-012, TEST-013 | A detail-only edit does not extend access. |
| P035 | Update button and spinner. S03 L848 to L849 and L1632 to L1653. The source payload includes `name`. S03 L1639. | Missing. The `name` field is removed (D-9). | FR-012, FR-033 | T022, T024 | TEST-012, TEST-033 | Exactly one verified update occurs after fresh confirmation. |
| P036 | Revoke Access button in the edit footer. S03 L843 to L845. | Missing. | FR-014 | T023, T024 | TEST-014 | Cancel, denial, confirmed revoke, failure, and unknown outcome stay distinct. |
| P037 | Source revocation sends PUT with `minutes` set to 0. S02 L649 to L652 and S09 L238. | Decision required. Revoke stays unavailable until verified (D-8). | FR-014, FR-022 | T003, T023 | TEST-014, TEST-022 | A schema-valid zero is not accepted as proof of removal. |
| P038 | Backend `notify` option sent when true. S01 L196 and S02 L554 to L555. The schema has no `notify`. | Intentional deviation. D-10 applies. | FR-034 | T003, T006, T017 | TEST-034 | The payload omits `notify`. No notification option appears. |
| P039 | Import dialog with two steps and close controls. S03 L858 to L875 and L886. | Missing. | FR-019, FR-027 | T027, T034 | TEST-019, TEST-027 | Paired import views keep the order and keyboard dismissal. |
| P040 | Template download and CSV template with ten headers and two examples. S03 L877 and S01 L285 to L334. | Missing. | FR-015 | T025, T027 | TEST-015 | The ten headers match. The examples use fictional data. |
| P041 | File input accepts `.csv`. Local read and reset on close. S03 L889. | Missing. | FR-016, FR-033 | T025, T027 | TEST-016, TEST-033 | Invalid type, empty file, cancel, replacement, and reopen states pass. |
| P042 | Preview shows the first five rows and the total row count. S03 L891 to L899 and L1305. | Missing. | FR-016 | T025, T027 | TEST-016 | Rows beyond five keep complete accounting outside the preview. |
| P043 | Browser CSV parser with limited quote handling. The parser lines were not re-read in this run. | Intentional deviation. The parser rejects or reports each malformed row. | FR-016 | T025, T026 | TEST-016 | Quoting, newlines, and malformed rows are reported. |
| P044 | Case-insensitive site and SSID mapping. S03 L1381 to L1382 and S01 L349 to L375. | Missing. | FR-017 | T026, T027 | TEST-017 | A duplicate name requires an explicit ID. It does not use the last entry. |
| P045 | Sponsor header alias `field3_sponsor_email`. S01 L302. | Missing. | FR-015, FR-016 | T025 | TEST-015, TEST-016 | Supported aliases are documented. Conflicting values are rejected. |
| P046 | Missing or invalid row minutes default to 1440. S03 L1409 and S01 L407. | Intentional deviation. D-11 applies. | FR-011, FR-018 | T025, T026 | TEST-011, TEST-018 | An invalid value never becomes 1440 silently. |
| P047 | Import progress bar. S03 L905 to L910. Sequential behavior not re-read. | Missing. | FR-019 | T028 | TEST-019 | Progress shows confirmed processing and keeps unstarted rows. |
| P048 | Success and failure counts with error details. S03 L911 to L917. | Missing. | FR-019, FR-023 | T028, T029 | TEST-019, TEST-023 | Totals include unknown and unstarted states. |
| P049 | Import can span sites and WLANs through the mapping. S03 L1360 to L1382. | Decision required. D-11 and D-15 apply. | FR-017, FR-018 | T002, T004, T026 | TEST-017, TEST-018 | The reviewed scope binds to a fresh batch revision. |
| P050 | Repeat import button. S03 L924. | Intentional deviation. Dispatched rows are never submitted again. | FR-019, FR-021 | T024, T028 | TEST-019, TEST-021 | No row replays after a dispatch. |
| P051 | Site change resets only part of the state. Not re-read in this run. | Intentional deviation. Every dependent action is invalidated. | FR-004, FR-033 | T012, T029 | TEST-004, TEST-033 | A late response from the old scope cannot change the new scope. |
| P052 | Guest sort order. Not re-read in this run. | Missing. | FR-005 | T013, T014 | TEST-005 | The documented sort is stable for each state. |
| P053 | Expiry thresholds and duration text. S03 L1149 to L1150 and L1485 to L1489. | Missing. | FR-006 | T013, T014 | TEST-006 | Values 0, 59, 60, 479, 480, 1439, and 1440 minutes are tested. |
| P054 | Guest filter covers MAC, name, email, company, and fields 1 to 4. S03 L1137. | Decision required. D-6 applies. | FR-007 | T002, T014 | TEST-007 | Approved fields work without DOM or log exposure. |
| P055 | Organization auto-selection uses the first organization. S02 L160. | Intentional deviation. An explicit approved organization is required. | FR-002, FR-020 | T002, T012 | TEST-002, TEST-020 | No automatic organization selection occurs. |
| P056 | Organization templates and site groups filter the WLAN assignment. S02 L245 to L282. | Missing. | FR-003 | T012, T019 | TEST-003 | A failed lookup shows unavailable, not a false no-portal result. |
| P057 | Organization WLAN merge without an exact site assignment check. S02 L283 to L296 and L342. | Intentional deviation. | FR-003, FR-022 | T012, T019 | TEST-003, TEST-022 | No unrelated organization WLAN appears for the selected site. |
| P058 | A failed site request uses the organization scope. S02 L423, L592, and L772. | Intentional deviation. | FR-022 | T003, T019, T024 | TEST-022 | A failed site request never issues an organization operation. |
| P059 | Success is synthesized from a 2xx response. S02 L659 to L660. | Intentional deviation. | FR-023, FR-033 | T024, T029 | TEST-023, TEST-033 | The observed record controls the result. |
| P060 | Read errors go to the console and show an empty state. S03 L1122 to L1125 and L666. | Intentional deviation. | FR-023 | T019, T029 | TEST-023 | A failed read never equals a true empty result. |
| P061 | Personal values appear in logs. S01 L200. The token name is used as attribution. S02 L550 to L552. | Intentional deviation. | FR-024 | T005, T030 | TEST-024 | Audit, log, and screenshot retention follow D-12 and redaction tests. |
| P062 | No database or Redis service exists in the source. S06 L6 and S07 L2. | Missing guest coordination. No source data migration exists. | FR-025 | T008, T030, T031 | TEST-025 | No source database is assumed. The existing SQLite store holds only approved coordination. |
| P063 | Target offline projection and its exact shape. T01 L1 to L64 and T02 L11 to L91. | Existing. | FR-029 | T009, T013 | TEST-029 | All 22 current projection cases keep the exact shape and behavior. |
| P064 | Standalone port 5000 and one application container. S06 L10 to L11 and S05 L52 and L56. | Intentional deviation. The target app owns the route, health check, stores, and port. | FR-025, FR-035 | T008, T031 | TEST-025, TEST-035 | One existing application serves the feature. |
| P065 | Source runtime pins mistapi 0.64.0 and Flask 3.1.3. S08 L2 to L4. | Intentional deviation. The target pins mistapi 0.64.1 (T10 L129). | FR-026 | T008, T010, T031 | TEST-026 | No downgrade, second credential setup, or duplicate stack exists. |
| P066 | Source health route and configuration names. S01 L423 to L424 and S02 environment names. | Intentional deviation. The target health check and configuration own these paths. | FR-026, FR-035 | T031 | TEST-026, TEST-035 | The existing session and health check stay stable. |
| P067 | Source workflows for quality, release, CodeQL, STE, stranded branches, and build. S12 and the source workflow list in R68. | Intentional deviation. The target workflows own these checks. | FR-035 | T031, T035 | TEST-035 | Required status names stay unchanged. Release ownership stays with the target. |
| P068 | Seven PNG screenshots and a capture helper. S13. | Missing. The target comparison does not exist yet. | FR-027, FR-030 | T001, T034, T038 | TEST-027, TEST-030 | Paired fixtures and approved differences exist. |
| P069 | Source offline tests. S11. | Missing. The target coverage does not exist yet. | FR-030 | T035, T037 | TEST-030 | Each acceptance family has executed evidence before release. |
| P070 | CC BY-NC-SA 4.0 license with attribution. S04 L1 and S10 L77. | Decision required. D-5 applies. | FR-032 | T001, T036 | TEST-032 | Credit, license, change notice, and share-alike terms are preserved. |
| P071 | No operator authentication in the source. The route list in S01 has no login route. | Intentional deviation. D-6 applies. | FR-020, FR-021 | T002, T018, T024 | TEST-020, TEST-021 | Approval, identity, scope, CSRF, and typed confirmation come before writes. |
| P072 | Source setup, usage, and troubleshooting guide. S09 L1 to L276 and S10. | Missing. The integrated operator guide does not exist. | FR-031 | T036, T039, T040 | TEST-031 | The guide covers supported behavior, deviations, approval, cutover, and recovery. |
| P073 | Menu 200 exports per-site authorized guests as CSV through the operation registry. T06 L118 and T08 L41. | Existing adjacent. The source interactive workflow remains missing. | FR-029, FR-030 | T037 | TEST-030 | Menu 200 behavior stays unchanged. The inventory keeps it separate from the source workflow. |

## Disposition counts

| Disposition | Count |
| --- | --- |
| Existing | 1 |
| Existing adjacent | 1 |
| Missing | 39 |
| Intentional deviation | 19 |
| Decision required | 13 |
| Total rows | 73 |

## Coverage rule

- Each row is an inventory unit. Each control or variant has its own row.
- No unseen server feature is inferred from a screenshot.
- A new discovery needs a new row, a requirement, a test family, and a task before approval.
- Existing infrastructure does not count as completed guest functionality.
- Rows that cite UNVERIFIED evidence stay visible. The research unverified list names each one.
