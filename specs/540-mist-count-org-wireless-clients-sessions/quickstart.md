# Phase 1 Quickstart: countOrgWirelessClientsSessions (Menu 195)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-06-29

Local-developer quickstart for running and validating the new menu item.

## 1. Prerequisites

- Python 3.13+
- `mistapi` 0.59 or newer (`pip install -r requirements.txt`)
- A populated `.env` file at the repo root (never committed)

## 2. Required `.env` Variables

```env
# Mist API endpoint -- one of api.mist.com, api.eu.mist.com, api.gc1.mist.com, etc.
MIST_HOST=api.mist.com

# API token for the user running MistHelper. Generated in the Mist UI under
# My Account -> API Tokens. Never log this value.
MIST_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Default org for non-interactive testing. The menu item still prompts at
# runtime; pressing Enter accepts this default.
MIST_ORG_ID=00000000-0000-0000-0000-000000000000
```

## 3. Expected `data/` Output Filenames

After a successful run, MistHelper writes the following under `data/`:

- `data/count_org_wireless_clients_sessions_summary.csv` -- one row per
  invocation
- `data/count_org_wireless_clients_sessions_results.csv` -- one row per
  bucket returned in `results[]`
- `data/mist_data.db` -- gets the two matching SQLite tables on first run
  (DDL listed in `data-model.md`)
- ArangoDB and Redis (if configured) receive identical rows; no extra
  steps needed.

## 4. Interactive Invocation

```powershell
# Activate the venv (Windows 11 standard env).
.venv\Scripts\Activate.ps1

# Launch MistHelper and select the new menu item.
python MistHelper.py
```

Expected prompt sequence:

```text
Select menu option: 195
[INFO] Counting wireless client sessions for org 00000000-... distinct=ssid duration=1d
Org ID [default: 00000000-0000-0000-0000-000000000000]: <Enter>
Distinct attribute (ssid|ap|band|client_family|client_manufacture|client_model|client_os|wlan_id) [ssid]: <Enter>
Duration window (e.g. 1d, 7d, 2w) [1d]: 7d
[INFO] Calling mistapi countOrgWirelessClientsSessions org=00000000-... distinct=ssid duration=7d
[DEBUG] Count response: total=12 buckets=12
[INFO] Flattening 12 result buckets
[DEBUG] Flatten produced summary_rows=1 result_rows=12
[INFO] Writing output via DataExporter
[DEBUG] DataExporter completed backend=sqlite tables=2
```

## 5. Non-Interactive Invocation (used by --test)

```powershell
# Runs the menu item directly with defaults pulled from .env.
python MistHelper.py --menu 195
```

The non-interactive code path uses `MIST_ORG_ID` for `org_id`, `ssid` for
`distinct`, and `1d` for `duration`. `safe_input()` short-circuits to the
default on EOF, so this works identically in SSH sessions and inside the
container.

## 6. Method Outline (for reviewers)

The new method lives on `OrgClientSecurityExporter` (MistHelper.py line 11267).
Outline shown with the mandated inline comments and action logs; the actual
implementation lands during `/speckit.implement`.

