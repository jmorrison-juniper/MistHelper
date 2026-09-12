# Phase 1 Quickstart: countSiteNacClients (Menu 89)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Contract**: [contracts/count_site_nac_clients.md](./contracts/count_site_nac_clients.md)

This quickstart shows a junior NOC engineer how to run the new menu item locally on
Windows 11, what `.env` values are required, where the data lands, and which quality
gates must be green before the change can be committed.

---

## 1. Prerequisites

- Python 3.13+ on `PATH` (`python --version`).
- A Mist API token in `.env` at the repo root (never commit `.env`).
- The MistHelper venv created and activated:

  ```powershell
  cd C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging
  .venv\Scripts\Activate.ps1
  ```
- A known `site_id` (UUID) you have read access to. If you do not have one handy,
  run menu 1 (`listOrgSites`) first against your `MIST_ORG_ID` to discover sites.

---

## 2. Required .env variables

The new menu item reads these `.env` keys (no new variables introduced):

```ini
# Mist Cloud connection (consumed by mistapi.APISession)
MIST_HOST=api.mist.com           # or api.eu.mist.com / api.gc1.mist.com etc.
MIST_API_TOKEN=<your-token>      # generate from Mist Web UI -> My Account -> API Tokens

# Output backend selection (consumed by DataExporter.write_with_format_selection)
OUTPUT_FORMAT=csv                # one of: csv | sqlite | arango

# Optional org context (used by other menu items, not required for menu 89)
MIST_ORG_ID=<org-uuid>
```

The endpoint is site-scoped, so `MIST_ORG_ID` is not used by menu 89; the user
supplies `site_id` at the prompt.

---

## 3. Expected output

| Backend  | Location                                                                |
|----------|-------------------------------------------------------------------------|
| csv      | `data\site_nac_clients_count_<site_id>_<YYYYMMDD_HHMMSS>.csv`           |
| sqlite   | `data\mist_data.db` -> table `site_nac_clients_count`                   |
| arango   | Collection `site_nac_clients_count`, plus Redis cache + edges to sites  |

The CSV header (and SQLite columns) match the DDL in `data-model.md`:

```
site_id,distinct,distinct_value,end_epoch,count,start_epoch,limit_value,total,fetched_at
```

---

## 4. Example invocation

### Interactive (menu-driven)

```powershell
python MistHelper.py
# at the menu prompt: 89
# Site ID (UUID): 11111111-2222-3333-4444-555555555555
# Distinct field (default: type) [type|auth_type|last_vlan_id|last_ssid|...]: auth_type
# Duration window (default: 1d, e.g. 1h, 7d, 2w): 7d
```

Expected console (ASCII only):

```
INFO  Counting NAC clients at site 11111111-2222-3333-4444-555555555555 grouped by auth_type
DEBUG NAC count returned: distinct=auth_type total=1234 rows=5
INFO  Flattening 5 buckets into rows
DEBUG Flatten produced 5 rows
INFO  Writing 5 rows via DataExporter (format=csv)
DEBUG Wrote data\site_nac_clients_count_11111111_20260629_192617.csv
```

### Direct (automation)

```powershell
python MistHelper.py --menu 89
# Same prompts apply; for fully non-interactive runs, set MIST_SITE_ID in .env
# (handled by the per-menu prompt wrappers) or run --test which uses .env defaults.
```

### Test sweep

`python MistHelper.py --test` exercises every non-skipped menu (skip list: 14, 18,
63-65, 90-100). Menu 89 sits inside the default sweep range and is invoked
non-interactively using `.env` defaults.

---

## 5. Method outline (the actual code shape)

The new method on the NAC client export class follows this shape. Every executable
line carries an inline comment per Principle VI; every meaningful step has a
before/after log pair per Principle VII. The whole method stays under 25 lines per
the 5-Item Rule.

```python
def export_site_nac_clients_count(self, site_id, distinct="type", duration="1d"):
    site_id = self._validate_uuid(site_id)                                # Reject malformed UUIDs early to avoid wasted API calls
    distinct = self._validate_distinct_field(distinct)                    # Constrain to documented enum per research Task 5
    logging.info("Counting NAC clients at site %s grouped by %s",         # Pre-API audit log per Principle VII
                 site_id, distinct)
    response = nac_count.countSiteNacClients(                             # Single SDK call, no wrappers per Principle II
        self.session, site_id=site_id,
        distinct=distinct, duration=duration,
    )
    payload = response.data or {}                                         # Defensive default for empty 200 responses
    buckets = payload.get("results", [])                                  # results[] is the histogram array
    logging.debug("NAC count returned: distinct=%s total=%d rows=%d",     # Post-API summary log
                  payload.get("distinct"), payload.get("total", 0),
                  len(buckets))
    logging.info("Flattening %d buckets into rows", len(buckets))         # Pre-flatten audit log
    rows = self._flatten_nac_count(site_id, payload, buckets)             # Helper produces the wide tabular shape
    logging.debug("Flatten produced %d rows", len(rows))                  # Post-flatten count
    logging.info("Writing %d rows via DataExporter (format=%s)",          # Pre-write audit log
                 len(rows), self.exporter.format_name)
    self.exporter.write_with_format_selection(                            # Multi-backend dispatch per Principle II
        rows, "site_nac_clients_count",
        api_function_name="countSiteNacClients",
    )
```

The `_flatten_nac_count` helper merges the top-level summary keys (`distinct`,
`start`, `end`, `limit`, `total`) onto every bucket row, extracts the dynamic
`distinct_value` from the bucket's additional property, and adds the
`site_id` + `fetched_at` provenance columns.

---

## 6. Quality gates (must all be green before commit)

Run these in order from the repo root. The first three must produce zero warnings;
the fourth must exit 0.

```powershell
python -m py_compile MistHelper.py            # syntax check, no output on success
python -m ruff check MistHelper.py            # lint (auto-fix with: ruff check --fix)
python -m black --check MistHelper.py         # format check (auto-fix: drop --check)
python MistHelper.py --test                   # full menu sweep (skips 14, 18, 63-65, 90-100)
```

If any gate fails, fix the source -- do NOT add `# noqa` or `# fmt: skip` to suppress.
See `.github/instructions/coding-standards.instructions.md` for the fix-over-suppress
policy.

---

## 7. After the gates are green

Follow the standard deployment pipeline documented in `.github/copilot-instructions.md`:

```powershell
git add MistHelper.py README.md CHANGELOG.md specs\554-mist-count-site-nac-clients\
git commit -m "version YY.MM.DD.HH.MM - add menu 89 countSiteNacClients"
git push origin main
gh run watch                                  # wait for container build
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest
podman ps                                     # confirm running
```
