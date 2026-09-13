# Phase 1 Quickstart: getOrgJuniperDevicesCommand (Menu 58)

This document is the developer / NOC-engineer quickstart for the new menu
item. It assumes you have already cloned the repo and have the standard
MistHelper environment set up.

## Prerequisites

- Python 3.13 or newer.
- `mistapi==0.59+` installed (`pip install -r requirements.txt` or
  `uv pip install -r requirements.txt`).
- A populated `.env` file in the repo root.
- (Optional) Podman if you want to run the containerized version.

## Required `.env` Variables

| Variable | Required | Purpose |
|---|---|---|
| `MIST_HOST` | Yes | API host, e.g. `api.mist.com` or `api.eu.mist.com`. |
| `MIST_API_TOKEN` | Yes | Bearer token (`Authorization: Token <value>`). Never logged. |
| `MIST_ORG_ID` | Recommended | Defaults the `org_id` prompt so `--test` can run non-interactively. |
| `OUTPUT_BACKEND` | Optional | One of `csv` (default), `sqlite`, or `arango`. |
| `MIST_PAGE_LIMIT` | Optional | Default 1000 -- not used by this endpoint (non-paginated). |

Site-id is **never** taken from `.env`; it is per-invocation only.

## Expected Output

- CSV (default backend):
  `data/org_juniper_devices_outbound_ssh_cmd.csv`
  Columns: `org_id, site_id, cmd, cmd_length, retrieved_at`
  (the surrogate `misthelper_internal_id` is omitted from CSV to match the
  pattern used by other `auto_increment_with_unique` operations).
- SQLite (backend = `sqlite`):
  `data/mist_data.db` table `org_juniper_devices_outbound_ssh_cmd`
  (DDL in `data-model.md`).
- ArangoDB + Redis (backend = `arango`):
  Collection `org_juniper_devices_outbound_ssh_cmd`, with a graph edge
  `org -[has_outbound_ssh_cmd]-> command` and a Redis cache key
  `mist:org:<org_id>:outbound_ssh_cmd:<site_id_or_empty>`.

## How to Run

### Interactive (menu mode)

```powershell
.venv\Scripts\Activate.ps1                 # activate the local venv on Windows 11
python MistHelper.py                       # launch the interactive menu
# at the prompt:
58                                         # select the new menu item
# follow the prompts:
#   Enter org_id [MIST_ORG_ID default]: <press Enter to accept default, or paste a UUID>
#   Enter site_id (optional, press Enter to skip): <press Enter to skip>
```

### Direct invocation (automation)

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py --menu 58             # invokes the new method directly; uses MIST_ORG_ID from .env
```

### Containerized

```powershell
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman run --rm -it `
    -v "${PWD}/data:/app/data:rw" `
    -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest `
    python MistHelper.py --menu 58
```

## Example Run (CSV backend)

```text
> python MistHelper.py --menu 58
INFO  Fetching outbound SSH command for org 203d3d02-... (site=)
DEBUG Received cmd payload: length=412
INFO  Flattening response into one row
DEBUG Flatten produced 1 row
INFO  Writing org_juniper_devices_outbound_ssh_cmd to CSV backend
DEBUG DataExporter wrote 1 row to data/org_juniper_devices_outbound_ssh_cmd.csv
INFO  Menu 58 completed: rows=1
exit code: 0
```

The CSV file then contains a single row whose `cmd` column holds the
multi-line Mist-generated outbound-SSH + NETCONF bootstrap snippet.

## Method Outline (target: <=25 lines, <=3 params, <=5 blocks)

```python
def export_org_juniper_devices_outbound_ssh_cmd(self, org_id: str = "", site_id: str = "") -> int:  # menu 58 entry point
    org_id = org_id or safe_input(                                                 # block 1 of 5: prompt for org_id
        f"Enter org_id [{os.getenv('MIST_ORG_ID', '')} default]: ",
        context="org_juniper_devices_outbound_ssh_cmd:org_id",
    ) or os.getenv("MIST_ORG_ID", "")                                              # fall back to .env default if user pressed Enter
    if not UUID_REGEX.match(org_id):                                               # client-side UUID validation saves an API call
        logging.warning("Invalid org_id format; aborting menu 58")                 # warn-and-return rather than 400 from Mist
        return 0                                                                   # exit code 0 because user input is recoverable
    site_id = site_id or safe_input(                                               # block 2 of 5: prompt for optional site_id
        "Enter site_id (optional, press Enter to skip): ",
        context="org_juniper_devices_outbound_ssh_cmd:site_id",
    )
    if site_id and not UUID_REGEX.match(site_id):                                  # soft-validate site_id; degrade to no-site on failure
        logging.warning("Invalid site_id; proceeding without site context")        # do not abort -- site_id is optional in the API
        site_id = ""                                                               # normalize to empty so unique constraint is stable
    logging.info("Fetching outbound SSH command for org %s (site=%s)", org_id, site_id or "")  # block 3 of 5: action log before SDK call
    response = ocdevices_outbound_ssh_cmd.getOrgJuniperDevicesCommand(             # the sole permitted Mist Cloud client call
        self.apisession, org_id, site_id=site_id or None,
    )
    logging.debug("Received cmd payload: length=%d", len(response.data.get("cmd", "") or ""))  # length only -- never log the body
    juniper_command_row = {                                                        # block 4 of 5: flatten single object into one row
        "org_id": org_id, "site_id": site_id or "",
        "cmd": response.data.get("cmd", ""),
        "cmd_length": len(response.data.get("cmd", "") or ""),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
    return DataExporter.write_with_format_selection(                               # block 5 of 5: persist via the multi-backend writer
        [juniper_command_row],
        "org_juniper_devices_outbound_ssh_cmd",
        api_function_name="getOrgJuniperDevicesCommand",
    )
```

Line count = 22 executable lines (under the 25-line ceiling). Parameter
count = 3 (under the 5 ceiling). Logical block count = 5 (at the ceiling
but not over). Every executable line carries an inline comment per
Principle VI.

## Quality Gates (run before commit)

```powershell
.venv\Scripts\Activate.ps1                  # activate venv

python -m py_compile MistHelper.py          # syntax check; no output = pass
python -m ruff check MistHelper.py          # lint; must be clean
python -m black --check MistHelper.py       # format check; drop --check to auto-fix

python MistHelper.py --test                 # exercises menu 58 in non-interactive mode
                                            # (uses MIST_ORG_ID from .env; skips 14, 18, 63-65, 90-100)
```

All four gates must be green before `git commit`. The full deployment
pipeline (commit -> push -> GitHub Actions container build -> `podman pull`
-> restart container) is documented in
`.github/copilot-instructions.md` under "MANDATORY: Full Deployment
Pipeline" and applies unchanged here.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Invalid org_id format; aborting menu 58` | Typo in pasted UUID, or `MIST_ORG_ID` unset | Re-run, paste a valid UUID, or set `MIST_ORG_ID` in `.env`. |
| `404 Not Found` from Mist | Wrong org_id, or org has no OC devices feature enabled | Verify org via menu 1 / Mist UI; confirm OC adoption is licensed. |
| `429 Too Many Requests` | Rate limit hit | The adaptive delay in `delay_metrics.json` self-tunes; re-run after the back-off interval. |
| `PermissionError: ... /app/data/script.log` (container) | Mounted `data/` dir not writable by non-root container user | `chmod -R 777 data/` on the host then re-run. |
| Empty `cmd` field in output | Org genuinely has no OC bootstrap available | Confirm with Mist support; the menu reports zero-content but exits 0 cleanly. |
