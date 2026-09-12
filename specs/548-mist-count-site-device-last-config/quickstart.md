# Quickstart: Run countSiteDeviceLastConfig (Menu 72)

This quickstart describes how a developer runs and verifies the new menu
item locally on a Windows 11 host using the project venv. The same commands
work inside the Podman container after `podman exec -it misthelper bash`.

## Prerequisites

- Python 3.13 or newer (constitution requirement)
- mistapi 0.59 or newer
- `.venv` activated:

```powershell
.venv\Scripts\Activate.ps1
```

## Required .env variables

`MistHelper.py` reads credentials from `.env` (git-ignored) via
`python-dotenv`. The minimum required keys for this menu item are:

| Key                       | Purpose                                  | Example |
|---------------------------|------------------------------------------|---------|
| `MIST_HOST`               | Mist Cloud regional host                 | `api.mist.com` |
| `MIST_API_TOKEN`          | API token with read scope                | `*** redacted ***` |
| `MIST_DEFAULT_ORG_ID`     | Default org for `--test` mode            | `203d3d02-...` |
| `MIST_DEFAULT_SITE_ID`    | Default site offered at the site_id prompt | `4ac1dde6-...` |

The token is never logged. `safe_input()` reads from stdin and exits cleanly
on EOF (SSH disconnect / container detach).

## Expected output

After a successful run with `distinct=hostname` against a site that has any
config history, the following artifacts appear under `data/`:

- `data/site_<site_id>_device_last_config_count_summary.csv` -- one row
- `data/site_<site_id>_device_last_config_count_results.csv` -- N rows,
  one per distinct hostname
- `data/mist_data.db` -- updated tables
  `site_device_last_config_count_summary` and
  `site_device_last_config_count_results`
- `data/script.log` -- new INFO/DEBUG entries from the operation

If the selected output backend is ArangoDB + Redis, the corresponding
graph + cache writes happen instead; the SQLite file is not touched.

## Interactive invocation

```powershell
python MistHelper.py
# At the menu prompt:
# 72
# At "Site ID [<default>]:" press Enter or type a site UUID
# At "Distinct field (hostname / version / device_type / blank for none):"
#   type: hostname
# At "Duration [1d]:" press Enter
# At "Limit [100]:" press Enter
```

## Direct (non-interactive) invocation

```powershell
python MistHelper.py --menu 72
```

In `--menu` mode, MistHelper sources every prompt from `.env` defaults or
the `MENU_72_*` environment overrides. The `--test` sweep includes menu 72
because it is outside the skip list (14, 18, 63-65, 90-100).

## Method outline (reference for implementer)

The new method (placed on the existing site-device export class in
`MistHelper.py`) is approximately:

```python
def count_site_device_last_config(                                       # New menu method
    self,                                                                # Standard bound-method receiver
    site_id: str,                                                        # Required path parameter
    distinct: str = "",                                                  # Optional distinct field
    duration: str = "1d",                                                # Optional time window
    limit: int = 100,                                                    # Optional result cap
) -> None:                                                               # Side-effecting export -- returns nothing
    logging.info(                                                        # Action log BEFORE the API call
        "Counting last_config history site=%s distinct=%s duration=%s",
        site_id, distinct or "(none)", duration,
    )
    response = mistapi.api.v1.sites.devices.last_config.countSiteDeviceLastConfig(  # SDK call
        self.apisession,                                                 # Auth context
        site_id=site_id,                                                 # Required path param
        distinct=distinct or None,                                       # Empty string -> None for the SDK
        duration=duration,                                               # Resolved by Mist into start/end
        limit=max(1, min(int(limit), 1000)),                             # Clamp limit for safety
    )
    body = response.data or {}                                           # Defensive default for empty body
    logging.debug(                                                       # Action log AFTER the API call
        "Count response total=%s groups=%s",
        body.get("total"), len(body.get("results", [])),
    )
    summary_row, result_rows = self._flatten_last_config_count(          # Private helper -- two-table flatten
        site_id, body,
    )
    DataExporter.write_with_format_selection(                            # Multi-backend persistence
        data={                                                           # Two logical tables in one call
            "site_device_last_config_count_summary": [summary_row],
            "site_device_last_config_count_results": result_rows,
        },
        filename=f"site_{site_id}_device_last_config_count",             # Backend uses suffix per table
        api_function_name="countSiteDeviceLastConfig",                   # Drives PK strategy lookup
    )
```

The flatten helper `_flatten_last_config_count()` is a private method on
the same class, also commented inline, and stays under 25 lines.

## Quality gates (run before every commit)

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py
python MistHelper.py --test
```

All four must pass green. The `--test` step exercises menu 72 against the
`.env`-configured org/site without manual input. On a clean run the exit
code is 0, the two CSV files exist, and the script log shows the INFO and
DEBUG lines from the new method.
