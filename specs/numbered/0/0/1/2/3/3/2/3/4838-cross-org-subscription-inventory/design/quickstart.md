# Quickstart: Cross-Org Subscription and Stock Inventory

## Local Validation

Run the unit tests for the report package:

```powershell
rtk .venv\Scripts\python.exe -m pytest -q tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry
```

Run compile, lint, format, and types:

```powershell
rtk .venv\Scripts\python.exe -m py_compile MistHelper.py
rtk .venv\Scripts\python.exe -m ruff check .
rtk .venv\Scripts\python.exe -m black --check .
rtk .venv\Scripts\python.exe -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
```

## Live Single-Organization Test

Set the Mist API token in the ignored `.env` file.
Set `org_id` to an authorized T-Mobile or customer organization.
Start the report with a read-only API token:

```powershell
rtk .venv\Scripts\python.exe MistHelper.py --menu 308
```

The report should create five result files under `data/`.
It should create no firmware or device change request.

## Live MSP Test

Start an interactive login session:

```powershell
rtk .venv\Scripts\python.exe MistHelper.py --login --menu 308
```

Complete the email, password, and 2FA prompts.
The active session must have permission to list MSP organizations.
The report should discover and scan every authorized organization.

## T-Mobile Evidence Baseline

The 2026-11-19 T-Mobile Validation Lab read found:
- 41 organization license records
- 48 license usage rows
- 79 inventory devices
- One unassigned SSR130 stock device
- Two JSI contract rows
- No serial match between the stock device and JSI rows

The direct read received HTTP 403 for MSP organizations and MSP licenses.
The interactive MSP path is the required authentication path for the complete MSP view.

## Expected Stock Record

The stock report should mark the T-Mobile SSR130 as:
- Inventory type: gateway or SSR
- Deployment status: stock
- Site: missing
- License review: required
- JSI match: no-match or unavailable

The contract report should not invent a contract end date without JSI evidence.
