# Phase 1 Quickstart: countSiteDevices

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This quickstart shows a developer how to run, exercise, and validate the new menu
item on a Windows 11 dev box. Container parity is identical (paths normalize via
`pathlib.Path` and `os.path.join`).

## Prerequisites

- Windows 11 with PowerShell 7+ (or any shell on Linux container).
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
MIST_SITE_ID=<your-default-site-uuid>   # optional default for the site_id prompt
```

Loading is handled by the existing `python-dotenv` bootstrap in `MistHelper.py`.
The API token is consumed by `mistapi.APISession` and is never written to logs
or stdout.

## Expected output filenames

Files land under `data/` (the directory is enforced at runtime; create it with
`chmod -R 777 data/` on Linux first to satisfy the non-root container user).

- CSV (per `distinct` choice):
  `data/site_<first-8-of-site-uuid>_devices_count_<distinct_field>.csv`
- CSV (no `distinct`, server default):
  `data/site_<first-8-of-site-uuid>_devices_count_summary.csv`
- SQLite: `data/mist_data.db`, single table `site_devices_count` (shared across
  all `distinct` choices; `distinct_field` is a discriminator column)

## Example invocation

```powershell
python MistHelper.py
```

Interactive transcript (proposed menu number 72 -- final number confirmed at task
time):

```
Select menu option: 72
Site ID (UUID) [press Enter for default from .env]:
Group by which field? (model/version/hostname/mac/mxedge_id/lldp_system_name -- press Enter for server default): model
Result limit (default 100): 100
[INFO] Counting devices for site 0a1b2c3d-... distinct=model limit=100
[DEBUG] Count result: total=4 buckets=4
[INFO] Flattening 4 bucket rows
[DEBUG] Flattened 4 bucket rows
[INFO] Writing site devices count via DataExporter
```

Non-interactive smoke test (accepts the `.env` site default, omits `distinct`,
uses limit=100):

```powershell
python MistHelper.py --menu 72
```

Pipe-friendly variant (defaults to `.env` site, no `distinct`, default limit):

```powershell
echo "`r`n`r`n`r`n" | python MistHelper.py --menu 72
```

## Skeleton of the new method

The full implementation is produced by `/speckit.implement`; this skeleton shows
the expected shape so that inline-comment and action-logging coverage can be
reviewed before code is written. Every executable line carries a `#` comment
(Constitution VI), and every meaningful action is bracketed by `logging.info()`
/ `logging.debug()` calls (Constitution VII).

```python
class SiteDeviceExportUtils:                                                        # existing class, no new wrapper

    def export_site_devices_count(self, site_id=None, distinct_field=None,          # menu 72 entrypoint
                                  limit=100):                                       # 100 matches OpenAPI default
        logging.info("Prompting for site_id for site devices count menu item")      # before-prompt action log
        site_id = site_id or safe_input(                                            # honor caller override else prompt
            "Site ID (UUID): ",                                                     # human-readable prompt text
            context="site_devices_count:site_id",                                   # SSH/container EOF context tag
            default=os.environ.get("MIST_SITE_ID", ""),                             # fall back to .env default
        )
        if not is_valid_uuid(site_id):                                              # validate before any API call
            logging.warning("Invalid site_id %s -- aborting menu 72", site_id)      # log validation failure (no traceback)
            return                                                                  # early return per safety-first principle

        logging.info("Prompting for distinct grouping field")                       # before-prompt action log
        distinct_field = (distinct_field if distinct_field is not None              # caller override wins
                          else safe_input(                                          # else ask the user
                              "Group by which field? (model/version/hostname/"
                              "mac/mxedge_id/lldp_system_name -- press Enter "
                              "for server default): ",
                              context="site_devices_count:distinct",                # EOF context tag
                              default="",                                           # empty = omit param entirely
                          )).strip()

        logging.info("Prompting for result limit")                                  # before-prompt action log
        limit_raw = safe_input(                                                     # ask for limit, default 100
            "Result limit (default 100): ",                                         # human-readable prompt text
            context="site_devices_count:limit",                                     # EOF context tag
            default=str(limit),                                                     # current limit becomes default
        )
        try:                                                                        # parse int with safe fallback
            limit = int(limit_raw)                                                  # numeric conversion
        except (TypeError, ValueError):                                             # bad input is non-fatal
            logging.warning("Bad limit %r -- falling back to 100", limit_raw)       # log and continue
            limit = 100                                                             # safe default

        logging.info("Counting devices for site %s distinct=%s limit=%d",           # before-API-call action log
                     site_id, distinct_field or "<default>", limit)
        api_kwargs = {"limit": limit}                                               # always pass limit
        if distinct_field:                                                          # only set distinct when supplied
            api_kwargs["distinct"] = distinct_field                                 # SDK kwarg matches query param name
        response = mistapi.api.v1.sites.devices.count.countSiteDevices(             # SDK call
            self.apisession, site_id, **api_kwargs,                                 # site_id is positional
        )
        envelope = response.data or {}                                              # normalize None to empty dict
        buckets = envelope.get("results", []) or []                                 # protect against missing key
        logging.debug("Count result: total=%s buckets=%d",                          # after-API-call summary log
                      envelope.get("total"), len(buckets))

        logging.info("Flattening %d bucket rows", len(buckets))                     # before-flatten action log
        polled_at = datetime.now(timezone.utc).isoformat(timespec="seconds")        # one timestamp for whole poll
        rows = self._flatten_count_results(site_id, envelope, buckets, polled_at)   # build row list
        logging.debug("Flattened %d bucket rows", len(rows))                        # after-flatten count log

        logging.info("Writing site devices count via DataExporter")                 # before-export action log
        suffix = distinct_field or "summary"                                        # filename suffix per choice
        DataExporter.write_with_format_selection(                                   # multi-backend write
            rows,                                                                   # list-of-dicts interface
            filename=f"site_{site_id[:8]}_devices_count_{suffix}",                  # human-friendly stem
            api_function_name="countSiteDevices",                                   # PK strategy lookup key
        )
```

The `_flatten_count_results()` helper lives on the same `SiteDeviceExportUtils`
class, stays under 25 lines, takes `<=5` parameters, and follows the same
comment- and log-density rules.

## Quality gates (all must pass before commit)

Run these from the repository root with the venv active:

```powershell
python -m py_compile MistHelper.py        # 1. Syntax check (zero output = pass)
python -m ruff check MistHelper.py        # 2. Lint (zero violations = pass)
python -m black --check MistHelper.py     # 3. Format (zero diffs = pass; rerun without --check to auto-fix)
python MistHelper.py --test               # 4. Functional smoke test (menu 72 included)
```

The `--test` sweep automatically skips heavy/destructive operations (14, 18,
63-65, 90-100). Menu 72 sits inside the standard sweep range, so a green run
confirms the new item works end to end against the site configured in `.env`.

## Full deployment pipeline (Constitution Principle IV)

After all four quality gates pass:

```powershell
git add MistHelper.py README.md CHANGELOG.md
git commit -m "version YY.MM.DD.HH.MM - add menu 72 countSiteDevices"
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