```python
def export_count_org_wireless_clients_sessions(
    self,
    org_id: str | None = None,             # Org UUID; defaults to MIST_ORG_ID env var
    distinct: str | None = None,           # Bucket attribute; defaults to "ssid"
    duration: str | None = None,           # Time window; defaults to "1d"
) -> None:                                  # Read-only export -- no return value needed
    """Menu 195 -- count wireless client sessions grouped by a distinct attribute."""
    org_id = org_id or os.getenv("MIST_ORG_ID", "")                             # Pull default org from .env when not supplied
    org_id = safe_input(                                                        # Wrap input for SSH/container EOF safety
        f"Org ID [default: {org_id}]: ",                                        # Show the default so the user can press Enter
        context="count_wireless_sessions:org_id",                               # Context string aids EOF log triage
    ) or org_id                                                                 # Reuse the env default on empty input
    distinct = (safe_input(                                                     # Same safe-input wrapper for the distinct attribute
        "Distinct attribute [ssid]: ",                                          # Document the accepted enum elsewhere; default to ssid
        context="count_wireless_sessions:distinct",                             # Distinct context tag for log correlation
    ) or "ssid").strip()                                                        # Strip stray whitespace from interactive shells
    duration = (safe_input(                                                     # Final prompt: time window
        "Duration window (e.g. 1d, 7d, 2w) [1d]: ",                             # 1d matches the documented API default
        context="count_wireless_sessions:duration",                             # Tag for EOF-context logging
    ) or "1d").strip()                                                          # Empty input falls back to the API default
    if not _is_valid_uuid(org_id):                                              # Validate before any network call to avoid 404 noise
        logging.warning("Invalid org_id %s -- aborting menu 195", org_id)       # ASCII-only warning, no token in the line
        return                                                                  # Early return preserves the 5-Item Rule budget
    logging.info(                                                               # Action log BEFORE the SDK call (Principle VII)
        "Counting wireless client sessions org=%s distinct=%s duration=%s",     # Format string keeps secrets out of the message
        org_id, distinct, duration,                                             # Bound args use lazy %s formatting
    )
    response = mistapi.api.v1.orgs.clients.sessions.count.countOrgWirelessClientsSessions(  # The one permitted SDK entry point
        self.apisession, org_id, distinct=distinct, duration=duration, limit=1000,          # Clamp limit at 1000 (well within API max)
    )
    payload = response.data or {}                                               # Defensive: tolerate empty bodies on 204-like responses
    logging.debug(                                                              # Action log AFTER the SDK call (Principle VII)
        "Count response total=%s buckets=%s",                                   # Lazy formatting; no secrets in the log line
        payload.get("total"), len(payload.get("results", [])),                  # total + bucket count are safe to log
    )
    summary_row, result_rows = self._flatten_session_count(payload, org_id, duration)  # Helper splits the JSON into two flat tables
    DataExporter.write_with_format_selection(                                   # Single facade for CSV/SQLite/ArangoDB+Redis output
        data=[summary_row],                                                     # Summary row goes first; helper returns one element
        filename="count_org_wireless_clients_sessions_summary",                 # No extension -- DataExporter appends per backend
        api_function_name="countOrgWirelessClientsSessions",                    # Keys into ENDPOINT_PRIMARY_KEY_STRATEGIES
    )
    DataExporter.write_with_format_selection(                                   # Second call writes the per-bucket detail table
        data=result_rows,                                                       # Possibly empty list -- DataExporter handles that
        filename="count_org_wireless_clients_sessions_results",                 # Companion table name documented in data-model.md
        api_function_name="countOrgWirelessClientsSessions",                    # Same PK strategy entry applies to both tables
    )
```

The helper `_flatten_session_count()` is a private method on the same class.
Its body builds the two row dicts and applies the validation rules listed in
`data-model.md`; it is kept under the 25-line ceiling.

## 7. Quality Gates

Run every gate before committing. All four must be clean:

```powershell
# Syntax (no output on success).
python -m py_compile MistHelper.py

# Lint -- must pass clean.
python -m ruff check MistHelper.py

# Format check -- run without --check to auto-fix.
python -m black --check MistHelper.py

# Functional smoke test using MIST_ORG_ID from .env.
python MistHelper.py --test
```

Then follow the standard deployment pipeline documented in
`.github/copilot-instructions.md` (commit, push, watch the container build,
pull the new image, restart).

## 8. Troubleshooting

| Symptom                                                           | Cause                                       | Fix                                                        |
|-------------------------------------------------------------------|---------------------------------------------|------------------------------------------------------------|
| `PermissionError: [Errno 13] ... /app/data/script.log`            | Container `data/` dir not writable          | `chmod -R 777 data/` before first container run            |
| `mistapi.exceptions.AuthorizationError`                           | Token missing/expired                       | Regenerate `MIST_API_TOKEN` in Mist UI; reload `.env`      |
| `[WARNING] Invalid org_id ... -- aborting menu 195`               | UUID malformed at the prompt                | Copy `MIST_ORG_ID` directly from the Mist URL bar          |
| 404 from the SDK                                                  | Org exists but no wireless sessions visible | Run during a known-active window or pick a different org   |
| Empty `results[]` array on every distinct                         | Org has no wireless activity in the window  | Widen `duration` (e.g. `7d`, `2w`)                         |
