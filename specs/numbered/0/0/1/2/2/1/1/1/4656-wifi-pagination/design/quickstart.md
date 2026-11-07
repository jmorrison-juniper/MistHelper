# Quickstart: WiFi Pagination Failure Handling

## Prerequisites

- Use the repository worktree environment created by `python3 scripts/bootstrap_worktree.py`.
- Use the controlled SDK response helpers in `tests/support/sdk_pages.py`.
- Do not set Mist credentials or make live Mist requests.

## Validation

Run the focused unit and integration tests:

```sh
python -m pytest tests/unit/export/test_wifi_clients_exporter.py tests/unit/export/test_wifi_clients_response_failures.py tests/integration/export/test_wifi_clients_native_response_failures.py -q
```

Expected results:

- Successful pages produce the same complete records as before.
- A later transport timeout retains earlier records and reports a partial result.
- Later HTTP 403 and 503 responses stop the export and do not create a success-shaped placeholder.
- First-page failure and successful empty-result behavior remain unchanged.
- The controlled session records only the planned SDK page links.

For the relevant managed-route guard, run:

```sh
python -m pytest tests/guardrails/test_process_folder_structure.py -q
```

The implementation must not change `.specify/feature.json`.
