# Phase 1 Quickstart: getOrgMxEdgeCluster Menu Item

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) |
**Research**: [research.md](./research.md) |
**Data Model**: [data-model.md](./data-model.md) |
**Contract**: [contracts/get_org_mx_edge_cluster.md](./contracts/get_org_mx_edge_cluster.md)

This document is the developer-facing quickstart for the new menu item
**Menu 96 -- GetOrgMxEdgeCluster**.

---

## 1. Prerequisites

- Python **3.13+** in a venv at the repo root: `.venv\Scripts\Activate.ps1`.
- `mistapi >= 0.59` installed via UV or pip (`uv pip install -r
  requirements.txt`).
- `.env` file at the repo root, NOT committed, containing at minimum:

```dotenv
MIST_HOST=api.mist.com                              # or your regional host
MIST_API_TOKEN=<paste your Mist API token here>     # never logged
MIST_ORG_ID=<your org UUID>                         # optional but recommended
MIST_TEST_MXCLUSTER_ID=<a known MxCluster UUID>     # only used by `--test`
```

- `data/` directory must exist and be writable. In containerized runs:
  `chmod -R 777 data/` once before first run.

---

## 2. How to run

### Interactive (humans)

```powershell
.venv\Scripts\Activate.ps1                          # Activate venv (Windows).
python MistHelper.py                                # Launch menu.
# Enter `96` at the menu prompt.
# Enter org_id (or press Enter to use MIST_ORG_ID from .env).
# Enter mxcluster_id (no default -- always prompted).
```

### Non-interactive (CI / automation)

```powershell
python MistHelper.py --menu 96                      # Direct invocation.
# Reads org_id from MIST_ORG_ID env var.
# Reads mxcluster_id from MIST_TEST_MXCLUSTER_ID env var when running --test.
```

### Test sweep

```powershell
python MistHelper.py --test                         # Runs full skip-aware test sweep.
# Menu 96 is included; skip list (14, 18, 63-65, 90-100 destructive) does
# not affect 96.
```

---

## 3. Expected output

| Backend | Location |
|---|---|
| CSV | `data/OrgMxEdgeCluster.csv` -- one row containing the cluster's flattened configuration. Nested objects are JSON-encoded into columns ending in `_json`. |
| SQLite | `data/mist_data.db`, table `org_mx_edge_cluster`. `INSERT OR REPLACE` on `id` so re-runs upsert cleanly. |
| ArangoDB+Redis | Document collection `org_mx_edge_cluster` (Arango) plus Redis cache key `mxcluster:<id>`. |

Console log (ASCII only, sample):

```
INFO  Fetching MxEdge cluster 53f10664-... for org a97c1b22-...
DEBUG MxCluster fetched: id=53f10664-... name=primary-cluster radsec_auth_servers=2 tunterm_hosts=3
INFO  Flattening MxCluster record for export.
DEBUG Flattened row has 21 columns.
INFO  Writing 1 record to OrgMxEdgeCluster via DataExporter.
DEBUG Wrote 1 record (backend=sqlite, table=org_mx_edge_cluster).
```

(No RADIUS shared secrets, `mist_password`, or `root_password` values
appear in the log lines.)

---

## 4. Method outline (the 25-line method body)

The skeleton below shows the expected shape; comments are MANDATORY on
every executable line per Constitution VI, and the action-log pattern is
MANDATORY per Constitution VII. Final implementation lives on
`OrgExportUtils` in `MistHelper.py`.

```python
@staticmethod
def org_mx_edge_cluster() -> None:                                          # New menu method for op 96.
    """Export one Org MxEdge cluster's full configuration to OrgMxEdgeCluster.csv."""
    org_id = safe_input(                                                    # Pull org_id with EOF safety.
        "Org ID (default from MIST_ORG_ID): ",
        context="org_mx_edge_cluster:org_id",
    ) or os.environ.get("MIST_ORG_ID", "")                                  # Fall back to env default.
    mxcluster_id = safe_input(                                              # Always prompt for cluster id.
        "MxEdge Cluster ID: ",
        context="org_mx_edge_cluster:mxcluster_id",
    )
    if not _is_uuid(org_id) or not _is_uuid(mxcluster_id):                  # Reject malformed IDs locally.
        logging.warning(                                                    # ASCII-only warning, no secrets.
            "Invalid UUID(s) supplied; aborting cluster fetch (org=%s, cluster=%s)",
            org_id, mxcluster_id,
        )
        return                                                              # Early exit -- no API call.
    logging.info(                                                           # Action log BEFORE the call.
        "Fetching MxEdge cluster %s for org %s", mxcluster_id, org_id,
    )
    response = mistapi.api.v1.orgs.mxclusters.getOrgMxEdgeCluster(          # The single GET.
        apisession, org_id=org_id, mxcluster_id=mxcluster_id,
    )
    record = response.data or {}                                            # Tolerate empty / 404 payloads.
    logging.debug(                                                          # Action log AFTER the call.
        "MxCluster fetched: id=%s name=%s",
        record.get("id"), record.get("name"),
    )
    flat_row = OrgExportUtils._flatten_mxcluster_row(record)                # Helper preserves 5-Item Rule.
    DataExporter.write_with_format_selection(                               # Multi-backend write.
        data=[flat_row],
        filename="OrgMxEdgeCluster",
        api_function_name="getOrgMxEdgeCluster",                            # Drives PK strategy lookup.
    )
```

The private helper `_flatten_mxcluster_row()` JSON-encodes the nested
config objects into `_json` columns (see `data-model.md` for the exact
column list). The helper itself stays <=25 lines because it is a single
dict construction.

---

## 5. Quality gates (run BEFORE every commit)

```powershell
python -m py_compile MistHelper.py                  # Syntax (no output = good).
python -m ruff check MistHelper.py                  # Lint (must pass clean).
python -m black --check MistHelper.py               # Format (drop --check to auto-fix).
python MistHelper.py --test                         # Smoke-test sweep (includes menu 96).
```

All four must pass. After they pass, follow the Full Deployment Pipeline
in `.github/copilot-instructions.md` to commit, push, wait for the
container build, pull the new image, and restart the container.

---

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `PermissionError: [Errno 13] ... data/script.log` | Container's `data/` not writable. | `chmod -R 777 data/` once. |
| API returns 404 | Wrong `org_id` or `mxcluster_id`. | Re-check IDs; menu logs a WARNING and exits 0 (no traceback). |
| API returns 401 | Bad `MIST_API_TOKEN` in `.env`. | Regenerate token in Mist Cloud; never commit it. |
| CSV row is empty | `response.data` was empty (no such cluster). | Confirm via `listOrgMxEdgeClusters` (existing menu) that the cluster id exists. |
| `safe_input()` raised | Not a bug -- EOF in SSH/container caused exit code 0. | Re-run interactively or provide both env vars before `--test`. |

---

## 7. References

- Endpoint contract: [contracts/get_org_mx_edge_cluster.md](./contracts/get_org_mx_edge_cluster.md)
- Mist API SDK source:
  `https://github.com/tmunzer/mistapi_python/tree/main/src/mistapi/api/v1/orgs/mxclusters.py`
- Enriched OpenAPI doc:
  `documentation/api/orgs/GET_orgs_org_id_mxclusters_mxcluster_id.md`
- Constitution: `.specify/memory/constitution.md`
- AI agent rules: `.github/copilot-instructions.md`
