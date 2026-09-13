# Phase 1 Quickstart: getOrgAntivirusProfile Menu Item

**Branch**: `594-mist-get-org-antivirus-profile` | **Date**: 2026-06-29
**Plan**: [plan.md](./plan.md) | **Contract**:
[contracts/get_org_antivirus_profile.md](./contracts/get_org_antivirus_profile.md)

A practical guide to running the new menu item locally during
implementation and CI smoke-test.

---

## Required `.env` Variables

The new menu item reuses the standard MistHelper environment. No new
variables are introduced; the optional defaulting variable is already
recognized by sibling menu items.

| Variable                | Required | Purpose                                                                 |
|-------------------------|----------|-------------------------------------------------------------------------|
| `MIST_HOST`             | Yes      | Mist Cloud regional host (e.g. `api.mist.com`, `api.eu.mist.com`).       |
| `MIST_API_TOKEN`        | Yes      | API token for the operator account. Never logged.                       |
| `MIST_DEFAULT_ORG_ID`   | No       | UUID. Pressing Enter at the `org_id` prompt uses this default.          |
| `MIST_PAGE_LIMIT`       | No       | Ignored here -- endpoint is not paginated.                              |
| `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` | No | Honored by `--fast`. Has no effect on this single-call menu item. |

`.env` lives at the repository root, is git-ignored, and is mounted into
the Podman container read-only at `/app/.env`.

---

## Expected Output

| Backend        | Location                                                |
|----------------|---------------------------------------------------------|
| CSV (default)  | `data/org_avprofile.csv` -- one row appended per run.   |
| SQLite         | `data/mist_data.db`, table `org_avprofile` -- one row upserted per run keyed on `id`. |
| ArangoDB+Redis | Document collection `org_avprofile`, graph edges to `org` and `site`, Redis cache key `mh:org_avprofile:<id>` (per existing exporter conventions). |
| Log file       | `data/script.log` -- INFO/DEBUG breadcrumbs (token redacted). |

If the upstream API returns `null` / 404, the file is **not** rewritten;
the run logs a `WARNING` and exits 0.

---

## Local Run: Interactive Invocation

