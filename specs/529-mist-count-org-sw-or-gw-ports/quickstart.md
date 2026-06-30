# Phase 1 Quickstart: countOrgSwOrGwPorts (Menu 89)

**Spec**: [spec.md](./spec.md)  **Plan**: [plan.md](./plan.md)

## Goal

Run the new MistHelper menu item that calls
`GET /api/v1/orgs/{org_id}/stats/ports/count` and produces a count-by-distinct-attribute
report of switch/gateway ports for an org, written to `data/` via the multi-backend
`DataExporter`.

## Required `.env` Variables

| Variable        | Required | Purpose                                                        |
|-----------------|----------|----------------------------------------------------------------|
| `MIST_HOST`     | Yes      | Mist cloud host, e.g. `api.mist.com`, `api.eu.mist.com`.       |
| `MIST_API_TOKEN`| Yes      | API token with at least read scope on the target org.          |
| `MIST_ORG_ID`   | No       | If set, presented as the default at the `org_id` prompt.       |
| `MIST_LOG_LEVEL`| No       | `DEBUG` or `INFO`. Default `INFO`. ASCII-only, no Unicode.     |

Never commit `.env`. The repo ships `deploy/.env.example` with these keys blank.

## Run It Locally (Windows 11 venv)

```powershell
# 1. Activate the venv (standard MistHelper dev environment).
.venv\Scripts\Activate.ps1                                  # PowerShell on Windows 11

# 2. Run the interactive menu.
python MistHelper.py                                        # Pick option 89 at the menu

# 3. Or run the operation directly without the menu loop.
python MistHelper.py --menu 89                              # Direct invocation
```

## Example Prompt Flow

```text
Enter org_id [default 1234abcd-1234-1234-1234-1234abcd5678]: <Enter>
Enter distinct field [default port_id]
  Common: port_id, mac, neighbor_system_name, speed, stp_state, up
: port_id
Enter site_id filter (blank for none): <Enter>
Filter by up=true / up=false (blank for none): <Enter>
Duration [default 1d]: 1d
```

After the prompts MistHelper logs (ASCII only, `%s` formatting):

```text
INFO  Counting org ports for org 1234abcd-... by distinct=port_id duration=1d
DEBUG Count response: total=42 results=42 start=1719600000 end=1719686400
INFO  Flattening 42 result rows for export
DEBUG Flatten complete: 42 rows ready
INFO  Writing org_stats_ports_count via DataExporter
DEBUG DataExporter wrote 42 rows to CSV + SQLite + Arango (where enabled)
```

## Expected `data/` Output

```text
data/
+-- org_stats_ports_count_1234abcd_port_id_20260629_175432.csv   # Timestamped CSV
+-- mist_data.db                                                  # SQLite (existing)
    \-- table: org_stats_ports_count                              # New table on first run
+-- per-host-logs/                                                # Unchanged
+-- script.log                                                    # Action log appended
```

When ArangoDB+Redis is the active backend, an `org_stats_ports_count` vertex collection
appears in the configured Arango database with the same rows, plus an `is_count_of`
edge from each row to the parent `orgs/<org_id>` vertex.

## Method Outline (Implementation Preview)

The new method lives on `OrgStatsExportUtils` in `MistHelper.py` and follows the
constitution's Inline Comments + Action Logging rules on every executable line. The
canonical skeleton (illustrative -- final code goes in MistHelper.py, NOT in this
file):

```python
def export_org_sw_or_gw_ports_count(                          # Menu 89 entry point
    self,                                                     # Bound to OrgStatsExportUtils
    org_id: str,                                              # Org UUID from .env or prompt
    distinct_field: str,                                      # Allow-listed group attribute
    extra_filters: dict | None = None,                        # Optional site_id/up/duration
) -> int:                                                     # Returns row count for tests
    """Count org switch/gateway ports by a distinct attribute."""
    logging.info(                                             # Pre-call action log
        "Counting org ports for org %s by distinct=%s",       # ASCII only
        org_id, distinct_field,
    )
    response = mistapi.api.v1.orgs.stats_ports.\
        countOrgSwOrGwPorts(                                  # Single SDK call
            self.apisession, org_id,                          # Path + auth
            distinct=distinct_field,                          # Required by API
            **(extra_filters or {}),                          # Optional filters
        )
    payload = response.data or {}                             # Defensive default
    results = payload.get("results", [])                      # Bucket array
    logging.debug(                                            # Post-call action log
        "Count response: total=%d results=%d start=%s end=%s",
        payload.get("total", 0), len(results),
        payload.get("start"), payload.get("end"),
    )
    rows = self._flatten_port_count_response(                 # Private helper, <=5 lines
        org_id, distinct_field, payload, extra_filters or {},
    )
    DataExporter.write_with_format_selection(                 # Multi-backend write
        rows,                                                 # Flattened row list
        filename=self._build_count_filename(                  # Helper builds CSV name
            org_id, distinct_field,
        ),
        api_function_name="countOrgSwOrGwPorts",              # Drives PK strategy lookup
    )
    return len(rows)                                          # Test hook
```

The accompanying `safe_input()` prompts live in the menu dispatcher, NOT inside this
method, so the method stays unit-testable and the prompt loop stays in one place.

## Quality Gates

Run BEFORE pushing. All three must succeed.

```powershell
python -m py_compile MistHelper.py                          # Syntax sanity check
python -m ruff check MistHelper.py                          # Lint clean required
python -m black --check MistHelper.py                       # Format clean required
python MistHelper.py --test                                 # Full menu sweep (skips destructive)
```

If `black --check` reports diffs, rerun without `--check` to auto-format:

```powershell
python -m black MistHelper.py                               # Auto-fix formatting
```

## Container Round-Trip

After local gates pass, ship through the standard pipeline documented in
`.github/copilot-instructions.md`:

```powershell
git add MistHelper.py README.md CHANGELOG.md                # Stage the touched files
git commit -m "version 26.06.29.18.00 - add menu 89 countOrgSwOrGwPorts"
git push origin main                                        # Triggers container-build.yml
gh run watch                                                # Wait for image publish
podman pull ghcr.io/jmorrison-juniper/misthelper:latest     # Refresh local image
podman stop misthelper ; podman rm misthelper               # Tear down old container
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" `
    -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest             # Start fresh
podman ps                                                   # Confirm running
```
