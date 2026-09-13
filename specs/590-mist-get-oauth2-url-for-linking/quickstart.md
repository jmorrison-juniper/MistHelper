# Phase 1 Quickstart: GetOauth2UrlForLinking (Menu 149)

**Feature**: 590-mist-get-oauth2-url-for-linking
**Date**: 2026-06-29
**Audience**: Developers extending MistHelper; junior NOC engineers verifying the
new menu item end-to-end.

---

## Prerequisites

1. **Python 3.13+** active in a venv:
   ```powershell
   .venv\Scripts\Activate.ps1
   python --version   # expect 3.13.x or newer
   ```
2. **mistapi 0.59+** installed:
   ```powershell
   pip show mistapi | Select-String Version
   ```
3. **`.env` populated** with the operator's Mist credentials (file is git-ignored).

---

## Required .env Variables

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| `MIST_HOST` | yes | `api.mist.com` | Regional Mist Cloud host. Passed to `mistapi.APISession`. |
| `MIST_API_TOKEN` | yes | `abcdef...` | API token for the admin whose account will be link-fetched. Account-scoped endpoint -- no `org_id` needed. |
| `MISTHELPER_TEST_OAUTH_PROVIDER` | no | `google` | Default provider slug used only by `--test` sweeps (non-interactive). Defaults to `google` if unset. |
| `MIST_PAGE_LIMIT` | no | `1000` | Standard rate-limit / page-size tuning (irrelevant for this endpoint -- single object response -- but honoured for consistency). |

Never commit `.env`. The repo template lives at `deploy/.env.example`.

---

## Expected Output (data/)

| File / Table | Backend | Path / Name |
|--------------|---------|-------------|
| `self_oauth_link_url.csv` | CSV | `data/self_oauth_link_url.csv` |
| `self_oauth_link_url` | SQLite | table inside `data/mist_data.db` |
| `self_oauth_link_url` | ArangoDB | collection in the polyglot store |
| `mist:self:oauth:link_url:<provider>` | Redis | string key, JSON value |

Exactly one row is produced per invocation. Re-running with the same `provider`
upserts the row (overwrites `authorization_url`, refreshes `fetched_at_utc`,
preserves the schema).

---

## Example Invocation -- Interactive

```powershell
# from the repo root
.venv\Scripts\Activate.ps1
python MistHelper.py
```

Menu navigation:

```
Select operation: 149
[Self / OAuth2 -- Get link URL]
OAuth2 provider slug (e.g. google, microsoft, azure, okta): google
Optional post-link redirect URL (press Enter to skip): https://localhost:8055/post-link
```

Expected log lines (ASCII, no Unicode):

```
INFO  Fetching OAuth2 link URL for provider google
DEBUG OAuth2 link URL fetched: linked=False, url_length=312
INFO  Flattening 1 OAuth2 link URL record
DEBUG Flatten complete: 1 row
INFO  Writing 1 row to data/self_oauth_link_url.csv via DataExporter
DEBUG DataExporter write_with_format_selection returned 1 row written
```

Note that the `authorization_url` value itself is never logged -- only its length
and the `linked` flag, per Principle V (Observability).

---

## Example Invocation -- Direct CLI Flag

```powershell
python MistHelper.py --menu 149
```

In non-interactive (`--test`) mode the same menu is invoked with the `provider`
sourced from `MISTHELPER_TEST_OAUTH_PROVIDER` (default `google`) and `forward`
left unset (`None`).

---

## Method Outline (for implementers)

The new method lives on the new `SelfOauthExportUtils` class in `MistHelper.py`:

```python
class SelfOauthExportUtils:                                    # New class for "Self OAuth2" tag operations
    def __init__(self, apisession, data_exporter):             # Accept the session and exporter from the main app
        self.apisession = apisession                           # Mist API session (token + host)
        self.data_exporter = data_exporter                     # Shared multi-backend writer

    def export_self_oauth_link_url(self, provider=None, forward=None):  # Menu 149 entry point
        provider = self._prompt_provider(provider)             # safe_input wrapper, validates against allow-list
        if provider is None:                                   # Unknown provider -> early return after WARNING
            return                                             # No API call wasted on a guaranteed 404
        forward = self._prompt_forward(forward)                # safe_input wrapper, returns None on empty input
        logging.info("Fetching OAuth2 link URL for provider %s", provider)  # Action log: before API call
        response = mistapi.api.v1.self.oauth2.getOauth2UrlForLinking(       # Sole permitted Mist interface
            self.apisession, provider, forward=forward)
        logging.debug("OAuth2 link URL fetched: linked=%s, url_length=%d",  # Action log: after API call
                      response.data.get("linked"),
                      len(response.data.get("authorization_url") or ""))
        row = self._flatten(provider, forward, response.data)  # Build the six-column row
        self.data_exporter.write_with_format_selection(        # Multi-backend write
            data=[row],
            filename="self_oauth_link_url.csv",
            api_function_name="getOauth2UrlForLinking")
```

Total executable lines in the public method: 8 (well under the 25-line cap). The
two helpers `_prompt_provider` and `_prompt_forward` are themselves <=10 lines
each; the `_flatten` helper is <=8 lines. All three live on the same class, no
wrappers.

Every executable line above has been illustrated with an inline comment, matching
the Principle VI requirement that NEW code carry comments on every line.

---

## Quality Gates (run before every commit)

```powershell
# Syntax
python -m py_compile MistHelper.py

# Lint
python -m ruff check MistHelper.py

# Format
python -m black --check MistHelper.py

# Functional sweep (uses MISTHELPER_TEST_OAUTH_PROVIDER from .env)
python MistHelper.py --test
```

All four must pass clean. If `black --check` fails, run `python -m black
MistHelper.py` to auto-fix and rerun the gates.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `PermissionError: [Errno 13] Permission denied: '/app/data/...'` | Container `data/` dir not writable | `chmod -R 777 data/` before first container run |
| 404 from Mist | Unknown provider slug | Confirm `provider` is one of `google`, `microsoft`, `azure`, `okta` |
| 401 from Mist | `MIST_API_TOKEN` expired or absent | Regenerate token at `https://manage.mist.com/admin/?#!/myaccount/api-tokens` |
| Traceback on EOF in SSH session | `safe_input` not used | Confirm every prompt routes through `safe_input(..., context=...)` |
| Same `authorization_url` appears multiple times in CSV | PK strategy mis-registered | Verify entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` is `natural_pk` on `provider` |

---

## Sanity Test (no real Mist call)

```powershell
python -c "from mistapi.api.v1.self import oauth2; print(oauth2.getOauth2UrlForLinking.__doc__)"
```

Should print the SDK docstring describing path / query parameters. If `ImportError`,
the installed `mistapi` is below 0.59 -- upgrade with `pip install -U mistapi`.
