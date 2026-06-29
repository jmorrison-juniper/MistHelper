# Phase 1 Quickstart: countOrgTunnelsStats Menu Item

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Data Model**: [data-model.md](./data-model.md)
**Date**: 2026-06-29

This quickstart describes how to run, test, and verify the new menu item on a
developer workstation.

## Prerequisites

- Python 3.13+ available in a venv at `.venv\`.
- `mistapi` 0.59+ installed (`pip install -r requirements.txt`).
- A valid Mist API token with read access to the target org.
- The repo's `.env` file populated (see below).

## Required `.env` variables

The new menu item uses the existing MistHelper dotenv bootstrap. Required keys:

```ini
MIST_HOST=api.mist.com          # or api.eu.mist.com / api.gc1.mist.com / ...
MIST_API_TOKEN=<your-api-token> # never logged
```

Optional convenience key (lets the user press Enter at the org_id prompt):

```ini
MIST_ORG_ID=<org-uuid>
```

No site, device, template, or NAC-rule IDs are required by this endpoint.

## Activate the venv (Windows PowerShell)

```powershell
.venv\Scripts\Activate.ps1
```

## Run the menu item (interactive)

```powershell
python MistHelper.py
# At the menu prompt, type: 91
```

You will see four prompts (defaults shown in brackets):

```
Org ID (UUID) [from MIST_ORG_ID]:
Tunnel type (wxtunnel / wan, blank for both):
Distinct attribute (default wxtunnel_id for wxtunnel / mac for wan):
Row limit (default 100):
```

Press Enter at each to accept defaults. Example end-to-end session:

```
Org ID (UUID) [abc12345-...]:
Tunnel type: wan
Distinct attribute: site_id
Row limit: 50
```

## Run the menu item (direct invocation)

```powershell
python MistHelper.py --menu 91
```

In `--menu` mode, prompts still appear unless `.env` already provides values.

## Expected output

A new file under `data/`:

```
data\org_<org_id_short>_tunnels_stats_count.csv
```

(`org_id_short` is the first 8 hex chars of the org UUID.)

If the SQLite backend is active, the same data lands in
`data\mist_data.db` -> table `org_tunnels_stats_count` (PK `(org_id, query_type,
query_distinct, distinct_value)`).

A successful run logs (ASCII-only, `%s` formatting):

```
INFO  Counting org tunnel stats for org %s distinct=%s type=%s limit=%d
DEBUG Tunnel count response: distinct=%s total=%d returned_rows=%d
INFO  Flattening tunnels count response into rows
DEBUG Flattened %d rows
INFO  Writing tunnels count to backend
DEBUG Wrote %d rows via DataExporter
```

On empty data:

```
WARNING countOrgTunnelsStats returned no rows for org=%s type=%s distinct=%s
```

On 404:

```
WARNING countOrgTunnelsStats: org %s not found or no permission
```

The process exits 0 in every safe path. Tracebacks indicate a bug.

## Method outline (matches plan.md and Constitution VI / VII)

The implementation will look approximately like (pseudo-skeleton, every executable
line will have an inline comment in the real implementation):

```python
def count_org_tunnels_stats(self):                           # menu entry, no args from dispatcher
    org_id = safe_input(                                     # prompt 1: org UUID
        "Org ID (UUID): ",
        context="count_org_tunnels_stats:org_id",
        default=os.getenv("MIST_ORG_ID", ""),
    )
    if not is_valid_uuid(org_id):                            # validate before SDK call
        logging.warning("Invalid org_id %s -- aborting", org_id)
        return
    tunnel_type = self._prompt_tunnel_type()                 # prompt 2 helper, enum-validated
    distinct = self._prompt_distinct(tunnel_type)            # prompt 3 helper, type-aware enum
    limit = self._prompt_limit()                             # prompt 4 helper, int 1..1000
    logging.info(
        "Counting org tunnel stats for org %s distinct=%s type=%s limit=%d",
        org_id, distinct, tunnel_type or "none", limit,
    )
    response = count.countOrgTunnelsStats(                   # SDK call
        self.apisession,
        org_id,
        distinct=distinct or None,
        type=tunnel_type or None,
        limit=limit,
    )
    rows = self._flatten_tunnels_count(org_id, response.data, tunnel_type)
    logging.debug("Flattened %d rows", len(rows))
    DataExporter.write_with_format_selection(                # multi-backend write
        rows,
        f"org_{org_id[:8]}_tunnels_stats_count",
        api_function_name="countOrgTunnelsStats",
    )
```

Line count: <=25 in the public method (helpers are private methods on the same
class, each also <=25 lines).

## Quality gates (run before every commit)

```powershell
python -m py_compile MistHelper.py    # syntax check; no output on success
python -m ruff check MistHelper.py    # lint; must be clean
python -m black --check MistHelper.py # format check; run without --check to auto-fix
```

All three MUST pass before committing.

## Automated test invocation

```powershell
python MistHelper.py --test
```

The default test runner skips operations 14, 18, 63-65, and 90-100. Menu 91 falls
inside the historical skip range, so one of the following applies:

1. The number is shifted to 92 at task-generation time (preferred), placing the op
   inside the default sweep range.
2. The number stays at 91 and the test runner gains a `--include 91` override or an
   explicit non-skip entry; the change to the runner is part of the same PR.

If menu 91 is kept and the skip block remains in force, the operator runs:

```powershell
python MistHelper.py --menu 91 --noninteractive --org-id $env:MIST_ORG_ID
```

(Non-interactive flag plumbing is already present for analogous skip-listed ops.)

## Verifying multi-backend output

After a successful run:

```powershell
# CSV
gci data\*tunnels_stats_count*.csv

# SQLite
python -c "import sqlite3; c = sqlite3.connect('data/mist_data.db'); print(c.execute('SELECT COUNT(*) FROM org_tunnels_stats_count').fetchone())"

# ArangoDB+Redis (only if those containers are running)
# - Inspect ArangoDB collection: org_tunnels_stats_count
# - Inspect Redis key: tunnels_count:<org_id>:<query_type>:<query_distinct>
```

## Tearing down test data

The new table is upsert-only and does not affect other tables. To reset between
runs:

```powershell
python -c "import sqlite3; sqlite3.connect('data/mist_data.db').execute('DROP TABLE IF EXISTS org_tunnels_stats_count'); print('dropped')"
```

CSV files can be deleted from `data\` directly; they are recreated on next run.

## Container verification

After commit and successful container build:

```powershell
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest
podman ps
# SSH in and select menu 91 to confirm prompts work over SSH.
ssh -p 2200 misthelper@localhost
```

The same menu number must be present in the container build as in local source.
