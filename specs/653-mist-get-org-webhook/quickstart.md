# Phase 1 Quickstart: getOrgWebhook (Menu 96)

**Feature**: 653-mist-get-org-webhook
**Endpoint**: `GET /api/v1/orgs/{org_id}/webhooks/{webhook_id}`
**Operation number (proposed)**: 96

## Prerequisites

- Python 3.13 or newer installed at the system level.
- Project virtual environment provisioned at `.venv` in the repo root (Windows
  standard environment per project conventions).
- Podman installed (optional; only required when running the container image
  instead of the local venv).
- `.env` file present at the repo root and readable.

## Required `.env` Variables

| Variable          | Required | Purpose                                                                          |
|-------------------|----------|----------------------------------------------------------------------------------|
| `MIST_HOST`       | Yes      | Mist API host, e.g. `api.mist.com`, `api.eu.mist.com`, or a private cloud host.  |
| `MIST_API_TOKEN`  | Yes      | API token for `mistapi.APISession`. Never logged.                                |
| `MIST_ORG_ID`     | No       | Default org UUID; when set, menu 96 accepts an empty `org_id` prompt to use it.  |
| `MIST_BACKEND`    | No       | Output backend selector consumed by `DataExporter`: `csv`, `sqlite`, or `arango`.|

## Expected Output

- **CSV**: `data/org_webhook_detail_<webhook_id>.csv` (one row).
- **SQLite**: table `org_webhook_detail` inside `data/mist_data.db`; primary
  key `id`; one row upserted per invocation.
- **ArangoDB + Redis**: collection `org_webhook_detail` and graph edge
  `webhook_detail_of_org` per the polyglot pattern (spec 188).

## Running the Menu Item Locally

### Interactive mode

```powershell
# Activate the local Python virtualenv (Windows 11 standard environment)
.venv\Scripts\Activate.ps1

# Launch MistHelper without arguments to enter the menu system
python MistHelper.py

# At the menu prompt, type 96 and press Enter
# You will then be prompted for:
#   Enter org_id (default: MIST_ORG_ID from .env):
#   Enter webhook_id (UUID from menu 47 output):
```

### Direct-invocation mode (automation-friendly)

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py --menu 96
# Same two prompts appear; safe_input() handles EOF gracefully in SSH
# and container contexts.
```

### Example session

```text
> python MistHelper.py --menu 96
Enter org_id (default: MIST_ORG_ID from .env): [ENTER accepts .env default]
Enter webhook_id (UUID from menu 47 output): 53f10664-3ce8-4c27-b382-0ef66432349f
2026-07-01 08:15:22 INFO Fetching webhook 53f10664-3ce8-4c27-b382-0ef66432349f for org a97c1b22-a4e9-411e-9bfd-d8695a0f9e61
2026-07-01 08:15:23 DEBUG Webhook name=noc-splunk-prod type=splunk enabled=True topics=6 secret=<redacted> splunk_token=<redacted>
2026-07-01 08:15:23 INFO Writing output via DataExporter (backend=csv)
2026-07-01 08:15:23 DEBUG Wrote data\org_webhook_detail_53f10664-3ce8-4c27-b382-0ef66432349f.csv (1 row)
> exit 0
```

## Implementation Sketch (matches Constitution VI + VII)

The new method lives on the existing webhook exporter class in `MistHelper.py`
(the class that owns menu 47 `listOrgWebhooks`). Every executable line carries
an inline comment; every meaningful action has a before / after log pair.

```python
    def export_org_webhook_detail(self, org_id: str, webhook_id: str) -> int:
        # Validate org_id shape before any API call to fail fast on typos.
        if not self._is_uuid(org_id):                                                       # UUID guard on user input
            logging.warning("Invalid org_id supplied to menu 96 export_org_webhook_detail") # ASCII-only warning
            return 1                                                                        # Exit code 1 signals validation failure
        # Validate webhook_id shape before any API call.
        if not self._is_uuid(webhook_id):                                                   # UUID guard on user input
            logging.warning("Invalid webhook_id supplied to menu 96 export_org_webhook_detail")
            return 1
        # Announce the outbound API request for observability.
        logging.info("Fetching webhook %s for org %s", webhook_id, org_id)                  # Principle VII before-call log
        # Delegate transport, auth, retry, and adaptive-delay to mistapi.
        response = mistapi.api.v1.orgs.webhooks.getOrgWebhook(self.session, org_id, webhook_id)  # Sole permitted Mist Cloud interface
        # Summarize the response with sensitive fields redacted.
        summary = self._redact_secrets(response.data)                                       # Redact secret / splunk_token / oauth2_* fields
        logging.debug(                                                                      # Principle VII after-call log
            "Webhook name=%s type=%s enabled=%s topics=%d",
            summary.get("name"),
            summary.get("type"),
            summary.get("enabled"),
            len(response.data.get("topics") or []),
        )
        # Persist via the multi-backend exporter; sensitive fields are stored raw.
        logging.info("Writing output via DataExporter (backend=%s)", self.backend)          # Principle VII before-write log
        DataExporter.write_with_format_selection(                                           # Multi-backend fan-out (CSV / SQLite / ArangoDB)
            data=[response.data],                                                           # Wrap the single object in a list for exporter contract
            filename=f"org_webhook_detail_{webhook_id}",                                    # No .csv suffix; exporter appends per-backend
            api_function_name="getOrgWebhook",                                              # Drives ENDPOINT_PRIMARY_KEY_STRATEGIES lookup
        )
        logging.debug("Wrote org_webhook_detail row for %s", webhook_id)                    # Principle VII after-write log
        return 0                                                                            # Exit code 0 signals success
