# Implementation Plan: Menu 256 Webhook Control

**Branch**: `jmorrison-juniper-endpoint-explorer-sweep-3188`  
**Date**: 2026-10-06  
**Spec**: `specs/3188-menu-256-webhook-control/spec.md`

**Input**: The approved issue #3188 specification and the assigned implementation file set.

## Summary

Add one exact Flask route for menu 256 parameter data. The route will use a dedicated provider that reads organization webhooks through `mistapi`.

The route will return the existing portal choice shape. Each option value will use the stable webhook identifier.

Extend the exporter resolver to accept a stable identifier or a displayed one-based number. An exact identifier match will take precedence.

Keep the generic parameter route and the existing JavaScript unchanged. Add mocked unit and browser coverage with zero live Mist calls.

## Assigned Scope

The implementation will change only these files:

```text
specs/3188-menu-256-webhook-control/spec.md
specs/3188-menu-256-webhook-control/plan.md
specs/3188-menu-256-webhook-control/tasks.md
web_portal/routes/settings.py
src/operations/exporting/export/org_webhook_deliveries_exporter.py
tests/unit/web_portal/test_issue_3188_webhook_parameters.py
tests/unit/export/test_issue_3188_webhook_id_selection.py
tests/e2e/web_portal/test_issue_3188_webhook_control.py
changelog.d/issue-3188-menu-256-webhook-control.md
```

The implementation will not change these files:

```text
web_portal/services/operation.py
web_portal/static/js/operations.js
web_portal/routes/operations.py
tests/unit/export/test_org_webhook_deliveries_exporter.py
```

Open pull requests modify some untouched files. This plan avoids those files and prevents overlap.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Flask, `mistapi>=0.64.0,<0.65`, pytest, and Playwright.

**Storage**: Existing CSV, SQLite, ArangoDB, and Redis export paths remain unchanged.

**Testing**: pytest unit tests, Flask test clients, and one Playwright browser journey.

**Target Platform**: Windows 11, macOS, Linux, and the existing Podman image.

**Project Type**: Python command-line application with a Flask web portal.

**Performance Goals**: Add one Mist list request per menu 256 parameter request. Add no polling or repeated browser request.

**Constraints**:

- Use the exact static route `/api/operations/parameters/256`.
- Use only `mistapi.api.v1.orgs.webhooks.listOrgWebhooks` for webhook choices.
- Preserve `searchOrgWebhooksDeliveries` for the delivery search.
- Preserve the current choice JSON shape and existing JavaScript behavior.
- Use stable webhook identifiers as browser option values.
- Preserve one-based command-line selection.
- Make an exact identifier match before positional parsing.
- Make no live Mist request in any feature test.
- Create no research, data model, contract, or quickstart artifact.

**Scale/Scope**: One parameter route, one provider, one exporter resolver change, and three focused test modules.

## Constitution Check

### Pre-Design Gate

| Gate | Result | Evidence |
| --- | --- | --- |
| Mist SDK boundary | PASS | The provider uses `listOrgWebhooks`. The exporter retains `searchOrgWebhooksDeliveries`. |
| Direct HTTP prohibition | PASS | The design adds no direct Mist REST request. |
| Input validation | PASS | The resolver validates stable identifiers and one-based positions before the delivery search. |
| Secret handling | PASS | Logs contain organization and webhook identifiers, but no token or password. |
| Output boundary | PASS | The existing exporter and storage path remain unchanged. |
| Destructive-operation safety | PASS | Menu 256 is read-only and does not change Mist Cloud state. |
| Test isolation | PASS | Each Mist method is mocked. No test uses a credential or live session. |
| Assigned file ownership | PASS | The design changes only the explicit file set. |
| Release note | PASS | The assigned changelog fragment records the user-visible portal repair. |
| Specification requirement | PASS | The approved specification covers the multi-file portal and exporter change. |

### Hierarchy Check

The revised assignment in coordination issue #3959 comment 6013568037 uses the existing `web_portal/routes/settings.py` module. The change adds no child to a noncompliant folder.

### Post-Design Gate

The design introduces no direct HTTP transport, schema change, destructive action, or new dependency.

The stable identifier crosses the existing browser input queue without a JavaScript change. The exporter validates it before the delivery search.

## Project Structure

### Documentation

```text
specs/3188-menu-256-webhook-control/
├── spec.md
├── plan.md
└── tasks.md
```

No other Spec Kit artifact will be created for this feature.

### Implementation

```text
web_portal/
└── routes/
    └── settings.py

src/operations/exporting/export/
└── org_webhook_deliveries_exporter.py

tests/
├── unit/
│   ├── export/
│   │   └── test_issue_3188_webhook_id_selection.py
│   └── web_portal/
│       └── test_issue_3188_webhook_parameters.py
└── e2e/web_portal/
    └── test_issue_3188_webhook_control.py

changelog.d/
└── issue-3188-menu-256-webhook-control.md
```