Assumes Windows 11 + venv (the project's standard local environment).

```powershell
.venv\Scripts\Activate.ps1                 # Standard venv activation
python MistHelper.py                       # Launch the menu loop
# At prompt: enter 96 (the proposed menu number for this op)
# Prompt 1: "Org ID [default <MIST_DEFAULT_ORG_ID>]: "
#   -> press Enter to accept default, or paste a UUID
# Prompt 2: "Antivirus profile ID: "
#   -> paste the avprofile UUID (run menu N (listOrgAvprofiles) first if unknown)
# Output: confirmation lines, then a summary of which backends were written.
```

Expected console output (abridged, ASCII only):

```
INFO  Fetching antivirus profile <avprofile_id> for org <org_id>
DEBUG Got avprofile id=<id> name=<name> protocols=3
INFO  Flattening avprofile record for export
DEBUG Flattened 1 row from 1 source object
INFO  Writing avprofile to configured backends
INFO  DataExporter: wrote 1 row to data/org_avprofile.csv
INFO  DataExporter: upserted 1 row in SQLite org_avprofile
Done. Returning to menu.
```

---

## Local Run: Direct (Non-Interactive) Invocation

```powershell
python MistHelper.py --menu 96
# Prompts proceed as above; suitable for scripted smoke tests.
```

`--test` mode runs the full menu sweep but **skips** menu 96 by default
because it requires a known `avprofile_id` per environment. To include it,
either:

1. Add `getOrgAntivirusProfile` to the test harness's per-env override
   map with a known UUID, or
2. Invoke directly via `python MistHelper.py --menu 96 --org <uuid>
   --avprofile <uuid>` (when the CLI flag wiring is added; otherwise rely
   on the env-default flow).

---

## Implementation Outline (for `/speckit.tasks` planning)

The new method lives on `SecurityProfileExportUtils`. Approximate shape
(~22 executable lines, each commented per Principle VI):

```python
def export_org_antivirus_profile(self, org_id=None, avprofile_id=None):
    org_id = org_id or safe_input(                     # Prompt only if not pre-supplied
        f"Org ID [{self.default_org_id}]: ",
        context="org_antivirus_profile:org_id",
    ) or self.default_org_id                            # Fall back to .env default
    avprofile_id = avprofile_id or safe_input(          # No .env default for per-profile UUID
        "Antivirus profile ID: ",
        context="org_antivirus_profile:avprofile_id",
    )
    if not _is_valid_uuid(org_id):                      # Early-validate to save an API call
        logging.warning("Invalid org_id %s -- aborting", org_id)
        return
    if not _is_valid_uuid(avprofile_id):                # Same protection for avprofile_id
        logging.warning("Invalid avprofile_id %s -- aborting", avprofile_id)
        return
    logging.info(                                       # Action log BEFORE the SDK call
        "Fetching antivirus profile %s for org %s",
        avprofile_id, org_id,
    )
    response = mistapi.api.v1.orgs.avprofiles.getOrgAntivirusProfile(
        self.mist_session, org_id, avprofile_id,        # Single GET, non-paginated
    )
    profile_record = response.data or {}                # Handle null/404 path cleanly
    logging.debug(                                      # Action log AFTER the SDK call
        "Got avprofile id=%s name=%s protocols=%d",
        profile_record.get("id"),
        profile_record.get("name"),
        len(profile_record.get("protocols") or []),
    )
    if not profile_record:                              # 404 / empty payload guard
        logging.warning("No avprofile returned for %s", avprofile_id)
        return
    flattened_row = _flatten_avprofile(profile_record)  # Per data-model.md column order
    DataExporter.write_with_format_selection(            # Multi-backend write (Principle IV)
        data=[flattened_row],
        filename="org_avprofile",
        api_function_name="getOrgAntivirusProfile",
    )
```

`_flatten_avprofile` is a private helper on the same class -- needed only
if the inline flatten step exceeds 5 lines (Principle I).

---

## Quality Gates (run BEFORE every commit)

Per `.github/copilot-instructions.md` and the constitution Principle IV:

```powershell
python -m py_compile MistHelper.py            # Syntax check; silent on success
python -m ruff check MistHelper.py            # Lint; must report 0 findings
python -m black --check MistHelper.py         # Format; must exit 0
python MistHelper.py --test                   # Full menu sweep (excluding skip list)
```

All four must be green before `git commit`. Then the full deployment
pipeline applies:

```powershell
git add MistHelper.py README.md CHANGELOG.md
git commit -m "version YY.MM.DD.HH.MM - add menu 96 getOrgAntivirusProfile"
git push origin main
gh run watch                                  # Wait for container-build.yml
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest
podman ps                                     # Verify container is running
```

---

## Troubleshooting Cheat-Sheet

| Symptom                                            | Likely Cause / Fix                                                                 |
|----------------------------------------------------|------------------------------------------------------------------------------------|
| `safe_input` raises `EOFError`                     | SSH client closed mid-prompt. The wrapper exits 0 -- not a bug.                    |
| 401 Unauthorized                                   | `MIST_API_TOKEN` missing or wrong. Reload `.env`.                                  |
| 403 Permission Denied                              | Operator role lacks read-access to AV profiles. Mist admin must grant.             |
| 404 on a UUID you just got from the list export    | Wrong org context (`org_id`). Confirm the avprofile belongs to the supplied org.   |
| Repeated runs spawn duplicate SQLite rows          | PK strategy not registered. Confirm `getOrgAntivirusProfile` is in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. |
| `ruff` flags missing inline comments               | Principle VI violation. Add a `# why` comment on every executable line touched.    |
| `PermissionError: ...data/script.log`              | `chmod -R 777 data/` on the host before first container run.                       |
