# Quickstart: Endpoint Payload Preservation

This guide validates the planned repair with local response fixtures only.
Do not use a Mist Cloud credential, production store, or live endpoint.

## Prerequisites

```powershell
python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

Use the prepared environment when it already exists. Keep
`mistapi>=0.64.0,<0.65` unchanged.

## Red proof

Run the new documented-object tests before changing production code:

```powershell
python -m pytest tests\unit\export\test_endpoint_family_exporter.py -k "documented or object or received or written" -q
```

Expected result: the documented summary and classifier object tests fail
because `mistapi.get_all` returns zero records for objects without `results`.

## Targeted validation

After implementation, run:

```powershell
python -m pytest tests\unit\export\test_endpoint_family_exporter.py -q
python -m pytest tests\unit\test_pk_strategies.py -q
python -m pytest tests\guardrails\test_endpoint_catalog.py -q
python -m pytest tests\contract\test_mistapi_sdk_compatibility.py -q
```

These tests must prove the two object shapes, empty cases, unknown-object
handling, loud discard logging, count mismatch evidence, list pagination,
`results` pagination, exact dispatch, error safety, secret redaction, and
deprecated SDK attribute absence.

## Applicable repository gates

Run the gates that apply to the changed manifest paths:

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
bandit -c pyproject.toml -r . -q
bandit-exclude-check
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/0/0/0/0/0/0/endpoint-payload-preservation/*.md specs/numbered/0/0/0/0/0/0/0/0/endpoint-payload-preservation/contracts/*.md
```

Run `test-quality-analyzer` only after implementation tests are committed and
the intended base reference is available. Do not change the baseline.

## Acceptance evidence

Record actual received and written counts for both documented objects.
Record zero counts for each true empty response. Record pagination order and
the exact output call. Record the loud discard message for unsupported data.
Record that `endpoint_primary_key_strategies.py` remained unchanged.
