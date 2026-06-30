# Phase 1 Quickstart: getOrgJseInfo (Menu 58)

**Feature**: 609-mist-get-org-jse-info
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document gives a developer or junior NOC engineer the shortest path from a clean
checkout to a successful run of the new menu item, plus the exact quality gates that
must pass before commit.

---

## 1. Prerequisites

- Windows 11 with the project venv at `.venv` (Python 3.13+).
- A populated `.env` at the repo root with at minimum:
  - `MIST_HOST` -- e.g. `api.mist.com` (or your regional endpoint)
  - `MIST_API_TOKEN` -- a valid Mist API token with read access to the target org
  - `MIST_ORG_ID` -- (optional) default org UUID; offered as the prompt default
- A target organization that has the JSE integration enabled (see Gotcha #1).

The `data/` directory must exist and be writable. If you have not run MistHelper
before in this checkout:

```powershell
New-Item -ItemType Directory -Force -Path data | Out-Null
```

When running inside the container, also ensure the bind-mounted `data/` is
world-writable as documented in `.github/copilot-instructions.md` (the container
runs as a non-root `misthelper` user):

```powershell
chmod -R 777 data/   # WSL / Git Bash; or set ACLs in PowerShell
```

---

## 2. Required `.env` variables

| Variable         | Required | Source                  | Used by                                |
|------------------|----------|-------------------------|----------------------------------------|
| `MIST_HOST`      | Yes      | Mist cloud region URL   | `mistapi.APISession` constructor       |
| `MIST_API_TOKEN` | Yes      | Mist admin -> API Tokens | `mistapi.APISession` constructor       |
| `MIST_ORG_ID`    | Optional | Mist UI -> Organization  | Default value offered at the org prompt |

Tokens and IDs are never logged. The SDK reads them from the environment exactly
once at process start.

---

## 3. Expected `data/` output

| Backend            | Artifact                                         |
|--------------------|--------------------------------------------------|
| CSV (default)      | `data/org_jse_info_<org_id>.csv`                 |
| JSON               | `data/org_jse_info_<org_id>.json`                |
| SQLite             | Row in `data/mist_data.db` -> table `org_jse_info` |
| ArangoDB + Redis   | Document in `org_jse_info` collection + Redis cache |

The row contains six columns: `org_id`, `cloud_name`, `org_names` (sorted,
comma-joined), `org_names_count`, `username`, `fetched_at`. See
[data-model.md](./data-model.md) for the full schema.

---

## 4. Run the menu item

### Interactive (menu-driven)

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# At the main menu, enter: 58
# When prompted "Enter org_id [<default from MIST_ORG_ID>]:" press Enter to accept
# the .env default, or paste a different UUID.
```

Expected console output (ASCII only):

```
INFO     Fetching JSE info for org <org_id>
DEBUG    JSE info: cloud=devcentral.juniperclouds.net username=john@abc.com org_count=3
INFO     Writing org_jse_info_<org_id>.csv (1 row)
DEBUG    Wrote 1 row to org_jse_info via DataExporter
```

If the integration is not configured (404), the run logs a `WARNING` and exits 0:

```
WARNING  getOrgJseInfo returned no payload for org <org_id> (HTTP 404)
```

### Non-interactive (direct invocation, for `--test` and CI)

```powershell
python MistHelper.py --menu 58
```

`--menu 58` consumes the `MIST_ORG_ID` from `.env` for the org prompt; if that
variable is unset the run exits 0 with a `WARNING` rather than hanging on stdin.

---

## 5. Example invocation walk-through

```
> python MistHelper.py
================ MistHelper Main Menu ================
...
 58. Export Org JSE Info (getOrgJseInfo)
...
Select an operation (q to quit): 58

Enter org_id [203d3d02-xxxx-xxxx-xxxx-xxxxxxxxxxxx]: <Enter>

INFO     Fetching JSE info for org 203d3d02-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DEBUG    JSE info: cloud=devcentral.juniperclouds.net username=ops@acme.com org_count=2
INFO     Writing org_jse_info_203d3d02-xxxx-xxxx-xxxx-xxxxxxxxxxxx.csv (1 row)
DEBUG    Wrote 1 row to org_jse_info via DataExporter

Operation 58 complete. Output: data/org_jse_info_203d3d02-xxxx-xxxx-xxxx-xxxxxxxxxxxx.csv
```

Re-run the same selection: the SQLite row UPSERTs in place with no duplicate. The
CSV file is overwritten with the latest snapshot.

---

## 6. Method outline (for implementers)

The new method lives on the existing `OrgConfigExportUtils` class. Approximate
shape (final form is produced in `/speckit.tasks` / `/speckit.implement`):

```python
def export_org_jse_info(self, org_id: str | None = None) -> None:
    org_id = org_id or os.environ.get("MIST_ORG_ID")            # honor .env default
    org_id = safe_input(                                        # SSH/container-safe prompt
        f"Enter org_id [{org_id or ''}]: ",
        context="org_jse_info:org_id",
    ).strip() or org_id                                          # fall back to default on empty
    if not UUID_RE.match(org_id or ""):                          # validate before SDK call
        logging.warning("Invalid org_id for getOrgJseInfo: %s", org_id)
        return                                                   # bail cleanly on bad input
    logging.info("Fetching JSE info for org %s", org_id)         # action log BEFORE call
    response = mistapi.api.v1.orgs.integration_jse.getOrgJseInfo(
        self.apisession, org_id,                                 # sole SDK call
    )
    payload = response.data or {}                                # tolerate empty body / 404
    if not payload:                                              # no integration configured
        logging.warning(
            "getOrgJseInfo returned no payload for org %s", org_id,
        )
        return                                                   # exit 0 -- nothing to write
    org_names = sorted(payload.get("org_names") or [])           # deterministic ordering
    row = {                                                      # build the flat persistence row
        "org_id": org_id,                                        # injected natural PK
        "cloud_name": payload.get("cloud_name"),                 # upstream field
        "org_names": ",".join(org_names),                        # CSV-friendly join
        "org_names_count": len(org_names),                       # derived cardinality
        "username": payload.get("username"),                     # upstream field
        "fetched_at": datetime.now(timezone.utc).isoformat(),    # snapshot timestamp
    }
    logging.debug(                                               # action log AFTER call
        "JSE info: cloud=%s username=%s org_count=%d",
        row["cloud_name"], row["username"], row["org_names_count"],
    )
    DataExporter.write_with_format_selection(                    # multi-backend write
        data=[row],
        filename=f"org_jse_info_{org_id}.csv",
        api_function_name="getOrgJseInfo",
    )
```

Line count: ~22 executable lines (within the 25-line Five-Item Rule budget).
Parameter count: 2 (`self`, `org_id`). Logical block count: 5 (resolve -> validate
-> call -> flatten -> write).

---

## 7. Quality gates (run BEFORE commit)

All three must pass clean. No warnings, no errors.

```powershell
python -m py_compile MistHelper.py                       # syntax check (silent on success)
python -m ruff check MistHelper.py                       # lint
python -m black --check MistHelper.py                    # format (drop --check to auto-fix)
```

Then run the test harness against a known org:

```powershell
python MistHelper.py --test                              # exercises menu 58 in non-interactive mode
```

`--test` skips the documented heavy / destructive list (14, 18, 63-65, 90-100); menu
58 is inside the standard sweep range and will execute.

---

## 8. Common pitfalls

1. **404 on first call**: The Mist org does not have JSE integration enabled. This
   is the documented "Gotcha" in the enriched per-endpoint reference. MistHelper
   logs a `WARNING` and exits 0 -- this is expected behavior, not a defect.
2. **`PermissionError` on `data/`**: The container runs as non-root; bind-mounted
   `data/` needs `chmod -R 777 data/` once.
3. **EOF on prompt**: Running over SSH (port 2200) without a TTY -- `safe_input()`
   detects EOF and exits 0 cleanly. Use `--menu 58` for non-interactive contexts.
4. **`MIST_ORG_ID` unset**: Interactive runs prompt with an empty default; `--menu
   58` exits 0 with a `WARNING` instead of hanging.

---

## 9. Post-implementation deployment

Follow the standard MistHelper Full Deployment Pipeline (see
`.github/copilot-instructions.md` -> "MANDATORY: Full Deployment Pipeline"):
commit with `version YY.MM.DD.HH.MM - add menu 58 getOrgJseInfo`, push, wait for the
container-build workflow, `podman pull`, restart the container, verify with `podman
ps`. The README operation count and menu table row are updated in the same commit.
