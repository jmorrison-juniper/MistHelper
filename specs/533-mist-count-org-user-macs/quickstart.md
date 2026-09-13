# Phase 1 Quickstart: countOrgUserMacs (Menu 59)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/orgs/{org_id}/usermacs/count`
**Proposed menu number**: 59

## How to run this menu item locally

### 1. Activate the venv (Windows)

```powershell
cd C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper
.venv\Scripts\Activate.ps1
```

### 2. Required `.env` variables

The `.env` file at the repo root must contain at minimum:

```ini
MIST_HOST=api.mist.com                # Mist API region host
MIST_API_TOKEN=<your_api_token>       # API token with read access to the target org
MIST_ORG_ID=<optional_default_org>    # Optional: prefills the org_id prompt for --test
```

The API token is loaded by `mistapi.APISession` and is never logged. Never commit
`.env` -- it is git-ignored.

### 3. Interactive launch

```powershell
python MistHelper.py
# At the menu prompt, type 59 and press Enter.
```

The menu method prompts (in order):

1. `Org ID: ` (UUID; defaults to `MIST_ORG_ID` if set)
2. `Distinct attribute [mac/name/labels/org_id] (default: mac): `
3. `Limit (default: 100): `
4. `Start window (epoch or -1d / -2h / now; blank to omit): `
5. `End window (epoch or now; blank to omit): `

All prompts route through `safe_input()`; EOF (closed SSH / container session) exits
with code 0 and no traceback.

### 4. Direct (non-interactive) launch

```powershell
python MistHelper.py --menu 59
```

When `MIST_ORG_ID` is set in `.env`, `--menu 59` runs end-to-end with the documented
defaults (`distinct=mac`, `limit=100`, no time window).

### 5. Expected `data/` output

After a successful run the following files appear (timestamp is UTC `YYYYMMDD_HHMMSS`):

```text
data/
  org_<org_id>_usermacs_count_envelope_<timestamp>.csv
  org_<org_id>_usermacs_count_mac_<timestamp>.csv          # filename includes distinct
  mist_data.db                                              # tables upserted:
                                                            #   org_usermacs_count_envelope
                                                            #   org_usermacs_count_results
```

When the `OUTPUT_BACKEND` env var selects ArangoDB+Redis, the same logical rows are
written to the configured collections via `DataExporter`. The user sees no
behavior change.

## Example invocation transcript

```text
$ python MistHelper.py --menu 59
[INFO] Starting menu 59 -- countOrgUserMacs
[INFO] Org ID: a1b2c3d4-1234-5678-9abc-def012345678
[INFO] Distinct attribute (default: mac): mac
[INFO] Limit (default: 100):
[INFO] Start window (blank to omit):
[INFO] End window (blank to omit):
[INFO] Counting user MACs for org a1b2c3d4-... by distinct=mac
[DEBUG] countOrgUserMacs: total=412 returned=100 start=None end=None
[INFO] Flattening 100 result rows
[DEBUG] Flatten produced 1 envelope row and 100 detail rows
[INFO] Writing org_usermacs_count via DataExporter (api_function_name=countOrgUserMacs)
[DEBUG] DataExporter: wrote 1 row to org_usermacs_count_envelope
[DEBUG] DataExporter: wrote 100 rows to org_usermacs_count_results
[INFO] Menu 59 complete; exit 0
```

## Method outline (~22 lines, fits the 5-Item Rule)

```python
def export_org_usermacs_count(self, org_id: str | None = None) -> int:
    org_id = org_id or safe_input("Org ID: ", context="org_usermacs_count:org_id")  # prompt or arg
    if not self._is_uuid(org_id):                                                   # validate UUID shape
        logging.warning("Invalid org_id %s; aborting menu 59", org_id)              # warn and exit clean
        return 1                                                                    # non-zero on bad input
    distinct = safe_input(                                                          # distinct attribute prompt
        "Distinct attribute [mac/name/labels/org_id] (default: mac): ",
        context="org_usermacs_count:distinct",
    ) or "mac"                                                                      # default to mac
    if distinct not in {"mac", "name", "labels", "org_id"}:                         # enum guard
        logging.warning("Invalid distinct=%s; aborting", distinct)                  # warn and exit
        return 1
    limit = int(safe_input("Limit (default: 100): ", context="...:limit") or 100)   # parse limit
    start = safe_input("Start window (blank to omit): ", context="...:start") or None  # optional
    end = safe_input("End window (blank to omit): ", context="...:end") or None       # optional
    logging.info("Counting user MACs for org %s by distinct=%s", org_id, distinct)   # action log BEFORE
    response = countOrgUserMacs(self.session, org_id, distinct, limit, start, end)   # SDK call
    logging.debug("countOrgUserMacs: total=%d returned=%d",                          # action log AFTER
                  response.data.get("total", 0), len(response.data.get("results", [])))
    rows = self._flatten_count_response(org_id, distinct, response.data)             # split envelope + detail
    DataExporter.write_with_format_selection(rows, "org_usermacs_count",             # multi-backend write
                                              api_function_name="countOrgUserMacs")
    return 0                                                                          # success
```

The actual implementation will be reviewed against the 5-Item Rule (<=25 lines,
<=5 params, <=5 logical blocks) by `ruff` rules and a manual check during PR review.

## Quality gates (run before commit, every time)

```powershell
python -m py_compile MistHelper.py                # syntax check; no output on success
python -m ruff check MistHelper.py                # lint; must be clean
python -m black --check MistHelper.py             # format check; rerun without --check to auto-fix
python MistHelper.py --test                        # smoke test (skips 14, 18, 63-65, 90-100)
```

All four must pass green before `git add` / `git commit`. The CI pipeline
(`.github/workflows/ci.yml`) re-runs the same gates plus mypy, Bandit, pip-audit, and
CodeQL; auto-merge is gated on every check passing.

## Smoke test (manual verification)

After implementation:

```powershell
python MistHelper.py --menu 59
# Enter a known good org_id, accept defaults.
# Verify:
#   1. data/org_<org_id>_usermacs_count_envelope_<ts>.csv exists and has 1 row.
#   2. data/org_<org_id>_usermacs_count_mac_<ts>.csv exists and has >=1 row.
#   3. sqlite3 data/mist_data.db "SELECT COUNT(*) FROM org_usermacs_count_results;"
#      returns a positive integer.
#   4. Re-run the same command; SQLite row count does NOT double (upsert works).
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `PermissionError: data/script.log` | Container data dir not writable | `chmod -R 777 data/` once on the host |
| `401 Unauthorized` from Mist | `MIST_API_TOKEN` missing or expired | Refresh token in `.env` |
| `404 Not Found` | Wrong `org_id` or token has no access | Verify with `--menu 1` (list orgs) first |
| `429 Too Many Requests` | Rate limit hit | Adaptive delay handles automatically; rerun |
| Empty `results[]` | Org has no user-MAC records in the window | Widen `start` / `end`; verify NAC is configured |

## Files touched (preview, for the implementation PR)

- `MistHelper.py` -- new method, new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, new menu
  registration at slot 59.
- `README.md` -- bump op count, add row in menu table for 59.
- `CHANGELOG.md` -- new `version YY.MM.DD.HH.MM` entry summarizing menu 59 addition.
