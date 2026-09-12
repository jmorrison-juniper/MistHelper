# Phase 1 Quickstart: getOrgNacCrl

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This quickstart shows a developer how to run, exercise, and validate the new menu
item on a Windows 11 dev box. Container parity is identical (paths normalize via
`pathlib.Path` and `os.path.join`).

## Prerequisites

- Windows 11 with PowerShell 7+ (or any shell on the Linux container).
- Python 3.13 or newer on PATH.
- Repository cloned at the worktree root referenced in `plan.md`.
- Working `.venv` activated:

  ```powershell
  .venv\Scripts\Activate.ps1
  ```

- `mistapi` 0.59+ installed:

  ```powershell
  python -m pip install --upgrade mistapi python-dotenv
  ```

## Required `.env` variables

Create or update `.env` in the repository root (git-ignored). Never commit this
file.

```ini
MIST_HOST=api.mist.com
MIST_API_TOKEN=<your-mist-api-token>
MIST_ORG_ID=<your-default-org-uuid>   # optional default for the org_id prompt
```

Loading is handled by the existing `python-dotenv` bootstrap in `MistHelper.py`.
The API token is consumed by `mistapi.APISession` and is never written to logs
or stdout.

## Expected output filenames

Files land under `data/` (the directory is enforced at runtime; create it with
`chmod -R 777 data/` on Linux first to satisfy the non-root container user).

- CSV: `data/org_<first-8-of-org-uuid>_nac_crl_files.csv`
- SQLite: `data/mist_data.db`, table `org_nac_crl_files`.
- ArangoDB (when configured): collection `org_nac_crl_files` keyed on the Mist
  UUID; Redis cache namespace `org_nac_crl_files:<id>`.

## Example invocation

```powershell
python MistHelper.py
```

Interactive transcript (proposed menu number 58 -- final number confirmed at task
time):

```
Select menu option: 58
Org ID (UUID) [press Enter for default from .env]:
[INFO] Fetching NAC CRL files for org 0a1b2c3d-...
[DEBUG] Received 3 NAC CRL file rows
[INFO] Flattening NAC CRL file payload
[DEBUG] Flattened 3 NAC CRL file rows
[INFO] Writing NAC CRL files via DataExporter
```

Non-interactive smoke test:

```powershell
python MistHelper.py --menu 58
```

Pipe-friendly variant (uses the `MIST_ORG_ID` default from `.env`):

```powershell
echo "" | python MistHelper.py --menu 58
```

## Skeleton of the new method

The full implementation is produced by `/speckit.implement`; this skeleton
documents the expected shape so the inline-comment and action-logging coverage
can be reviewed before the code is written. Every executable line carries a `#`
comment (Constitution VI). Every meaningful action is bracketed by
`logging.info()` / `logging.debug()` calls (Constitution VII).

```python
class NacExportUtils:                                                               # existing class; fallback OrgSettingExportUtils

    def export_org_nac_crl(self, org_id=None):                                      # menu 58 entrypoint, <=25 lines
        logging.info("Prompting for org_id for NAC CRL list menu item")             # before-prompt action log
        org_id = org_id or safe_input(                                              # honor caller override else prompt user
            "Org ID (UUID): ",                                                      # human-readable prompt text
            context="org_nac_crl:org_id",                                           # SSH/container EOF context tag
            default=os.environ.get("MIST_ORG_ID", ""),                              # fall back to .env default
        )
        if not is_valid_uuid(org_id):                                               # validate before any API call
            logging.warning("Invalid org_id %s -- aborting menu 58", org_id)        # log validation failure (no traceback)
            return                                                                  # early return per safety-first principle

        logging.info("Fetching NAC CRL files for org %s", org_id)                   # before-API-call action log
        response = mistapi.api.v1.orgs.setting.mist_nac_crls.getOrgNacCrl(          # actual SDK call (URL-derived module path)
            self.apisession, org_id,                                                # only required path param
        )
        body = response.data or {}                                                  # normalize None to empty dict
        results = body.get("results", []) or []                                     # extract the array, default to empty list
        logging.debug("Received %d NAC CRL file rows", len(results))                # after-API-call count log

        logging.info("Flattening NAC CRL file payload for org %s", org_id)          # before-flatten action log
        crl_rows = self._flatten_nac_crl_rows(org_id, results)                      # build list of flat dicts
        logging.debug("Flattened %d NAC CRL file rows", len(crl_rows))              # after-flatten count log

        logging.info("Writing NAC CRL files via DataExporter")                      # before-export action log
        DataExporter.write_with_format_selection(                                   # multi-backend write
            crl_rows,                                                               # list-of-rows interface
            filename=f"org_{org_id[:8]}_nac_crl_files",                             # human-friendly filename stem
            api_function_name="getOrgNacCrl",                                       # PK strategy lookup key
        )
```

The private helper `_flatten_nac_crl_rows(org_id, results)` returns a list of
dicts shaped to match the SQLite columns in `data-model.md`: it injects `org_id`
and `polled_at_utc` into every row, copies the API fields verbatim, and stays
under 25 lines / 5 nesting blocks. It lives on the same class -- no standalone
wrapper functions.

## Quality gates (all must pass before commit)

Run these from the repository root with the venv active:

```powershell
python -m py_compile MistHelper.py        # 1. Syntax check (zero output = pass)
python -m ruff check MistHelper.py        # 2. Lint (zero violations = pass)
python -m black --check MistHelper.py     # 3. Format (zero diffs = pass; rerun without --check to auto-fix)
python MistHelper.py --test               # 4. Functional smoke test (menu 58 included)
```

The `--test` sweep automatically skips heavy / destructive operations (14, 18,
63-65, 90-100). Menu 58 sits inside the standard sweep range, so a green run
confirms the new item works end to end against the org configured in `.env`.

## Full deployment pipeline (Constitution Principle IV)

After all four quality gates pass:

```powershell
git add MistHelper.py README.md CHANGELOG.md
git commit -m "version YY.MM.DD.HH.MM - add menu 58 getOrgNacCrl"
git push origin main
gh run list --workflow=container-build.yml --limit 1
gh run watch <run-id>
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
  -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
  ghcr.io/jmorrison-juniper/misthelper:latest
podman ps
```

The pipeline must not be skipped. The container in production reflects every
commit on `main`.
