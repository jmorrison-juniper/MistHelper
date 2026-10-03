# Implementation Plan: WiFi response failures

**Branch**: `jmorrison-juniper-wifi-response-failures` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3743-wifi-response-failures/spec.md`.

## Summary

Validate every native response page before accepting its records. Use the SDK's single-page helper instead of its unchecked aggregate helper.

Retain the existing merge, placeholder, output name, and final writer. Route failures through the exporter's existing error notice.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: The unchanged mistapi 0.64.0 SDK, requests, and the existing response integrity checker.

**Storage**: Existing CSV and configured export backends. Tests use temporary files and a counted controlled router.

**Testing**: Existing pytest scopes, independent native integration cases, and direct guard controls.

**Target Platform**: The owned macOS worktree. Existing portable path behavior remains unchanged.

**Project Type**: A menu-driven Python application.

**Performance Goals**: Preserve one SDK request for each requested page. Add no duplicate endpoint request.

**Constraints**: No live Mist request, production store, browser server, container, publication, shared-state mutation, or dependency change.

**Scale/Scope**: One reserved source file, two new test modules, and three authorized existing fixtures.

## Constitution Check

The repair retains class-based code, bounded methods, portable paths, existing logging, and existing output boundaries.
The native SDK remains the sole request interface.
The repair adds no wrapper, source alias, suppression, schema change, or endpoint-family migration.

The current exporter and parent directories already exceed five direct children.
The user's exact reservations require these existing boundaries and two new test names.
This repair does not restructure unrelated files.
A separate class and package refactor can remove that existing structural debt.

The app owns branch creation and renaming.
The standard feature hook switches branches, and the standard workflow writes shared `.specify` state.
The user prohibits both actions.
This feature uses current templates and feature-only context instead.
Optional commit hooks remain inactive until the one authorized local commit.

The user explicitly withholds publication and deployment.
The local commit, offline pull request body, and issue handoff are the delivery boundary.

## Project Structure

### Documentation (this feature)

```text
specs/3743-wifi-response-failures/
  .spec-context.json
  spec.md
  plan.md
  tasks.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/responses.md
    checklists/requirements.md
```

### Source Code (repository root)

```text
src/export/wifi_clients_exporter.py
tests/unit/export/test_wifi_clients_response_failures.py
tests/integration/export/test_wifi_clients_native_response_failures.py
tests/unit/export/test_wifi_clients_exporter.py  # Three authorized fixture cases only.
changelog.d/issue-3743-wifi-response-failures.md
```

**Structure Decision**: Keep the repair in the reserved exporter. Keep all support for the new tests inside their own modules.

## Design and Verification

1. Preserve all protected hashes and existing exporter method bodies before product edits.
2. Reproduce the four original native failure categories before product edits.
3. Validate status, parse evidence, and record shape on every page.
4. Read later pages through `mistapi.get_next`.
5. Verify successful page order, merges, valid empty data, and final writer selection.
6. Run applicable local gates and both unchanged test-quality ratchets.
7. Force analysis of native SDK tests with unchanged settings and baseline.
8. Prepare the current pull request template offline with exact results and limits.

The native tests call the imported shipped handler directly.
Literal HTTP statuses or `status_code` parameters reach the controlled transport.
Runtime evidence remains separate from static detector classification.
The plan makes no browser change, so it requires no browser server.

The coordinator's [fixture grant](https://github.com/jmorrison-juniper/MistHelper/issues/3743#issuecomment-5964719238)
permits concrete successful response fields in exactly three existing cases.
Their names, assertions, expected records, order, and alias membership remain unchanged.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing exporter exceeds five children | The user reserves one source boundary. | A module split needs unreserved source changes. |
| Existing test directories exceed five children | The user specifies two exact new test paths. | A new nested test package changes those reservations. |
| Standard branch and context hooks conflict with app constraints | The app owns this branch. Shared state is read-only. | Raw branch switching and shared context writes violate the request. |
