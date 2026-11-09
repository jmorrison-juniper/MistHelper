# Implementation Plan: Other-device event page status

**Branch**: `jmorrison-juniper-other-device-event-audit` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

Replace unchecked `get_all` aggregation with a local page loop through `mistapi.get_next`.
Check every status before accepting the payload. Return no aggregate after any failed page.
Keep the request boundary separate from local validation, collection, transformations, and the writer.
Track requested cursors locally. Reject repeated cursors, invalid cursors, and records that are not dictionaries.
Accept `None` and `""` as terminal cursors, consistent with the installed SDK.
Handle known invalid remote data explicitly with fixed messages and a failed result.
Catch arbitrary exceptions only around the actual endpoint or `get_next` call in `_fetch_events`.
Invoke `_collect_events` outside that catch and use `_fetch_events` for each follow-up request.

## Technical Context

**Language/Version**: Python 3.13 or newer. Local Python: 3.14.7.

**Primary Dependencies**: mistapi 0.64.1, requests, pytest.

**Storage**: Existing writer contract, mocked during tests.

**Testing**: Real SDK response objects through a mocked HTTP session with DNS and sockets blocked.

**Target Platform**: Windows, macOS, Linux.

**Project Type**: Existing menu operation.

**Performance Goals**: One SDK request for each required page. No new retries.

**Constraints**: Modify only the reserved source and test, one unique release note, and new feature-local records.

**Scale/Scope**: One operation. No shared API or schema change.

## Constitution Check

- Preserve #1794 commit `63dd076f7c1d96eda6c68a01237e48d6d29cf59b` without amendment.
- Preserve its patch and two source snapshots with SHA-256 values before changes.
- Retain the SDK transport and authentication. Add no direct HTTP requests.
- Use at most five methods in the existing exporter class.
- Existing persistence method length remains unchanged. Reduce the touched menu method by separating request behavior.
- Keep each new record directory at five children or fewer.
- Existing process-folder debt requires the existing managed-route migration, not unrelated edits in this slice.
- Preserve the shared selector, Git configuration, credentials, and app branch.
- Use `Refs #4709` and the required co-author trailer for the new local commit.

The design passes. PowerShell remains unavailable.
Use the inspected numeric route and managed-tree guard without selector-writing commands.
The branch hook cannot replace the app-managed branch. Optional commit hooks remain deferred until validation.

## Project Structure

- `src/operations/exporting/export/site_other_device_events_exporter.py`
- `tests/unit/export/test_site_other_device_events_exporter.py`
- `changelog.d/issue-4709-other-device-page-status.md`
- This root: specification, plan, tasks, analysis, and `design/`.
- `design/`: research, data model, quickstart, contracts, and checklists.

## Complexity Tracking

The existing persistence method exceeds 25 physical lines with comments and logging.
This repair does not alter it. A separate structural slice can address that existing debt.
No new module-level names or output fields are necessary.
The cursor extension follows the progress invariant in `PickerPageReader.read` and `PolicyResponse.collect`.
Use no feature-specific errors from those helpers.
The status check moves to the fetch boundary, outside the external-call catch.
The page validator returns the rows and the JSON `total`. The collector compares the total only at a terminal cursor.
Header totals receive a format check only, because the SDK derives the list cursor from them.
The device inventory guard `guard_page_count` is prior art. The exporter does not import the portal layer.
