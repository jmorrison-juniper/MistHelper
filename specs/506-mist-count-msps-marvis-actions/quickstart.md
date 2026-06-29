# Quickstart: countMspsMarvisActions (Menu 96)

**Feature**: 506-mist-count-msps-marvis-actions
**Date**: 2026-06-28
**Endpoint**: `GET /api/v1/msps/{msp_id}/suggestion/count`

## Prerequisites

- Python 3.13+ with the project venv activated:
  `.\.venv\Scripts\Activate.ps1`
- `mistapi` 0.59+ installed (already in `requirements.txt` / `uv.lock`).
- Repository worktree at:
  `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging`
- `data\` directory exists and is writable
  (`chmod -R 777 data\` once on first container run; on Windows venv the
  default ACLs are sufficient).
- Active Marvis subscription for the MSP-managed organizations
  (otherwise the API returns an empty / 403 payload).

## Required `.env` Variables

| Variable          | Required | Purpose                                                   |
|-------------------|----------|-----------------------------------------------------------|
| `MIST_HOST`       | yes      | Mist cloud host, e.g. `api.mist.com`                      |
| `MIST_API_TOKEN`  | yes      | API token with MSP read scope                             |
| `MIST_MSP_ID`     | optional | Default MSP UUID; pressing Enter at the prompt uses this  |

The token is loaded by `mistapi.APISession` and is never logged or echoed.

## Local Run

### Interactive (menu-driven)

```powershell
cd 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging'
.\.venv\Scripts\Activate.ps1
python MistHelper.py
# select menu number 96
# Enter msp_id: <press Enter to use MIST_MSP_ID, or paste a UUID>
# Enter distinct attribute (status|category|priority|type, blank for default): status
# Enter limit (1-1000, blank for 100): 100
```

### Direct (automation)

```powershell
python MistHelper.py --menu 96
```

In direct mode, prompts fall back to the `MIST_MSP_ID` value and SDK defaults
(`distinct` unset, `limit=100`). On a terminating EOF (common in CI), the
`safe_input()` wrapper exits cleanly with code 0.

## Expected `data\` Output

After a successful run two artifacts appear under `data\`:

- `data\msp_marvis_actions_count_summary.csv`
  -- one row describing the request envelope.
- `data\msp_marvis_actions_count_results.csv`
  -- one row per distinct bucket returned by the API.

If SQLite is the active backend, identical tables are created/updated inside
`data\mist_data.db`. If the polyglot ArangoDB+Redis backend is active, the
two collections are populated and a graph edge is added linking each result
row to its summary row.

## Example Invocation and Output

```text
> python MistHelper.py --menu 96
[INFO] Prompting for msp_id (context=msp_marvis_actions_count:msp_id)
[INFO] Prompting for distinct (context=msp_marvis_actions_count:distinct)
[INFO] Prompting for limit (context=msp_marvis_actions_count:limit)
[INFO] Fetching Marvis actions count for msp 00000000-aaaa-bbbb-cccc-1234567890ab distinct=status limit=100
[DEBUG] Marvis actions count: total=3 rows=3
[INFO] Flattening 3 result buckets into rows
[DEBUG] Flatten complete: summary_rows=1 result_rows=3
[INFO] Writing msp_marvis_actions_count_summary via DataExporter
[INFO] Writing msp_marvis_actions_count_results via DataExporter
```

CSV preview (`data\msp_marvis_actions_count_summary.csv`):

```csv
msp_id,distinct_attribute,limit,total,snapshot_timestamp
00000000-aaaa-bbbb-cccc-1234567890ab,status,100,3,2026-06-28T22:51:00Z
```

CSV preview (`data\msp_marvis_actions_count_results.csv`):

```csv
msp_id,distinct_attribute,distinct_value,count,snapshot_timestamp
00000000-aaaa-bbbb-cccc-1234567890ab,status,002e176a-0000-000-1111-002e208b20e1,24,2026-06-28T22:51:00Z
00000000-aaaa-bbbb-cccc-1234567890ab,status,2d3f176a-0000-000-2222-002e208f176a,12,2026-06-28T22:51:00Z
00000000-aaaa-bbbb-cccc-1234567890ab,status,08b2176a-0000-000-3333-002e208b2d3f,15,2026-06-28T22:51:00Z
```

## Implementation Sketch (for `/speckit.tasks`)

```python
class MspMarvisExportUtils:                                                # New class for MSP/Marvis exports
    def export_msp_marvis_actions_count(                                   # Menu 96 entry point
        self, msp_id=None, distinct=None, limit=None,                      # All inputs optional, prompted on demand
    ):
        logging.info("Prompting for msp_id")                               # Action log before prompt cluster
        msp_id = msp_id or safe_input(                                     # Prompt only if not pre-supplied
            "MSP UUID: ", context="msp_marvis_actions_count:msp_id",
        ) or os.getenv("MIST_MSP_ID", "")                                  # Fall back to .env
        if not _is_mist_uuid(msp_id):                                      # Pre-validate before API call
            logging.warning("Invalid msp_id; aborting")                    # NOC-friendly log line
            return 0                                                       # Early return on bad input
        logging.info(                                                      # Pre-call action log
            "Fetching Marvis actions count for msp %s distinct=%s limit=%s",
            msp_id, distinct, limit,
        )
        response = mistapi.api.v1.msps.suggestion.count.countMspsMarvisActions(  # SDK call
            self.session, msp_id, distinct=distinct, limit=limit or 100,
        )
        logging.debug(                                                     # Post-call action log
            "Marvis actions count: total=%d rows=%d",
            response.data.get("total", 0), len(response.data.get("results", [])),
        )
        summary_row, result_rows = self._flatten(msp_id, response.data)    # Local flatten helper
        DataExporter.write_with_format_selection(                          # Multi-backend write: summary
            [summary_row], "msp_marvis_actions_count_summary",
            api_function_name="countMspsMarvisActions_summary",
        )
        DataExporter.write_with_format_selection(                          # Multi-backend write: results
            result_rows, "msp_marvis_actions_count_results",
            api_function_name="countMspsMarvisActions_results",
        )
        return 0                                                           # Exit code for --test harness
```

Every executable line above carries an inline comment per Constitution VI;
every `INFO`/`DEBUG` pair satisfies Constitution VII.

## Quality Gates (run before every commit)

```powershell
python -m py_compile MistHelper.py                  # Syntax check (no output = valid)
python -m ruff check MistHelper.py                  # Lint
python -m black --check MistHelper.py               # Format check (omit --check to auto-fix)
python MistHelper.py --test                         # Test harness (menu 96 is in the default sweep)
```

All four must exit 0 before pushing.

## Troubleshooting

- **403 Permission Denied** -- the API token lacks MSP read scope or the
  managed orgs do not have a Marvis subscription. Verify in the Mist UI.
- **404 Not Found** -- `msp_id` is wrong. Re-check via
  `mistapi.api.v1.self.self.getSelf()`.
- **429 Too Many Requests** -- the adaptive delay system in
  `delay_metrics.json` will back off automatically; rerun the menu item.
- **Empty `results[]`** -- no pending Marvis suggestions across the MSP.
  Confirm by running the related per-org endpoints
  (`listOrgSuggestions` / `getOrgMarvisActions`).
- **PermissionError on `data\...`** (container only) -- run
  `chmod -R 777 data\` on the host once before first container start.
