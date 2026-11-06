# Implementation Plan: AP warning report

**Branch**: `jmorrison-juniper-ap-warning-report` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Summary

Keep the existing report package and menu registration.
Read AP statistics for each site, then retain recent or untimed nonzero trouble records.
Join the results with inventory, site names, connection state, and the live LED dictionary.
Preserve unknown codes and do not treat recent evidence as proof of an active fault.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing mistapi SDK and standard library.

**Storage**: Existing DataExporter backends. No new storage system.

**Testing**: Pytest with mocked SDK responses and real CSV and SQLite writer integration.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Existing menu application.

**Performance Goals**: One paginated request sequence per site, with dictionary retrieval once per run.

**Constraints**: Read-only SDK requests, no new dependencies, and no credentials in output.

**Scale/Scope**: One selected organization, all its sites and AP inventory, with sequential site statistics reads.

## Constitution Check

- The new package adds the fourth child to `src/operations/exporting`, which currently has three.
- Each new source package has at most five children.
- Methods use at most five parameters and remain small.
- Existing oversized report and export packages remain unchanged.
- Existing process-folder debt remains outside this feature.
  Separate remediation must migrate existing records without changing this feature.
- Product writes use DataExporter under `data/`.
- All cloud reads use supported SDK methods and the existing authenticated session.
- Site statistics reads use `listSiteDevicesStats` with AP type and all connection states.
- Timed observations must fall inside the inclusive 15-minute window ending at report creation.
- Untimed observations retain uncertainty. Future observations do not qualify.
- SDK pagination validates every page rather than accepting a partial `get_all` result.
- Tests cover endpoint arguments, malformed data, failed pages, unknown codes, and output failure.
- Commit messages use Conventional Commits.
- No custom transport or WebSocket exception is necessary.
- App-managed branch creation replaces the branch hook.
- No shared feature pointer changes.

**Post-design decision**: Pass for isolated implementation.
The coordination check found separate README sections and no active competing agent.
The user requests progress, so menu integration no longer depends on the WAN feature merge.

## Project Structure

### Documentation

The managed feature root contains `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
The design directory contains research, data model, quickstart, contracts, and checklists.

### Source Code

```text
src/operations/exporting/ap_warning_report/
  __init__.py
  client.py
  codes.py
  rows.py
  operation.py
tests/unit/ap_warning_report/
  test_codes.py
  test_rows.py
  test_client.py
  test_operation.py
tests/integration/ap_warning_report/
  test_export.py
  test_sqlite.py
```

**Structure Decision**: Use a new compliant package rather than extending an oversized existing package.

## Complexity Tracking

## Recovery filtering, issue #4625

Use the isolated completion worktree and preserve issue #4624 changes.
The existing branch replaces the branch-creation hook. Do not change the shared feature pointer.
Update this existing managed specification rather than create a competing feature record.
Use sequential candidate-only reads. No concurrency or new dependency is necessary.
Use `searchOrgDeviceEvents` with MAC, AP type, an explicit 60-minute UTC window, and at most ten pages.
Use SDK `search_after` pagination. Missing totals, incomplete totals, or a full terminal page without proof mean incomplete evidence.
Validate live `AP_CONNECTED` and `AP_DISCONNECTED` catalogue keys before accepting state evidence.
The verified event records contain `ap`, `mac`, `type`, and epoch `timestamp`.
Read `getSiteDeviceStats` for each candidate and require matching identity and site.
Statistics are fresh only when `last_seen` is within 300 seconds before the evidence cutoff and not before reconnect.
This five-minute freshness limit is conservative and independent of the trouble observation window.
Read all event types so newer trouble and connection blockers remain visible.
Treat `AP_CONFIG_FAILED`, `AP_RESTARTED`, `AP_UNASSIGNED`, and `AP_UNCLAIMED` after reconnect as blockers.
Also check fresh `last_trouble` for newer observations.
Only verified code-and-key pairs 02 through 08 and 12 through 16 can qualify for recovery.
Other codes remain visible. In particular, a cloud connection does not clear a management tunnel or firmware fault.
Add classification columns without removing the existing report columns.
Give the recovered export its own natural-key strategy so it cannot overwrite warning rows in the database.
Keep existing test directories unchanged. Extend their existing test modules.
The existing methods above structural limits remain debt. Keep new recovery methods at 25 lines or fewer and complexity at ten or less.
The separate structural guard remains the remediation authority for existing debt.

### Verified evidence

The vendored OpenAPI `response_device_events_search` requires `results`, `start`, `end`, `limit`, and `total`.
The installed SDK accepts `start` and `end` as text, and exposes `search_after`, not `page`.
Live definitions identify `AP_CONNECTED` as cloud reconnection and `AP_DISCONNECTED` as loss of cloud connection.
The read-only candidate probe returned `status`, `last_seen`, `last_trouble`, `mac`, `id`, and `site_id`.
The screenshot times convert to disconnect `2026-11-06T22:11:26Z`, trouble `22:17:01Z`, and reconnect `22:17:03Z`.
Those times establish ordering, not a complete recovery decision without fresh statistics and complete history.

No new structural exception is required for source files.
The existing test trees and unique changelog process records retain their established layout.
The primary-key registry receives one independent strategy entry.
This adds no module-level names and changes no existing strategy.
The follow-up integration must not rename modules or change existing menu behavior.
