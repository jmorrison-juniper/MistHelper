# Acceptance evidence

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
Connected production acceptance remains the parent's responsibility.
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

Committed test-quality checks and CI evidence remain pending.
No Windows execution or human acceptance is claimed.

## Connected legacy-bundle check

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
