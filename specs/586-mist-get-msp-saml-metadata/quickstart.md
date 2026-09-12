# Phase 1 Quickstart: getMspSamlMetadata

**Feature**: `586-mist-get-msp-saml-metadata`
**Date**: 2026-06-29
**Proposed menu number**: 58 (Misc cluster 56-59; re-verify at task generation)

This quickstart shows a developer how to run, test, and validate the new menu item
locally on Windows 11 + venv. Adapt path separators for Linux/Podman as needed.

## 1. Prerequisites

- Python 3.13+ in a venv at `.venv\`.
- `mistapi` 0.59+ installed (`pip install -r requirements.txt`).
- A valid `.env` at the repo root (never committed) with:

```dotenv
MIST_HOST=api.mist.com                # Or your tenant cloud (api.eu.mist.com, etc.)
MIST_API_TOKEN=<your-api-token>       # Loaded by mistapi.APISession; never logged
MIST_TEST_MSP_ID=<known-msp-uuid>     # Optional; used by --test for non-interactive run
MIST_TEST_SSO_ID=<known-sso-uuid>     # Optional; used by --test for non-interactive run
```

- Writable `data/` directory: `icacls data /grant Everyone:F /T` on Windows, or
  `chmod -R 777 data/` on Linux (the container runs as a non-root user).

## 2. Activate venv and verify environment

```powershell
.venv\Scripts\Activate.ps1                                # Windows venv activation
python --version                                          # Expect 3.13.x
python -c "import mistapi; print(mistapi.__version__)"    # Expect 0.59.x or newer
```

## 3. Interactive invocation

```powershell
python MistHelper.py                                      # Launch the menu
# At the prompt, enter:  58
# When prompted for "MSP ID": <paste msp UUID>
# When prompted for "SSO ID": <paste sso UUID>
```

Expected console flow (ASCII-only):

```text
INFO  Fetching MSP SAML metadata for msp <msp_id> sso <sso_id>
DEBUG MSP SAML metadata received: metadata_bytes=2048 acs_url=https://api.mist.com/...
INFO  Writing 1 row to msp_saml_metadata via <backend>
DEBUG Export complete: backend=<backend> rows_written=1
```

## 4. Direct (non-interactive) invocation

```powershell
python MistHelper.py --menu 58                            # Skips main menu; runs item 58
```

When `--menu 58` is combined with `MIST_TEST_MSP_ID` / `MIST_TEST_SSO_ID` set in `.env`,
no prompts appear and the menu item runs end-to-end. This is the path `--test` uses.

## 5. Expected outputs (under `data/`)

| Backend           | Artifact                                                     |
|-------------------|--------------------------------------------------------------|
| CSV               | `data/msp_saml_metadata.csv` (1 row appended/replaced)       |
| SQLite (default)  | `data/mist_data.db` table `msp_saml_metadata`, 1 row upserted |
| ArangoDB + Redis  | `msp_saml_metadata` collection in ArangoDB; key cached in Redis |

Re-running the menu item against the same `(msp_id, sso_id)` produces no duplicate row;
the existing row is replaced via `INSERT OR REPLACE` driven by the composite_pk strategy
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

## 6. Verify the SQLite row

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/mist_data.db'); print(list(c.execute('SELECT msp_id, sso_id, length(metadata) FROM msp_saml_metadata')))"
```

Expected: one tuple `(msp_uuid, sso_uuid, xml_byte_length)`.

## 7. Quality gates (run before commit)

All three must pass clean:

```powershell
python -m py_compile MistHelper.py                        # Syntax check; no output = pass
python -m ruff check MistHelper.py                        # Lint; must report 0 errors
python -m black --check MistHelper.py                     # Format check; run without --check to auto-fix
```

Then run the project's test sweep (menu 58 is in the default range; not in the heavy /
destructive skip list):

```powershell
python MistHelper.py --test                               # Non-interactive sweep using .env IDs
```

## 8. Implementation skeleton (for reference during task generation)

The actual method, with every executable line carrying the constitution-mandated inline
comment plus the before/after action logging pattern:

```python
def export_msp_saml_metadata(self, msp_id, sso_id):
    """Fetch and persist SAML SP metadata for one MSP SSO configuration."""
    if not _looks_like_uuid(msp_id):                                          # Guard malformed input early
        logging.warning("Invalid msp_id %s -- aborting", msp_id)              # Log validation failure for audit
        return                                                                # Bail out before hitting the API
    if not _looks_like_uuid(sso_id):                                          # Same guard for the SSO UUID
        logging.warning("Invalid sso_id %s -- aborting", sso_id)              # Mirror message for symmetry
        return                                                                # Bail out before hitting the API
    logging.info("Fetching MSP SAML metadata for msp %s sso %s", msp_id, sso_id)  # Action log before API call
    response = mistapi.api.v1.msps.ssos.metadata.getMspSamlMetadata(          # Sole permitted SDK invocation
        self.apisession, msp_id, sso_id                                       # Positional path params per SDK convention
    )
    payload = response.data or {}                                             # Tolerate empty body without KeyError
    logging.debug(                                                            # Action log after API call (size summary)
        "MSP SAML metadata received: metadata_bytes=%d acs_url=%s",
        len(payload.get("metadata") or ""), payload.get("acs_url"),
    )
    saml_metadata_row = {                                                     # Build the row in PK + body field order
        "msp_id": msp_id,                                                     # Inject path param 1 for composite PK
        "sso_id": sso_id,                                                     # Inject path param 2 for composite PK
        "acs_url": payload.get("acs_url"),                                    # Optional SAML ACS URL
        "entity_id": payload.get("entity_id"),                                # Optional SAML SP entityID
        "logout_url": payload.get("logout_url"),                              # Optional SAML logout URL
        "metadata": payload.get("metadata"),                                  # Raw XML, stored verbatim
        "scim_base_url": payload.get("scim_base_url"),                        # Optional OAuth/SCIM URL
    }
    logging.info("Writing 1 row to msp_saml_metadata")                        # Action log before export
    DataExporter.write_with_format_selection(                                 # Multi-backend output dispatch
        [saml_metadata_row], "msp_saml_metadata",                             # Filename / table base
        api_function_name="getMspSamlMetadata",                               # Drives PK strategy lookup
    )
    logging.debug("Export of msp_saml_metadata complete")                     # Action log after export
```

## 9. Rollback

If the new menu item misbehaves after deploy, revert by:

```powershell
git revert <commit-sha>                                   # Revert the version commit
git push origin main                                      # Trigger container-build.yml again
podman pull ghcr.io/jmorrison-juniper/misthelper:latest   # Pull the reverted image
podman stop misthelper ; podman rm misthelper             # Stop and remove the running container
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" ghcr.io/jmorrison-juniper/misthelper:latest
```

The `msp_saml_metadata` table remains populated and harmless after rollback; drop it
manually if a clean state is needed: `DROP TABLE IF EXISTS msp_saml_metadata;`.
