# Phase 1 Quickstart: Menu 195 -- getOrgEvpnTopology

## What this menu item does

Fetches one EVPN topology configuration from the Mist Cloud via
`GET /api/v1/orgs/{org_id}/evpn_topologies/{evpn_topology_id}` and writes two
files under `data/`:

- `data/OrgEvpnTopology.csv`           -- header (one row per fetched topology)
- `data/OrgEvpnTopologySwitches.csv`   -- detail (one row per switch in the topology)

Both files (and the corresponding SQLite tables `org_evpn_topology` and
`org_evpn_topology_switches`) upsert cleanly on repeated runs.

## Required `.env` variables

```dotenv
MIST_HOST=api.mist.com                          # Or your regional cloud (api.eu.mist.com, api.gc1.mist.com, ...)
MIST_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   # Your Mist API token; never commit
MIST_ORG_ID=a97c1b22-a4e9-411e-9bfd-d8695a0f9e61    # Default org UUID prompt fallback
MIST_EVPN_TOPOLOGY_ID=                          # Optional: default topology UUID for --test runs
```

`MIST_HOST` and `MIST_API_TOKEN` are loaded by `mistapi.APISession` at process
start. `MIST_ORG_ID` and `MIST_EVPN_TOPOLOGY_ID` are read by the menu method as
prompt defaults so `python MistHelper.py --test` can run non-interactively.

## Local run -- Windows 11 venv

```powershell
# 1. Activate the venv (standard MistHelper environment)
.venv\Scripts\Activate.ps1

# 2. Verify quality gates BEFORE running the menu item
python -m py_compile MistHelper.py    # Syntax check (no output = pass)
python -m ruff check MistHelper.py    # Lint
python -m black --check MistHelper.py # Format

# 3. Interactive run
python MistHelper.py --menu 195

# 4. Non-interactive test run (uses .env defaults)
python MistHelper.py --test
```

Expected interactive transcript:

```text
Org UUID [default from MIST_ORG_ID]: <Enter to accept default>
EVPN topology UUID [default from MIST_EVPN_TOPOLOGY_ID]: 9c8d0e2a-1f4b-4d5e-aabb-001122334455
[INFO ] Fetching EVPN topology 9c8d0e2a-1f4b-4d5e-aabb-001122334455 for org a97c1b22-a4e9-411e-9bfd-d8695a0f9e61
[DEBUG] EVPN topology 9c8d0e2a-1f4b-4d5e-aabb-001122334455: switches=12 pods=3
[INFO ] Flattening header + 12 switch rows
[DEBUG] Header columns=11 detail columns=10
[INFO ] Writing OrgEvpnTopology.csv via DataExporter
[INFO ] Writing OrgEvpnTopologySwitches.csv via DataExporter
[DEBUG] Wrote 1 header row, 12 detail rows
Menu 195 complete. Files under data/.
```

## Container run -- Podman

```powershell
# Assumes the container is already built and pulled per the standard pipeline
podman exec -it misthelper python /app/MistHelper.py --menu 195
```

The same `.env` file (mounted read-only at `/app/.env`) supplies the credentials
and prompt defaults. Output lands in `/app/data/` which is bind-mounted to
`./data/` on the host.

## SSH run -- port 2200

```bash
ssh -p 2200 misthelper@<host>
# Auto-launches MistHelper; select option 195 from the menu.
# safe_input() handles client disconnects without traceback.
```

## Implementation skeleton (~22 lines, fits the 5-Item Rule)

The method is added as a `@staticmethod` on `OrgConfigExporter` near
`MistHelper.py` line ~12047, beside `psks`, `webhooks`, `wlans`, and `mx_edges`.

```python
@staticmethod
def evpn_topology_detail():  # Menu 195: get one EVPN topology + its switches.
    """Fetch a single EVPN topology and write header + per-switch CSV/SQLite/Arango rows."""
    org_id = safe_input(                                                   # Prompt with .env fallback
        "Org UUID [default from MIST_ORG_ID]: ",
        context="org_evpn_topology:org_id",
    ) or os.environ.get("MIST_ORG_ID", "")                                 # Empty input -> .env default
    topo_id = safe_input(                                                  # Second required UUID
        "EVPN topology UUID [default from MIST_EVPN_TOPOLOGY_ID]: ",
        context="org_evpn_topology:evpn_topology_id",
    ) or os.environ.get("MIST_EVPN_TOPOLOGY_ID", "")                       # Empty input -> .env default
    if not _is_valid_uuid(org_id) or not _is_valid_uuid(topo_id):          # Fail fast on operator typos
        logging.warning("Invalid UUID supplied; aborting menu 195")        # ASCII-only warning, no token
        return                                                             # Early return per Principle III
    logging.info("Fetching EVPN topology %s for org %s", topo_id, org_id)  # Action log BEFORE API call
    resp = mistapi.api.v1.orgs.evpn_topologies.getOrgEvpnTopology(         # Single SDK call
        _get_session(), org_id, topo_id,
    )
    topology = resp.data or {}                                             # 404 surfaces here as {}
    switches = topology.get("switches", [])                                # Required by schema
    logging.debug(                                                         # Action log AFTER API call
        "EVPN topology %s: switches=%d pods=%d",
        topo_id, len(switches), len(topology.get("pod_names", {})),
    )
    header_row = _flatten_evpn_header(topology)                            # One row for the header table
    switch_rows = [_flatten_evpn_switch(topology, sw) for sw in switches]  # Per-switch detail rows
    DataExporter.write_with_format_selection(                              # Header export
        [header_row], "OrgEvpnTopology.csv",
        api_function_name="getOrgEvpnTopology",
    )
    DataExporter.write_with_format_selection(                              # Detail export
        switch_rows, "OrgEvpnTopologySwitches.csv",
        api_function_name="getOrgEvpnTopology_switches",
    )
```

`_flatten_evpn_header` and `_flatten_evpn_switch` are private static helpers on
the same class (each <=10 lines) that JSON-encode the nested blobs per the
data-model DDL.

## Quality gates (run before every commit)

```powershell
python -m py_compile MistHelper.py    # Must produce no output
python -m ruff check MistHelper.py    # Must report 0 violations
python -m black --check MistHelper.py # Must report "would be left unchanged"
python MistHelper.py --test           # Menu 195 must return 0 on a known org
```

After the gates pass, run the full deployment pipeline per
`.github/copilot-instructions.md` (commit -> push -> watch `container-build.yml`
-> pull image -> restart container -> verify with `podman ps`).
