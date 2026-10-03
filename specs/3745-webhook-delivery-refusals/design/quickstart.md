# Local verification: Webhook delivery refusals

Use only the owned Python 3.13 environment.
Do not supply an API token or connect a production store.

## Affected behavior

```bash
source .venv/bin/activate
rtk proxy python -B -m pytest -p no:cacheprovider -q \
  tests/unit/export/test_org_webhook_response_refusals.py \
  tests/integration/export/test_org_webhook_native_refusals.py \
  -W error::ResourceWarning
```

The native cases execute actual SDK operations and actual local CSV output.
Failed first and later responses require an exporter ERROR and zero persistence.
Successful controls require unchanged metadata, filenames, values, page order, and empty-result notices.
Each fixture closes its native sessions and Responses.

## Existing behavior

```bash
rtk proxy python -B -m pytest -p no:cacheprovider -q \
  tests/unit/export \
  tests/unit/api/test_response_integrity.py \
  tests/integration/test_mistapi_sdk_compatibility.py
```

An existing successful fixture may need a concrete successful response contract.
Only a separate narrow coordinator grant can permit that fixture correction.
Existing test identifiers, assertions, order, and aliases remain.

## Required quality input check

```bash
rtk proxy python -B -m pytest -p no:cacheprovider -s -q \
  tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

The output must report six input reads and three guide checks.
Run this check before either quality ratchet.
Use the unchanged config and baseline for full and committed-scope analysis.
Explicit native analysis must name the actual native test module as analyzed.

## Local-only completion

The completion evidence includes one clean local commit and an offline copy of the complete PR template.
The remote branch must remain absent.
No push, PR, Actions request, merge, live Mist request, container, or deployment belongs to this grant.
