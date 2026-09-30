# Quickstart: Organization Security Posture Checklist

This guide validates the planned feature after implementation.

## Prerequisites

1. Use Python 3.13 or newer.
2. Bootstrap the worktree if `.venv` is absent.
3. Activate the virtual environment.
4. Use fixture data for `--test` validation.

## Validate the test-mode checklist

Run the feature handler in test mode after implementation:

```powershell
python -c "from src.reports.org_security_posture.runner import OrgSecurityPostureChecklist; OrgSecurityPostureChecklist.run(test_mode=True)"
```

Expected result:

- The run does not prompt.
- The run writes `data/OrgSecurityPosture.csv`.
- The CSV has the required columns from `contracts/checklist-output.md`.
- The CSV contains at least twelve rows.
- The console summary prints pass, fail, and review counts.

## Validate the integrated menu

Run the normal safe test mode after the integration pull request wires menu 276:

```powershell
python MistHelper.py --test
```

Expected result:

- Menu 276 runs as part of the safe test path.
- The run writes `data/OrgSecurityPosture.csv`.

## Validate absent API settings

Use a fixture where the API policy setting is absent.

Expected result:

- The affected API check verdict is `review`.
- The reason contains `absent`.
- No absent setting produces `pass`.

## Validate webhook transport

Use a fixture with one webhook URL that starts with `http://`.

Expected result:

- `ORGSEC-API-003` returns `fail`.
- The reason states that a non-HTTPS webhook URL exists.

## Validate stable check IDs

Run the checklist twice with the same fixture.

Expected result:

- The check IDs are identical across both runs.
- The registry contains no duplicate check IDs.
- The CSV row order is deterministic.

## Validate source operation names

Before client code is written, verify these operation IDs in `documentation/mist-api-openapi3json.json` and `mistapi`:

- `getOrgSettings`
- `listOrgSsos`
- `listOrgAdmins`
- `listOrgApiTokens`
- `listOrgWebhooks`

Expected result:

- Each operation exists in OpenAPI.
- Each operation has a matching `mistapi` method.
- The implementation records the exact response keys used by each check.

## Validate local gates

Run the smallest gate set that covers touched implementation files:

```powershell
python -m py_compile MistHelper.py
python -m ruff check <touched-python-files>
python -m black --check <touched-python-files>
python -m pytest <touched-test-files>
```

Expected result:

- Each command passes.
- Any failure becomes a separate issue if it is unrelated to this feature.
