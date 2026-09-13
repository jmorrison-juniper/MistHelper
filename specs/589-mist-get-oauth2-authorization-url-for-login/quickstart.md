# Phase 1 Quickstart: getOauth2AuthorizationUrlForLogin Menu Item

**Feature**: 589 -- Mist API GET endpoint `getOauth2AuthorizationUrlForLogin`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Contract**: [contracts/get_oauth2_authorization_url_for_login.md](./contracts/get_oauth2_authorization_url_for_login.md)

## What this menu item does

Fetches the OAuth2 authorization URL plus the registered OAuth2 `client_id` for a named
identity provider (for example `google` or `azure`) from the Mist API endpoint
`GET /api/v1/login/oauth/{provider}`. Writes one row through `DataExporter` so the CSV,
SQLite, and ArangoDB+Redis backends are kept in sync. Re-running the menu upserts on
`provider`.

## Required `.env` variables

The standard Mist API credentials are the only required variables. No new variables are
introduced by this feature.

```dotenv
MIST_HOST=api.mist.com                                  # or api.eu.mist.com / api.gc1.mist.com / api.ac2.mist.com
MIST_API_TOKEN=<your-api-token>                         # token with at least read access to the account
```

Optional for non-interactive `--test` mode (consumed by the test harness only, not by
the menu method itself):

```dotenv
OAUTH_TEST_PROVIDER=google                              # default provider used by python MistHelper.py --test
```

## How to run locally

### Interactive (Windows + venv)

```powershell
cd "C:\Users\<you>\Code\MistHelper"
.\.venv\Scripts\Activate.ps1
python MistHelper.py
# Then at the prompt:
# Select option: 195
# OAuth2 provider name (e.g. google, azure): google
# Callback URL (press Enter to skip): [Enter]
```

### Direct invocation (automation-friendly)

```powershell
python MistHelper.py --menu 195
```

### Containerized run (Podman)

```powershell
podman exec -it misthelper python MistHelper.py --menu 195
```

### SSH access (port 2200)

```powershell
ssh -p 2200 misthelper@localhost
# The container forces MistHelper as the entry point; select option 195.
```

## Expected output

After a successful call MistHelper writes a single row to the configured backend:

- **CSV backend**: `data/login_oauth_authorization_url.csv` (created on first run, then
  upserted by `provider`).
- **SQLite backend**: row in `data/mist_data.db` table `login_oauth_authorization_url`,
  upserted with `INSERT OR REPLACE` on `provider`.
- **ArangoDB+Redis backend**: one document in collection
  `login_oauth_authorization_url`; Redis cache key is refreshed.

Sample CSV row:

```csv
provider,authorization_url,client_id,forward,fetched_at
google,https://accounts.google.com/o/oauth2/v2/auth?client_id=...&state=...,1234567890-abc.apps.googleusercontent.com,,2026-06-29T22:37:00+00:00
```

## Sample interactive transcript

```text
$ python MistHelper.py --menu 195
INFO  Loaded .env from C:\Users\me\Code\MistHelper\.env
INFO  Mist API session established for host api.mist.com
INFO  Fetching OAuth2 authorization URL for provider google
INFO  Writing 1 row to backend csv as login_oauth_authorization_url
INFO  Wrote data\login_oauth_authorization_url.csv (1 row, upserted on provider)
INFO  Done. Menu 195 returned 0.
```

## Implementation outline (target shape for the implementation pass)

The menu method lives on the chosen login-export class (proposed:
`LoginOAuthExportUtils`). The 5-Item Rule keeps it under 25 lines and within 5 logical
blocks:

```python
def export_oauth2_authorization_url(self) -> None:           # new menu method; no required args
    """Fetch OAuth2 authorization URL for a provider (menu 195)."""
    provider = safe_input(                                   # prompt 1 -- required path param
        "OAuth2 provider name (e.g. google, azure): ",
        context="oauth_auth_url:provider",
    ).strip().lower()                                        # normalize before validation
    if not re.fullmatch(r"[a-z0-9_-]{1,32}", provider):      # reject malformed provider input
        logging.warning("Invalid OAuth2 provider name; aborting")  # log and return without traceback
        return
    forward = safe_input(                                    # prompt 2 -- optional callback URL
        "Callback URL (press Enter to skip): ",
        context="oauth_auth_url:forward",
    ).strip() or None                                        # empty input -> None
    logging.info("Fetching OAuth2 authorization URL for provider %s", provider)  # before-API log
    oauth_mod = importlib.import_module("mistapi.api.v1.admins.login_-_oauth2")  # dash in module name
    response = oauth_mod.getOauth2AuthorizationUrlForLogin(self.api, provider, forward=forward)
    logging.debug("OAuth2 response status=%s url_len=%d client_id_len=%d",       # after-API log (no secrets)
                  response.status_code, len(response.data.get("authorization_url", "")),
                  len(response.data.get("client_id", "")))
    row = {                                                  # flatten into one row
        "provider": provider,
        "authorization_url": response.data["authorization_url"],
        "client_id": response.data["client_id"],
        "forward": forward,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    DataExporter.write_with_format_selection(                # multi-backend write
        [row],
        filename="login_oauth_authorization_url",
        api_function_name="getOauth2AuthorizationUrlForLogin",
    )
```

Every executable line above carries an inline comment per Constitution Principle VI; the
before / after `logging.info` and `logging.debug` pair satisfies Principle VII.

## Quality gates (run before every commit)

```powershell
python -m py_compile MistHelper.py                          # syntax-only check; no output = success
python -m ruff check MistHelper.py                          # lint must be clean
python -m black --check MistHelper.py                       # formatting must match; drop --check to auto-fix
python MistHelper.py --test                                 # full menu test sweep (menu 195 included)
```

All four gates must pass green before the PR is eligible for the `auto-merge` label and
the container build pipeline (`.github/workflows/container-build.yml`).

## Validation checklist

- [ ] Menu number 195 (or fallback 50) verified free at task generation.
- [ ] `ENDPOINT_PRIMARY_KEY_STRATEGIES["getOauth2AuthorizationUrlForLogin"]` present.
- [ ] `safe_input()` used for both prompts with explicit `context=` strings.
- [ ] `DataExporter.write_with_format_selection()` used for output.
- [ ] Inline comment on every executable line in the new method.
- [ ] `logging.info` before and `logging.debug` after every meaningful step.
- [ ] No secrets (API token, full `authorization_url`, `client_id`) logged above DEBUG.
- [ ] README.md menu count and table updated.
- [ ] CHANGELOG.md `version YY.MM.DD.HH.MM` entry added.
- [ ] All four quality gates green locally and in CI.
