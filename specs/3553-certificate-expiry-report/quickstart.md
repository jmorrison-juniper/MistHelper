# Quickstart: Certificate Expiry Report

This guide validates the implementation after code is added. This planning step does not execute
these commands.

## Prerequisites

1. Use the worktree for issue #3553.
2. Activate the repository virtual environment.
3. Install the implementation dependency pin from `requirements.txt`.
4. Keep Mist API credentials outside source files and logs.

## Unit validation

Run the focused unit tests:

```powershell
python -m pytest tests\unit\reports\certificate_expiry
```

Expected result:

- All tests pass.
- No test makes a live network request.
- Fixture PEM bodies and private key-like values do not appear in captured logs or output rows.

## Local syntax and style validation

Run the standard local gates:

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py
```

Expected result:

- `py_compile` prints no output.
- Ruff reports all checks passed.
- Black reports that no file needs formatting.

## Report validation with synthetic data

Run the operation through a test fixture that replaces Mist API calls:

```powershell
python -m pytest tests\unit\reports\certificate_expiry\test_operation.py
```

Expected result:

- The operation does not prompt for input.
- The exporter receives `CertificateExpiry.csv`.
- The exporter receives `api_function_name="certificate_expiry_report"`.
- The row set includes all supported scopes.
- The console summary includes `expired`, `0-30`, `31-90`, and `more than 90`.

## Manual menu validation

Run the existing MistHelper safe test mode after implementation:

```powershell
python MistHelper.py --test
```

Expected result:

- Menu 272 completes without a prompt.
- `data\CertificateExpiry.csv` exists when fixture data contains certificate rows.
- The CSV contains metadata only.
- No row contains a PEM body or private key material.

## Evidence to record in the pull request

Record these items:

- Unit test command and result.
- Syntax, lint, and format command results.
- Row count by band from the test fixture.
- Confirmation that no live Mist request occurred during unit tests.
- Confirmation that privacy checks found zero certificate bodies and zero private key strings.
