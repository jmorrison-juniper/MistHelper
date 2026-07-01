# Phase 1 Quickstart: getOrgService (Menu 195)

**Feature**: 637-mist-get-org-service
**Date**: 2026-06-30

## Purpose

Run the new "Get single Org Service by UUID" menu item locally on Windows 11, verify output
lands in `data/`, and run the four quality gates before commit.

## Prerequisites

1. Windows 11 with Python 3.13+ on PATH.
2. Local venv activated:
   ```powershell
   cd "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging"
   .venv\Scripts\Activate.ps1
   ```
3. `.env` present at repo root (git-ignored) with at minimum:
   ```dotenv
   MIST_HOST=api.mist.com                         # regional cloud host, e.g. api.eu.mist.com
   MIST_API_TOKEN=<personal api token>            # never commit; loaded by GlobalImportManager
   MIST_ORG_ID=<uuid of target org>               # default org_id, override at prompt if needed
   ```
4. `data/` directory exists and is writable (777 required if you ever ran the container image
   locally; see `.github/copilot-instructions.md` "Data Directory Permissions").
5. A known valid `service_id` UUID from the target org (obtain by first running menu 4
   `listOrgServices` and picking any `id` value from the exported `data/org_services.csv`).

## Environment Variables Consumed

| Variable | Required | Purpose |
|----------|----------|---------|
| `MIST_HOST` | Yes | Regional Mist Cloud host used by mistapi.APISession. |
| `MIST_API_TOKEN` | Yes | Bearer token sent as `Authorization: Token`. |
| `MIST_ORG_ID` | Yes (default) | Used unless the operator overrides at the prompt. |
| `MIST_PAGE_LIMIT` | No | Ignored -- endpoint is not paginated. |

## Run the Menu Item

**Interactive**:
```powershell
python MistHelper.py
# At the main menu, enter: 195
# Prompt 1: "Override org_id (blank = use MIST_ORG_ID): "  -> press Enter
# Prompt 2: "Enter service_id UUID: "                       -> paste UUID
```

**Direct dispatch (automation-friendly)**:
```powershell
python MistHelper.py --menu 195
# Same two prompts follow; both go through safe_input() for EOF-safe SSH/container use.
```

## Expected Output

- **CSV backend**: `data/org_services_detail.csv` -- one row for the requested service, columns
  matching the flattened Service schema (nested JSON blobs preserved as JSON text).
- **SQLite backend**: `data/mist_data.db` table `org_services` -- one row upserted via
  `INSERT OR REPLACE` on `id`. Re-running the menu with the same `service_id` MUST NOT create a
  duplicate row.
- **ArangoDB+Redis backend** (if configured): document upserted into the `org_services`
  collection keyed by `id`; Redis cache entry `org_services:<id>` refreshed.
- **Log stream** (ASCII only):
  ```
  INFO  MistHelper: Fetching service <uuid> from org <org_uuid>
  DEBUG MistHelper: getOrgService returned 27 field(s); persisted to data/org_services_detail.csv
  ```

## Edge-Case Behaviours to Spot Check

| Scenario | Expected observable |
|----------|--------------------|
| Unknown `service_id` (404) | `logging.warning("Service <uuid> not found in org <uuid> (HTTP 404)")`, exit code 0, no file written or empty CSV header only. |
| Bad token (401) | Warning logged, exit code 0, no traceback. |
| Rate limit (429) | Adaptive delay kicks in from `delay_metrics.json`; call auto-retries. |
| EOF on either prompt (SSH disconnect) | `safe_input()` catches EOFError, logs the context, `sys.exit(0)`. |
| `--fast` flag added | Fewer retries, higher concurrency; behaviour otherwise identical. |

## Quality Gates (run before every commit)

Run all four from the repo root. All must pass clean:

```powershell
python -m py_compile MistHelper.py                 # syntax gate; no output on success
python -m ruff check MistHelper.py                 # lint gate; must exit 0
python -m black --check MistHelper.py              # format gate; drop --check to auto-fix if needed
python MistHelper.py --test                        # smoke-test harness; menu 195 must be in the safe-run list
```

If any gate fails, fix the code (do not suppress). Security findings from bandit / pip-audit /
CodeQL follow the same rule per Constitution "Security Findings: Fix Over Suppress".

## Post-Commit Deployment

Follow the mandatory pipeline in `.github/copilot-instructions.md` -- MANDATORY: Full Deployment
Pipeline (commit with `version YY.MM.DD.HH.MM`, push to `main`, wait for
`container-build.yml`, `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`, restart
container, verify with `podman ps`).

## Inline-Comment Style Reminder (Constitution VI)

Every executable line added for this feature MUST carry a same-line inline comment. Example
target style for the new method:

```python
service_id = safe_input("Enter service_id UUID: ", context="get_org_service")  # per-request path param, EOF-safe
logging.info("Fetching service %s from org %s", service_id, org_id)  # Action Logging: before call
response = mistapi.api.v1.orgs.services.getOrgService(apisession, org_id, service_id)  # single-object GET
data = response.data if response and response.data else {}  # normalize empty response to dict
logging.debug("getOrgService returned %d field(s)", len(data))  # Action Logging: after call
DataExporter.write_with_format_selection(data, "org_services_detail", api_function_name="getOrgService")  # multi-backend persist
```