**Structure Decision**: Separate the Mist choice read from the Flask response. Keep exporter selection logic in its existing subject class.

## Design

### 1. Webhook Choice Provider

Add `OrgWebhookChoiceProvider` in `web_portal/routes/settings.py`.

The provider will receive the active Mist session and organization identifier. It will validate both values before an SDK call.

The provider will call `mistapi.api.v1.orgs.webhooks.listOrgWebhooks`. It will collect pages through `mistapi.get_all`.

The provider will preserve the Mist row order. It will not sort by name or identifier.

The provider will skip a row without a usable `id`. It will not invent an identifier.

Each valid row will become this existing option shape:

```json
{"value": "stable-webhook-id", "label": "Readable webhook name"}
```

If the name is empty, the label will equal the stable identifier.

Duplicate names will remain separate because each option value uses its identifier.

An empty successful list will return an empty option list. An SDK failure or failed HTTP response will produce an explicit provider failure.

The provider will log before and after the Mist read. It will log counts and status, but it will not log credentials.

### 2. Exact Static Parameter Route

Add the exact route to the existing `settings_bp` in `web_portal/routes/settings.py`.

Register only this exact route:

```text
GET /api/operations/parameters/256
```

The route will read `APISESSION` and `ORG_ID` from `current_app.config`. It will pass them to `OrgWebhookChoiceProvider`.

A successful response will use the current operation parameter envelope and one choice parameter:

```json
{
  "menu_number": "256",
  "description": "<existing menu 256 title>",
  "category": "interactive",
  "parameters": [
    {
      "name": "webhook_id",
      "label": "Webhook",
      "param_type": "choice",
      "required": true,
      "options": []
    }
  ]
}
```

The route will read the menu title from the existing menu action entry. It will not duplicate the title as a new constant.

An empty successful webhook list will return HTTP 200 with the same parameter shape and zero options.

A missing session or organization identifier will return a clear non-success JSON response. A Mist list failure will return HTTP 503.

The response will never use cached, partial, or fabricated webhook options after a failure.

Flask will resolve the exact static route before the existing variable route. A route test will prove this resolution.

### 3. Blueprint Registration

Use the existing always-registered `settings_bp`. Do not change `web_portal/app.py`.

Do not add a special case to `web_portal/routes/operations.py`. Do not add menu 256 to `PARAMETER_REGISTRY`.

### 4. Exporter Selection Resolution

Update `OrgWebhookDeliveriesExporter._resolve_webhook_choice()`.

Normalize the supplied value as a trimmed string. Reject an empty value before any search.

First, compare the supplied value with each nonempty webhook `id`. Return the exact matching identifier and display name.

This first pass gives stable identifiers priority. A numeric identifier will not be mistaken for a one-based position.

If no identifier matches, accept digits as the existing one-based command-line position. Validate the range before indexing.

Reject zero, negative values, nonnumeric values, unknown identifiers, and positions beyond the current list.

Reject a selected row without a usable identifier. Do not call `searchOrgWebhooksDeliveries` after any invalid selection.

Use the webhook name as the display name when present. Use the identifier as the fallback display name.

Keep `_select_webhook_id()` and `deliveries()` as the single list and search flow. Preserve the existing export file and persistence behavior.

### 5. Existing JavaScript Contract

Do not change `web_portal/static/js/operations.js`.

The existing code already fetches `/api/operations/parameters/<menu>`, renders `param_type: "choice"`, and queues the selected option value.

The new exact route will supply the expected shape. The selected stable identifier will enter `input_answers` without a browser code change.

### 6. Release Note

Add `changelog.d/issue-3188-menu-256-webhook-control.md`.

Use one `### Fixed` heading. State that menu 256 now lists organization webhooks and keeps command-line number selection.

## Test Plan

### Portal Unit Tests

Add `tests/unit/web_portal/test_issue_3188_webhook_parameters.py`.

Use a bare Flask app with the new blueprint. Set mocked `APISESSION`, `ORG_ID`, and menu actions in app configuration.

Mock `listOrgWebhooks` and `mistapi.get_all`. Cover these cases:

1. The exact route returns one required `webhook_id` choice control.
2. Option values use stable identifiers.
3. Names become labels, and empty names use identifiers.
4. Mist order remains unchanged.
5. Duplicate names remain distinct.
6. Rows without identifiers do not become options.
7. An empty list returns HTTP 200 with zero options.
8. An HTTP 4xx or 5xx list response returns a non-success result.
9. An SDK exception returns a non-success result.
10. A failure returns no stale or fabricated options.
11. The exact static route wins over the existing variable route.

Each test will use a local response double. No test will create a real Mist session.

### Exporter Unit Tests

Add `tests/unit/export/test_issue_3188_webhook_id_selection.py`.

Keep `tests/unit/export/test_org_webhook_deliveries_exporter.py` unchanged.

Cover these cases:

