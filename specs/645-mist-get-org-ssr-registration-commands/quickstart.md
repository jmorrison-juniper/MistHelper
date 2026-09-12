# Quickstart: Menu 95 -- Get SSR Registration Command

**Feature**: `645-mist-get-org-ssr-registration-commands`
**Endpoint**: `GET /api/v1/orgs/{org_id}/ssr/register_cmd`
**Menu number**: 95 (Safe Org Exports / Config / Admin cluster)

This quickstart shows how a developer runs, tests, and validates the new menu item on a
Windows 11 workstation with a Python venv. Container / SSH-on-2200 usage is identical
except the operator connects through `ssh -p 2200 misthelper@<host>` and menu 95 appears
in the same list.

## Prerequisites

- Python 3.13+ installed and on PATH.
- Repo cloned to
  `C:\Users\<you>\...\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging\`.
- Virtual environment activated: `.venv\Scripts\Activate.ps1`.
- Dependencies installed: `pip install -r requirements.txt` (or `uv sync` if using UV).
- `.env` file at the repo root with valid credentials (see below).

## Required `.env` variables

| Variable          | Required | Example                                                            | Notes                                                                 |
|-------------------|----------|--------------------------------------------------------------------|-----------------------------------------------------------------------|
| `MIST_HOST`       | Yes      | `api.mist.com`                                                     | Regional API host. Never include scheme.                              |
| `MIST_API_TOKEN`  | Yes      | `abcd...ef01`                                                      | API token with org read permission. Never logged.                     |
| `MIST_ORG_ID`     | Optional | `11111111-2222-3333-4444-555555555555`                             | When set, seeds the prompt default so operator can press Enter.       |
| `MIST_OUTPUT`     | Optional | `csv`, `sqlite`, or `arangodb`                                     | Selects the DataExporter backend. Defaults to `csv` when unset.       |

Sensitive values are loaded through `python-dotenv` -- do not commit `.env`.

## How to run the menu item locally

Interactive (menu-driven):

```powershell
.\.venv\Scripts\Activate.ps1
python MistHelper.py
```

Then type `95` at the menu prompt and answer the three inputs.

Direct (non-interactive scripted invocation):

```powershell
python MistHelper.py --menu 95
```

`--menu 95` still prompts for the three inputs (`org_id`, `ttl`, `asset_ids`); use the
`--org-id`, `--ttl`, and `--asset-ids` flag pattern already established by adjacent menu
items when they are wired in during the tasks phase.

## Example invocation transcript

```text
> python MistHelper.py --menu 95
[INFO ] Menu 95 selected: Get SSR Registration Command (for router adoption)
Enter org UUID [11111111-2222-3333-4444-555555555555]:
Enter TTL seconds (blank = 1 year default):
Enter comma-separated asset UUIDs (blank = general token):
[INFO ] Fetching SSR registration command for org 11111111-2222-3333-4444-555555555555 ttl=default asset_ids=0
[DEBUG] SSR registration: conductor_cmd_len=142 router_shell_cmd_len=214 code_present=True
[INFO ] Writing 1 row to CSV: data\org_ssr_registration_commands_11111111-2222-3333-4444-555555555555_20260630_234100.csv
[INFO ] Menu 95 complete (exit 0)
```

The returned `registration_code` and `router_shell_cmd` values are visible only in the
output file, never in stdout / log lines.

## Expected `data/` output

- CSV: `data/org_ssr_registration_commands_<org_id>_<YYYYMMDD_HHMMSS>.csv` with one row
  and the columns from `data-model.md`.
- SQLite: One row appended to the `org_ssr_registration_commands` table in
  `data/mist_data.db`. The table is created on first run.
- ArangoDB + Redis (when configured): One document in the
  `org_ssr_registration_commands` collection and one Redis key
  `org:<org_id>:ssr:register_cmd:<epoch>` with a short TTL.

## Method contract summary (implementation hint)

The new method lives on `DeviceUtilityCommandsUtils` in `MistHelper.py`:

```python
def export_org_ssr_registration_commands(                                  # New menu 95 method
    self,                                                                  # Instance context (bound class method)
    org_id: str,                                                           # Required org UUID from safe_input()
    ttl: int | None = None,                                                # Optional TTL override in seconds
    asset_ids: list[str] | None = None,                                    # Optional asset UUID allowlist
) -> None:                                                                 # No return value -- writes to data/
    logging.info("Fetching SSR registration command for org %s ttl=%s asset_ids=%d",
                 org_id, ttl if ttl is not None else "default",
                 len(asset_ids) if asset_ids else 0)                       # Log INFO before the SDK call
    response = mistapi.api.v1.orgs.ssr.register_cmd.getOrgSsrRegistrationCommands(
        self.apisession, org_id, ttl=ttl, asset_ids=asset_ids,             # SDK call -- constitution mandates mistapi
    )                                                                      # ...
    payload = response.data or {}                                          # Guard against None
    logging.debug("SSR registration: conductor_cmd_len=%d router_shell_cmd_len=%d code_present=%s",
                  len(payload.get("conductor_cmd", "")),
                  len(payload.get("router_shell_cmd", "")),
                  bool(payload.get("registration_code")))                  # DEBUG only -- never log the secret
    registration_row = {                                                   # Shape one row for DataExporter
        "org_id": org_id,                                                  # Client-side key
        "ttl_requested_seconds": ttl,                                      # Track what the operator asked for
        "asset_ids_requested": json.dumps(asset_ids) if asset_ids else None,   # Preserve as JSON array text
        "conductor_cmd": payload.get("conductor_cmd"),                     # From API response
        "registration_code": payload.get("registration_code"),             # Short-lived secret
        "router_shell_cmd": payload.get("router_shell_cmd"),               # Full SSR shell command
        "fetched_at": datetime.now(timezone.utc).isoformat(),              # UTC ISO-8601 timestamp
    }
    DataExporter.write_with_format_selection(                              # Multi-backend persistence
        [registration_row],                                                # One row per fetch
        "org_ssr_registration_commands",                                   # Table / filename stem
        api_function_name="getOrgSsrRegistrationCommands",                 # Enables PK strategy lookup
    )
