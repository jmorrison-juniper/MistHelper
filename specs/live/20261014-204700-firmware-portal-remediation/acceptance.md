# Acceptance evidence

## Current firmware-policy-only revision

The user explicitly approved firmware-policy-only restoration after the earlier complete-settings acceptance failed safely.
Complete private source and recovery backups remain required.
Earlier evidence below records the preceding implementation, not acceptance of the revised candidate.

| Requirement | Revision evidence | Status |
| - | - | - |
| FR-017, FR-018 | All-class policy restoration with current sibling preservation | Passed revised unit, integration, and browser tests |
| FR-019 | Unrelated historical fields do not block policy recovery or enter restoration writes | Passed strict policy rejection and unrelated-field preservation tests |
| FR-020 | Visible policy-only scope and schedule-default disclosure before confirmation | Passed revised browser tests and missing/empty/valid schedule tests |
| SC-002, SC-003 | Realistic large-bundle firmware policy roundtrip | Passed 4,003-record, 489,502,953-byte pipeline |
| Connected source and application | Parent validated the isolated committed candidate and confirmed the real firmware policy roundtrip | Passed |

Complete settings restoration remains outside the user-approved revised scope.
The parent confirmed actual firmware-policy restoration success under the explicit user-directed scope.

The combined revised firmware, jobs, and portal suite passed 332 tests with 92.25 percent coverage.
The full guardrail suite passed 909 tests and skipped three with reported causes.
The first guard run rejected the intentionally changed menu 306 title.
The exact identity digest now pins the user-approved title. The guard still checks the complete metadata.
The same-browser policy-to-restoration test preserves a later unrelated organization setting and valid `any` schedules.
The settings-free validator passed a private fixture and rejected a malformed policy.
It reported zero network requests and zero settings writes in both cases.
The actual private source remains with the parent. This session did not access it.

The parent passed actual private firmware projection on both 145-record source bundles.
The original source contained 149 policies and two explicitly defaulted records.
The fresh source contained four policies and no defaults.
Both validators reported zero network requests and zero settings writes.
The parent independently passed the revised 332-test suite.

Connected refresh exposed initialization that invalidated the saved job before attempting resume.
The repair starts saved status independently, retains prepared form choices, and never invalidates during identity initialization.
Waiting and ready regressions hold identity loading until resumed status appears.
All 65 firmware browser/API cases passed after the repair.
Terminal preparation and application errors remain visible after delayed identity loading.
## Final external acceptance