1. An exact stable identifier resolves to its webhook.
2. Reordered webhooks do not change an identifier result.
3. A numeric identifier match takes precedence over a positional match.
4. A valid one-based number still selects the displayed row.
5. A missing name uses the identifier.
6. An unknown identifier is rejected.
7. Empty, zero, negative, nonnumeric, and out-of-range inputs are rejected.
8. A positional row without an identifier is rejected.
9. Every invalid selection results in zero delivery-search calls.
10. A valid stable identifier reaches `searchOrgWebhooksDeliveries` once with the selected identifier.

Patch `InputUtils.safe_input`, both Mist SDK methods, pagination, and persistence. Use no live API token.

### Browser Test

Add `tests/e2e/web_portal/test_issue_3188_webhook_control.py`.

Serve the real Flask portal with a mocked Mist session and a mocked webhook list. Use the existing Playwright fixture and an ephemeral loopback port.

The browser journey will:

1. Open the operations page.
2. Select menu 256.
3. Wait for the parameter request to finish.
4. Verify one visible `Webhook` choice control.
5. Verify each option value is a stable identifier.
6. Verify the Run button remains disabled without a selection.
7. Select one webhook.
8. Start the operation through the existing JavaScript.
9. Verify the queued input answer equals the selected stable identifier.

Use a recording menu handler or a local request recorder. Do not call Mist Cloud.

The test will stop its server thread and release its ephemeral port in fixture cleanup.

## Validation

Run these focused checks after implementation:

```text
python -m pytest tests/unit/web_portal/test_issue_3188_webhook_parameters.py
python -m pytest tests/unit/export/test_issue_3188_webhook_id_selection.py
python -m pytest tests/e2e/web_portal/test_issue_3188_webhook_control.py
python -m pytest tests/integration/test_mistapi_sdk_compatibility.py
python -m ruff check web_portal/routes/settings.py src/operations/exporting/export/org_webhook_deliveries_exporter.py tests/unit/web_portal/test_issue_3188_webhook_parameters.py tests/unit/export/test_issue_3188_webhook_id_selection.py tests/e2e/web_portal/test_issue_3188_webhook_control.py
python -m black --check web_portal/routes/settings.py src/operations/exporting/export/org_webhook_deliveries_exporter.py tests/unit/web_portal/test_issue_3188_webhook_parameters.py tests/unit/export/test_issue_3188_webhook_id_selection.py tests/e2e/web_portal/test_issue_3188_webhook_control.py
bandit -c pyproject.toml -r web_portal/routes/settings.py src/operations/exporting/export/org_webhook_deliveries_exporter.py -q
```

Run the test quality preflight and changed-test gate after the implementation commit, as the repository instructions require.

The current directive permits a local commit. It prohibits rebase, merge, and auto-merge. Run the changed-test gate after the local commit.

## Local Validation Result

The focused unit tests passed with 25 tests.

The browser test passed with one test. Its fixture stopped the owned server thread and closed the port.

The Mist SDK compatibility tests passed with eight tests and 544 checked call signatures.

Ruff, Black, Bandit, pydocstyle, mypy, complexity, and the test quality preflight passed.

Each feature test mocked every Mist request. No feature test used a live Mist session.

## Implementation Order

1. Add the provider to the existing settings route module and add its focused unit tests.
2. Add the exact route to the already registered settings blueprint.
3. Add route shape, empty-list, and failure tests.
4. Extend the exporter resolver and add the new exporter test module.
5. Add the Playwright journey through the existing JavaScript.
6. Add the changelog fragment.
7. Run the focused tests and applicable quality gates.

## Risks and Controls

| Risk | Control |
| --- | --- |
| The variable parameter route handles menu 256 instead of the new route. | Register an exact static rule and assert route resolution in a unit test. |
| A webhook reorder changes the selected webhook. | Use stable identifiers and test the same identifier across reordered lists. |
| A numeric identifier becomes a positional number. | Resolve exact identifiers before positional parsing. |
| The portal and command line diverge. | Keep one resolver that accepts both stable identifiers and one-based numbers. |
| A failed list appears as an empty success. | Separate empty success from SDK and HTTP failures. Return a non-success response for failures. |
| Invalid input reaches the delivery search. | Stop at resolver failure and assert zero search calls. |
| JavaScript changes create overlap with an open pull request. | Use the existing choice shape and leave `operations.js` unchanged. |
| Existing exporter tests conflict with an open pull request. | Add a new issue-specific test module and leave the existing module unchanged. |
| Tests reach Mist Cloud. | Patch every SDK and pagination boundary. Use local sessions and response doubles only. |
| A new direct route child increases existing folder debt. | Keep the route and provider in the assigned existing settings module. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Add two subject classes to `web_portal/routes/settings.py`. | The revised assignment keeps the exact route on an always-registered blueprint without adding a folder child. | The generic route and operation service are protected by open pull request ownership. |