```

Total: 20 executable lines (under the 25-line Five-Item Rule budget). Four parameters
(including `self`, under the 5-param budget). Five logical blocks (log -> SDK call ->
shape -> log -> export -- exactly at the 5-block budget).

## Quality gates (must all pass before commit)

```powershell
# 1. Syntax check -- silent on success
python -m py_compile MistHelper.py

# 2. Lint -- must exit 0 with no findings
python -m ruff check MistHelper.py

# 3. Format check -- run without --check to auto-fix, then re-check
python -m black --check MistHelper.py

# 4. Test sweep -- menu 95 is in the default sweep range (not in the skip list 14, 18, 63-65, 90-100)
python MistHelper.py --test
```

All four gates green is the precondition for the container-build pipeline (see
`.github/copilot-instructions.md` "Full Deployment Pipeline").

## Troubleshooting

| Symptom                                                              | Likely cause                             | Fix                                                                             |
|----------------------------------------------------------------------|------------------------------------------|---------------------------------------------------------------------------------|
| `PermissionError: '/app/data/script.log'` on container start         | `data/` not writable                     | `chmod -R 777 data/` before starting the container                              |
| `401 Unauthorized` in logs                                           | Bad or expired `MIST_API_TOKEN`          | Regenerate in Mist UI and update `.env`                                         |
| `404 Not Found` in logs                                              | Wrong `org_id` or org lacks SSR feature  | Verify the UUID via menu 1 (list org sites) or the org-info menu               |
| Empty CSV / SQLite row (all API fields NULL)                         | API returned `{}`                        | Confirm SSR is enabled on the org and the operator has org-write scope         |
| `EOFError` traceback in SSH session                                  | `safe_input()` bypassed somewhere        | Every new prompt must use `safe_input(prompt, context="ssr_register_cmd:...")` |
