# Phase 1 Quickstart: getApiToken (Menu 96)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/self/apitokens/{apitoken_id}`

This quickstart shows a junior NOC engineer how to exercise the new menu item locally,
end-to-end, including the quality gates that must pass before commit.

## 1. Prerequisites

- Windows 11 + Python 3.13 venv (`.venv\Scripts\Activate.ps1`) **or** Podman container
  `ghcr.io/jmorrison-juniper/misthelper:latest` running on port 2200 (SSH) and 8055
  (web).
- A valid Mist API token with read access to the authenticated admin's own tokens.
- The id of at least one existing API token belonging to that admin. If unknown, run
  menu number for `listApiTokens` first (sibling endpoint) to discover ids.

## 2. Required `.env` Variables

Stored in `.env` at the repository root (git-ignored). The container expects the same
file mounted read-only at `/app/.env`.

```dotenv
# Mist Cloud region host (e.g. api.mist.com, api.eu.mist.com, api.gc1.mist.com)
MIST_HOST=api.mist.com

# Bearer token for mistapi.APISession -- never echoed, never logged
MIST_API_TOKEN=<your-personal-api-token>
```

No `MIST_ORG_ID` is required for this endpoint -- the path is account-scoped. No
additional new variables are introduced by this feature.

## 3. Expected Output Files

After a successful run against `apitoken_id=53f10664-3ce8-4c27-b382-0ef66432349f`:

| Backend         | Artifact                                                                 |
|-----------------|--------------------------------------------------------------------------|
| CSV (default)   | `data/self_api_token_53f10664-3ce8-4c27-b382-0ef66432349f.csv` (1 row + header) |
| SQLite          | Row upserted into `data/mist_data.db` table `self_api_tokens` (PK `id`)  |
| ArangoDB+Redis  | Document upserted into collection `self_api_tokens`; Redis cache key `self_api_token:<id>` refreshed |

Repeated runs against the same id never produce duplicate rows -- the natural PK on
`id` guarantees clean upserts.

## 4. Example Interactive Invocation

```powershell
# From repo root, with venv active
python MistHelper.py

# At the main menu prompt, type the new operation number:
> 96

# MistHelper logs (ASCII only):
# INFO  Selected menu 96: View single API token (self)
# INFO  Prompting for apitoken_id
# (safe_input prompts; in SSH/container EOF cleanly exits 0)
apitoken_id: 53f10664-3ce8-4c27-b382-0ef66432349f
# INFO  Fetching API token 53f10664-3ce8-4c27-b382-0ef66432349f
# DEBUG API token: name=org_token_xyz created=1690000000.0 last_used=1690115110
# INFO  Writing 1 record(s) via DataExporter
# DEBUG Wrote data/self_api_token_53f10664-3ce8-4c27-b382-0ef66432349f.csv
# DEBUG Upserted 1 row into SQLite table self_api_tokens
```

## 5. Example Non-Interactive Invocation

```powershell
# Direct menu invocation -- used by --test and by automation
python MistHelper.py --menu 96 --apitoken-id 53f10664-3ce8-4c27-b382-0ef66432349f
```

Exit code 0 indicates success; non-zero indicates the API call or output backend failed
(consult `data/script.log` for the full traceback).

## 6. Quality Gates (MANDATORY before commit)

Run all four; all must pass.

```powershell
# 1. Python syntax check -- no output means valid
python -m py_compile MistHelper.py

# 2. Lint check -- must finish clean (no warnings, no errors)
python -m ruff check MistHelper.py

# 3. Format check -- if this fails, run `python -m black MistHelper.py` to auto-fix
python -m black --check MistHelper.py

# 4. End-to-end self-test (skip list excludes 14, 18, 63-65, 90-100 -- 96 is in range)
python MistHelper.py --test
```

If any gate fails, fix the cause locally before committing. The CI pipeline
(`.github/workflows/ci.yml`) reruns the same gates plus mypy, Hypothesis, Bandit,
pip-audit, CodeQL, and Playwright. Failures on `main` auto-open issues labelled
`quality-gate`; passes auto-close them.

## 7. Deployment Pipeline (AFTER local gates pass)

```powershell
# Stage the three touched files
git add MistHelper.py README.md CHANGELOG.md

# Commit with the project's UTC timestamp convention
git commit -m "version YY.MM.DD.HH.MM - add menu 96 getApiToken"

# Push -- triggers .github/workflows/container-build.yml
git push origin main

# Watch the container build
gh run watch (gh run list --workflow=container-build.yml --limit 1 --json databaseId -q '.[0].databaseId')

# Pull the freshly built image
podman pull ghcr.io/jmorrison-juniper/misthelper:latest

# Restart the local container
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest

# Confirm it is up
podman ps
```

Do not skip any pipeline step -- the user expects the container to be running with the
new menu item after the PR merges.
