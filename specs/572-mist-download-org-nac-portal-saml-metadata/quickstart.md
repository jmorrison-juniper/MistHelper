# Phase 1 Quickstart: downloadOrgNacPortalSamlMetadata (Menu 96)

**Branch**: `572-mist-download-org-nac-portal-saml-metadata`
**Date**: 2026-06-29
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data Model**: [data-model.md](./data-model.md)

This quickstart shows a developer how to exercise the new menu item end-to-end
on Windows 11 with the project venv, then in the production Podman container.

## 1. Prerequisites

- Python 3.13+ with the project venv active:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- `mistapi` 0.59+ installed (already in `requirements.txt`).
- `data/` directory exists at the repo root with write permission (the
  container needs `chmod -R 777 data/` on first run; locally just ensure
  the folder exists).
- A valid `.env` at the repo root containing the variables in section 2.
- The target org must own at least one NAC portal. Run menu item for
  `listOrgNacPortals` first (or pull the portal UUID from the Mist UI)
  to obtain a `nacportal_id` to test against.

## 2. Required `.env` Variables

| Variable          | Purpose                                                          | Required by this menu item |
|-------------------|------------------------------------------------------------------|----------------------------|
| `MIST_HOST`       | Mist Cloud region host (e.g. `api.mist.com`, `api.eu.mist.com`). | Yes (via mistapi)          |
| `MIST_API_TOKEN`  | Account-scoped API token with Org Read permission.               | Yes (via mistapi)          |
| `MIST_ORG_ID`     | Default org UUID; offered as the default at the `org_id` prompt. | Recommended                |

`MIST_API_TOKEN` is loaded by `mistapi.APISession` and is never logged or
echoed. The new menu item itself never reads the token directly.

## 3. Expected `data/` Output

After a successful invocation, the following files exist under `data/`:

- `data/orgs_<org_id>_nacportals_<nacportal_id>_saml_metadata.xml`
  -- the raw SAML metadata XML, ready for direct IdP import.
- `data/orgs_<org_id>_nacportals_<nacportal_id>_saml_metadata.csv`
  -- one-row CSV summary (when CSV backend is active).
- `data/mist_data.db` -- updated SQLite database; the
  `org_nac_portal_saml_metadata` table now contains (or has upserted)
  exactly one row for the requested `(org_id, nacportal_id)` tuple.
- ArangoDB + Redis backends, if active, receive the same single record
  via the standard `DataExporter` fan-out.

## 4. Example Invocation

### Interactive (default)

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
```

Then at the menu prompt:

```
Enter operation number: 96
Org ID [<MIST_ORG_ID default>]: <press Enter to accept default, or paste UUID>
NAC Portal ID: 5hdF5g-1234-4567-89ab-cdef01234567
```

Expected console / log output (ASCII only):

```
INFO  Downloading SAML metadata for org 203d3d02-... nacportal 5hdF5g-...
DEBUG SAML metadata received: 1842 bytes, entity_id=https://api.mist.com/api/v1/saml/5hdF5g/login
INFO  Writing raw XML to data/orgs_203d3d02_..._nacportals_5hdF5g_..._saml_metadata.xml
DEBUG Wrote 1842 bytes to data/orgs_203d3d02_..._nacportals_5hdF5g_..._saml_metadata.xml
INFO  Persisting 1 row via DataExporter (api_function_name=downloadOrgNacPortalSamlMetadata)
DEBUG DataExporter wrote 1 row to org_nac_portal_saml_metadata
```

### Direct (automation / smoke test)

```powershell
python MistHelper.py --menu 96
```

In `--menu` mode the method reads `MIST_ORG_ID` from `.env` for `org_id`
and uses the `MIST_NACPORTAL_ID` env var if present; otherwise it logs an
INFO message and exits 0 (per the `--test` skip semantics for items that
require runtime-only IDs).

## 5. Method Outline (for implementer reference)

The new method on `OrgNacPortalsExporter` (or new
`NacPortalSamlExporter`) follows the documented logging + commenting
discipline. Skeleton -- to be expanded with full inline comments on every
executable line during implementation (Constitution VI):

```python
def export_org_nac_portal_saml_metadata(self, org_id=None, nacportal_id=None):
    org_id = org_id or safe_input(                                # Prompt; default from .env
        f"Org ID [{os.getenv('MIST_ORG_ID', '')}]: ",
        context="download_org_nac_portal_saml_metadata:org_id",
    ) or os.getenv('MIST_ORG_ID', '')                             # Apply .env default on empty enter
    nacportal_id = nacportal_id or safe_input(                    # Prompt; no .env default
        "NAC Portal ID: ",
        context="download_org_nac_portal_saml_metadata:nacportal_id",
    )
    if not _is_uuid(org_id) or not _is_uuid(nacportal_id):        # Reject malformed UUIDs early
        logging.warning("Invalid UUID; aborting SAML metadata download")
        return
    logging.info("Downloading SAML metadata for org %s nacportal %s",
                 org_id, nacportal_id)                            # INFO before API call
    resp = mistapi.api.v1.orgs.nac_portals.downloadOrgNacPortalSamlMetadata(
        self.apisession, org_id, nacportal_id)                    # SDK call
    metadata_xml = resp.data if isinstance(resp.data, str) else resp.data.decode('utf-8')
    entity_id, valid_until = _parse_saml_attrs(metadata_xml)      # Parse two attrs only
    logging.debug("SAML metadata received: %d bytes, entity_id=%s",
                  len(metadata_xml.encode('utf-8')), entity_id)   # DEBUG after API call
    xml_path = os.path.join('data',                               # Build sidecar path
        f"orgs_{org_id}_nacportals_{nacportal_id}_saml_metadata.xml")
    with open(xml_path, 'w', encoding='utf-8') as fh:             # Write raw XML for IdP import
        fh.write(metadata_xml)
    row = {                                                       # Build summary row
        'org_id': org_id, 'nacportal_id': nacportal_id,
        'entity_id': entity_id, 'valid_until': valid_until,
        'metadata_bytes': len(metadata_xml.encode('utf-8')),
        'metadata_xml': metadata_xml, 'xml_file_path': xml_path,
        'retrieved_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
    base = f"orgs_{org_id}_nacportals_{nacportal_id}_saml_metadata"
    DataExporter.write_with_format_selection(                     # Fan out to CSV/SQLite/Arango
        [row], base, api_function_name="downloadOrgNacPortalSamlMetadata")
```

## 6. Quality Gates

Run these locally before commit; CI runs them again on push and blocks
merge on any red.

```powershell
# 1. Syntax (zero output = pass)
python -m py_compile MistHelper.py

# 2. Lint (must be clean)
python -m ruff check MistHelper.py

# 3. Format check (run without --check to auto-fix)
python -m black --check MistHelper.py

# 4. Functional sweep (skip list: 14, 18, 63-65, 90-100;
#    menu 96 IS included in the default sweep)
python MistHelper.py --test

# 5. Targeted smoke test against a known portal
python MistHelper.py --menu 96
```

All four (or five) must pass before the PR is eligible for the
`auto-merge` label, and the standard deployment pipeline (commit ->
push -> container build -> `podman pull` -> restart) follows the
sequence documented in `.github/copilot-instructions.md`.