```

## Quality Gates

Run every gate before committing. All three must pass clean.

```powershell
# Activate venv
.venv\Scripts\Activate.ps1

# 1. Byte-compile check (no output means valid syntax).
python -m py_compile MistHelper.py

# 2. Lint (Ruff must exit 0).
python -m ruff check MistHelper.py

# 3. Format check (Black must exit 0; run without --check to auto-fix).
python -m black --check MistHelper.py

# 4. Test invocation of the new menu item.
python MistHelper.py --menu 96
# Provide a known-good org_id (or accept the .env default) and a webhook_id
# obtained from a prior menu 47 run. Expect exit code 0 and one row in
# data/org_webhook_detail_<webhook_id>.csv (or in the configured backend).

# 5. Repeat-run idempotency check (SQLite backend).
$env:MIST_BACKEND = "sqlite"
python MistHelper.py --menu 96    # First run inserts.
python MistHelper.py --menu 96    # Second run upserts, no duplicate PK.
```

## Post-Commit Deployment Pipeline

After all gates pass:

```powershell
git add MistHelper.py README.md CHANGELOG.md
git commit -m "version YY.MM.DD.HH.MM - add menu 96 getOrgWebhook"
git push origin main

# Watch the container-build workflow.
gh run list --workflow=container-build.yml --limit 1
gh run watch <run-id>

# Pull the freshly built image and restart the local container.
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest

# Verify.
podman ps
```

## Troubleshooting

| Symptom                                                                 | Likely Cause                                              | Fix                                                                                       |
|-------------------------------------------------------------------------|-----------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `PermissionError: [Errno 13] ... /app/data/script.log`                  | `data/` directory is not writable by the container user   | `chmod -R 777 data/` on the host before `podman run`.                                     |
| `404 Not Found`                                                         | Wrong `org_id` or `webhook_id`                            | Re-run menu 47 to enumerate webhooks; copy the exact UUID.                                |
| `403 Permission Denied`                                                 | API token lacks read permission on the org                | Verify `MIST_API_TOKEN` scope in the Mist admin console.                                  |
| `EOFError` traceback under SSH                                          | `safe_input()` not applied to a new prompt                | Confirm every `input(...)` in the new method is wrapped in `safe_input(..., context=...)`.|