The parent completed authorized connected menu 305 CONFIGURE and menu 306 RESTORE on candidate `8f0ceba`.
All 145 restoration scopes passed readback.
The admitted SDK observer confirmed 145 equal policy projections, unrelated snapshots, and owners.
It confirmed exact membership equality and performed zero writes.
Only the documented modification timestamp was excluded from unrelated-settings comparison.
No firmware execution request occurred.
Complete source and recovery backups remain preserved privately.
See [parent live evidence](https://github.com/jmorrison-juniper/MistHelper/issues/4227#issuecomment-6184224213).

The parent verified the exact `e2f779e` refresh candidate at 800px.
Preparation, reload, and a five-second wait retained organization, model, version, enabled state, and schedule.
The confirmation remained ready. A genuine edit invalidated it.
The parent examined the private fixture screenshot.
The [draft pull request](https://github.com/jmorrison-juniper/MistHelper/pull/4228) records this refresh proof.
The child stopped its exact offline fixture process after acceptance.

The following runs succeeded on exact `e2f779e`:

- [Quality Gates 38678356548](https://github.com/jmorrison-juniper/MistHelper/actions/runs/38678356548).
- [CodeQL 38678356397](https://github.com/jmorrison-juniper/MistHelper/actions/runs/38678356397).
- [STE 38678356464](https://github.com/jmorrison-juniper/MistHelper/actions/runs/38678356464).
The final logs reported 914 E2E passes and 94 percent combined coverage.
The actual browser artifact `11947529468` contains two complete/partial screenshots in a 378,193-byte ZIP.
Both agents downloaded and examined these screenshots.
Artifact metadata binds them to exact `e2f779e`.
The draft pull request records the complete final evidence.
The parent retains manual merge and deployment ownership.
Released-image verification and production deployment remain pending.
This child performed neither action.

## Requirement mapping

| Requirements | Evidence | State |
| - | - | - |
| FR-001, SC-001 | `test_workspace_category_keyboard_and_responsive_columns`, at 1440, 800, and 390 pixels. Semantic buttons retain both workspaces without an iframe. | Passed |
| FR-002 | Both workflows resolve checked SDK names. Bundle labels share one organization lookup and complete site listing per organization, without individual site requests. | Passed |
| FR-003, FR-004 | Catalog tests and `test_catalog_all_hardware_dynamic_versions_and_schedule_defaults` check all four classes, hidden selectors, and mixed numerical release ordering. | Passed |
| FR-005 | The same browser test checks day `any` and time `02:00`. Unsupported groups receive no schedule controls. | Passed |
| FR-006, SC-004 | `test_confirmation_waits_for_every_backup_and_no_early_write` blocks actual verification and checks hidden confirmation and zero settings writes. | Passed |
| FR-007 | Both complete portal suites exercise exact words, CSRF, ownership, cancellation, and repeated apply rejection. | Passed |
| FR-008 | `test_browser_resumes_wait_progress_and_paginates_sorted_scope_rows` checks a 7201-second wait and a sorted 101-row table. | Passed |
| FR-009, FR-010, SC-002, SC-003 | Scale tests verify realistic records, complete request counts, and the large legacy format. See the measured results below. | Passed |
| FR-011, SC-004 | Recovery tests cover complete recovery, freshness, exclusions, tampering, and private files. Portal tests verify private-output denial. | Passed |
| FR-012 | Admission tests verify the existing request control, authoritative rolling-hour usage, and repeated checks after 660-second waits. | Passed |
| FR-013 | Portal failure tests verify partial outcomes. The same-browser policy-to-restoration test checks organization-before-site writes and complete recovery. | Passed |
| FR-014, SC-005 | Job tests check restart interruption, persistent private status, bounded capacity, and atomic token consumption. Browser refresh checks recover ready and waiting states. | Passed |
| FR-015, SC-006 | Browser suites deny private downloads and inspect rendered content. Evidence uses only fixture identities and contains no settings. | Passed |
| FR-016 | Operator guides, wiki, narrow README descriptions, this mapping, and the issue fragment are present. | Passed |

Selection invalidation tests cover the model, version, day, time, scope, and policy state.
They require an empty obsolete summary, empty table, zero progress, hidden confirmation, and no retained operation reference.
A resumed preparation also loses its verification state when the scope changes.

The 179-switch-model browser fixture verifies bounded scrolling and reachable backup controls at 800 pixels.
It retains every model and permits selection of the last model.

## Visual evidence

The baseline commit `8b7554c` contains sanitized BEFORE screenshots and accessibility snapshots.
The matching AFTER evidence is under `evidence/`.
The image `after-800px.png` records the narrow side-by-side workspace.
The image `after-restore.png` records verified recovery before confirmation.
No connected screenshot, private backup, production log, or credential belongs in these files.

The parent confirmed the connected fixture policy apply and restoration flows.
The parent also confirmed numerical ordering, hidden unchecked selectors, schedule defaults, sorted verification rows, and confirmation sequencing.
The parent completed connected acceptance as recorded above.
The authorized live organization is Morrison House. This implementation session performs no production requests.

## Gate results

The two complete policy and restoration portal files passed 35 tests before the final large-model test.
The job manager and cross-workflow files passed 20 tests.
Generic execution and structure checks passed 88 tests and skipped two with stated causes.
Further structure, menu safety, and SDK checks passed 27 tests.

The full Ruff gate passed.
The full Black check left 2429 files unchanged.
The configured mypy command passed for 844 source files.
Firmware source Bandit and the complexity limit of 10 passed.
Firmware source docstring coverage reached 100 percent.
The three operator-guide link scans found zero broken links.

The combined domain, job, and browser command passed 271 tests in 60 seconds.
Changed firmware and portal packages reached 94.34 percent coverage.
The dependency audit through a resolved runtime lock found no known vulnerability.
The direct requirements audit failed because its temporary `ensurepip` process aborted.
An installed-environment audit reported eight advisory entries for development-environment `pip 26.0.1`, not a runtime requirement.

## Scale and resources

Both scale cases cover 4001 sites and two organizations.
Each requires exactly 4003 settings writes and 20015 settings reads.
Policy requires six complete membership reads.
Restoration requires eight membership reads, two organization lookups, and three complete source parses.
Each target receives one write. Every organization write precedes every site write.

The realistic 145-record roundtrip uses 121856-character payloads and exceeds 17402805 bytes.
The 4001-record parser fixture contains 487910097 bytes.
It retains 490655617 bytes, with a peak of 491098332 bytes.
Its maximum parser buffer is 187473 bytes.
Parsing and verification require 442715 peak bytes above the retained records.
Complete snapshots still require memory proportional to their settings.
The parser permits unlimited aggregate size and record count.
It bounds each JSON value or record to 8 MiB and nesting to 64 levels.

Committed test-quality checks and runtime CI passed as recorded above.
No Windows execution is claimed. Parent browser acceptance passed.

## Historical complete-settings legacy-bundle check

This section records the superseded complete-settings scope.
Its vendor contract blocker does not apply to the approved firmware-policy-only scope.

The parent built candidate `7700bcb` in a separate ephemeral container and copied the original private bundle.
The settings-free validator passed source privacy and integrity, then rejected record zero during saved ownership or writable-schema checks.
It sent zero network requests and zero settings writes.
The exact safe diagnostic cause remains under investigation.
This real-bundle acceptance is not complete, despite the passing generated large-bundle tests.

The parent also tested a fresh 145-record backup with the same result.
Safe diagnostics identify public-schema differences, nullable weekday and port fields, enum differences, and a nested read-only identifier.
Unrecognized field names remain withheld.
The repair must prove writable support from public schemas and preserve rejection of unproven fields.
Policy preparation must prove recovery usability before it reveals confirmation.
No live settings write occurred.

The parent verified guarded policy preparation against the actual organization.
Planning reported completed site counts and a percentage.
Unsupported restoration projection stopped preparation and kept confirmation hidden.
The browser incorrectly labeled this terminal failure as an unreadable status response.
The repair separates terminal preparation failure, uncertain application failure, and polling transport failure.
Three browser cases prove these distinctions without cloud writes.

Actual restoration preparation also reported a current ownership mismatch before schema projection.
The safe equality diagnostic confirmed that organization `org_id` matches.
Organization settings `id` and `site_id` hold unrelated metadata and do not identify the organization.
The corrected organization guard validates `org_id`.
Site guards still validate both `org_id` and `site_id`, with unchanged membership checks.
Distinct organization metadata and wrong site ownership have regression coverage.
Actual schema acceptance remains blocked.
