# Quickstart: Validate Menu 209 HTTP Error Handling

Use this guide after implementation. Run each command from the repository root.
Do not use a live Mist credential for the focused tests.

## Prerequisites

1. Use Python 3.13 or newer.
2. Bootstrap the worktree if `.venv` does not exist.
3. Keep the issue specification and planning artifacts unchanged.

```powershell
python scripts/bootstrap_worktree.py
```

## 1. Verify the implementation boundary

```powershell
git status --short --untracked-files=all
git diff -- src/operations/exporting/export/site_client_exporter.py tests/unit/export/test_site_client_exporter.py changelog.d/issue-4028-menu-209-http-errors.md
```

Expected result:

- The implementation changes only the planned production file, unit test
  file, and unique changelog fragment.
- `src/operations/exporting/export/simple_endpoint_exporter.py` has no change.
- The existing `.specify/feature.json` and issue specification changes remain
  present and preserved.
- The completed `tasks.md` records the implementation and validation evidence.

## 2. Run the focused unit regressions

```powershell
python -m pytest tests/unit/export/test_site_client_exporter.py -k "GetSiteBeacon" -v
```

Expected result:

- HTTP 404 emits exactly
  `! Error fetching site beacon detail: HTTP 404 from <url>`.
- HTTP 404, HTTP 429, and HTTP 500 call no exporter.
- Integer 1xx, 3xx, 4xx, and 5xx responses do not read or normalize payloads.
- A native HTTP 429 response does not retry.
- A thrown 429 error still uses adaptive delay and retries.
- Successful dictionary and empty responses keep existing behavior.
- Statusless and non-integer responses keep compatibility behavior.
- The classification test fails if it accesses the response body or
  `data["detail"]`.

## 3. Run menu wiring regression tests

```powershell
python -m pytest tests/integration/test_menu_site_beacon_detail.py -v
```

Expected result:

- Menu 209 still dispatches to `get_site_beacon`.
- The menu description still names `getSiteBeacon`.

## 4. Run related identity and portal regressions

```powershell
python -m pytest tests/unit/export/test_site_client_exporter.py tests/integration/test_menu_site_beacon_detail.py tests/unit/web_portal/test_portal_silent_completion.py -v
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -v
```

Expected result:

- The filename and `api_function_name` expectations remain unchanged.
- Portal prompt controls remain unchanged.
- The issue-specific changelog fragment follows repository policy.

## 5. Run static checks for the touched Python files

```powershell
python -m py_compile src/operations/exporting/export/site_client_exporter.py tests/unit/export/test_site_client_exporter.py
python -m ruff check src/operations/exporting/export/site_client_exporter.py tests/unit/export/test_site_client_exporter.py
python -m black --check --diff src/operations/exporting/export/site_client_exporter.py tests/unit/export/test_site_client_exporter.py
python -m mypy src/operations/exporting/export/site_client_exporter.py --config-file pyproject.toml
```

Expected result:

- Compilation has no output.
- Ruff reports `All checks passed`.
- Black reports no required change.
- Mypy reports success.

## 6. Run source and change hygiene checks

```powershell
git diff --check
python -m pytest tests/guardrails/test_src_public_symbol_preservation.py -v
```

Expected result:

- Git reports no whitespace error.
- No module-level public symbol is removed.

## 7. Review the exact response contract

Read:

- [Response classification contract](contracts/menu-209-response-classification.md)
- [Data model](data-model.md)
- [Research decisions](research.md)

Confirm these outcomes:

1. Status is inspected before payload data.
2. Integer status 200-299 succeeds.
3. Every other integer status fails.
4. Absent and non-integer status preserves the current payload path.
5. Classification never reads or logs the body or `data["detail"]`.
6. The operator line has the exact required text.
7. Native HTTP 429 does not use the exception retry path.
8. Exception-based HTTP 429 behavior remains unchanged.
9. Successful exports keep the current filename and primary key.
10. `simple_endpoint_exporter.py` remains unchanged.
