# Data Model: Converter Privacy and Shared Portal Integration

This integration stores no new data. The entities below describe what the tests check and what the owners track. Each entity has a natural key.

## ComparisonRow

- **Key**: `row_id`, one of C01 to C40 from the live comparison table (`design/research.md` lines 85 to 124 in the full-parity record).
- **Fields**: `capability`, `current_state`, `target`, `requirement_ids`, `linked_tests`, `remaining_task`, and `owner`.
- **Current state values**: Missing, Partial, Implemented, Unsupported, and Requiring approval. The live table uses these values.
- **Disposition values**: `verified`, `remaining-task`, `owner-unsupported`, and `open-decision`.
- **Transitions**:
  - Missing moves to Partial when one test covers part of the row.
  - Partial moves to `verified` when every linked test passes.
  - Requiring approval moves to `open-decision`, then to `verified` after the owner records the decision.
  - Unsupported moves to `owner-unsupported` after the owner records the decision.
- **Rule**: A row without a disposition fails `test_comparison_rows_have_dispositions`.

## PortalRoute

- **Key**: the pair of method and rule.
- **Approved set**: the five rules below. Test `test_route_allowlist_has_no_cloud_write_route` checks this set.
  - GET `/cisco-config-converter/`
  - POST `/cisco-config-converter/preview`
  - POST `/cisco-config-converter/review`
  - POST `/cisco-config-converter/export`
  - GET `/cisco-config-converter/assets/<path:filename>`
- **Transition**: A new rule needs owner approval and an allowlist change. Issue #4644 owns the first such change.

## HealthReply

- **Key**: the request path, `/health` or `/ready`.
- **`/health` fields**: `status` with the value `healthy`, `services` with the value `{"web_portal": "running"}`, and `uptime_seconds` as an integer of zero or more. Source: `web_portal/routes/dashboard.py` lines 60 to 66.
- **`/ready` fields**: `status` with the value `ready` or `not ready`. Source: `web_portal/routes/dashboard.py` line 83.
- **Transition**: None. The reply reflects the process state at request time.
- **Rule**: Registration must not add a key to `services`.

## CsrfAnswer

- **Key**: the request class and the negotiated media type.
- **Request classes**: the converter prefix, the `/api/` prefix, and all other paths.
- **Media type**: JSON when the path starts with `/api/` or `Accept` prefers `application/json`. HTML otherwise. Source: `web_portal/services/config.py` lines 333 to 338.
- **JSON fields**: `error` with a safe message, `code` with the value `csrf_expired`, and `detail` with the library description. Status 400 (line 328).
- **HTML answer**: The Flask-WTF error page, with status 400 (line 321).

## HandoverRecord

- **Key**: the shared path and the owner pull request. Shared paths are `web_portal/app.py` and `web_portal/templates/base.html`. The owner pull request is #4208.
- **States**: `pending` (the default), `recorded` (the coordinator comment names both paths and the prerequisites), and `released` (the owner pull request closed or merged).
- **Transitions**:
  - `pending` moves to `recorded` when the coordinator posts the comment on issue #4648.
  - `recorded` moves to `released` when PR #4208 closes or merges.
- **Rule**: Tasks T009 and T010 need the state `recorded` and the state `released`. Test `test_handover_state_matches_shared_files` reads the checklist for the state.

## BrowserEvidence

- **Key**: the pytest node ID of the failed browser test.
- **Path**: `test-artifacts/cisco-portal/<test name>.png`.
- **Lifetime**: Local only. Git ignores the folder (`.gitignore` line 107).
- **Transition**: Created on failure only. A passing test creates no file.
