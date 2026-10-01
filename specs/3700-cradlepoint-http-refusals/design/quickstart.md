# Validation: Cradlepoint HTTP refusals

## Prerequisites

Use this worktree's Python `3.13` environment.
Do not load live Mist credentials or connect to production stores.

The unchanged bootstrap failed when its copied macOS interpreter started `ensurepip`.
The owned UV-seeded recovery succeeded:

```bash
rtk proxy uv venv --python 3.13 --seed --clear .venv
rtk proxy .venv/bin/python scripts/bootstrap_worktree.py
```

The unchanged setup installed both requirement files.
Its package-record check found zero corrupt installs across 160 records.

## Native refusal proof

Before editing production behavior, run the native refusal and absent-transport cases.

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/unit/export/cradlepoint_http_refusals/test_native_responses.py -k "native_http_4xx_5xx_refusals or native_none_transport"
```

Expect failures on the unchanged exporter.
After the repair, expect all 31 cases to pass.
Each case must report one endpoint call and zero live requests.
Each refused case must report zero row, persistence, and writer callbacks.

## Focused regression proof

Run the complete owned exporter tests and the dedicated native tests.
Add the adjacent security-profile exporter and export-notice tests.
Use branch coverage for the affected exporter only.

Record exact commands and outcomes in [verification.md](verification.md).
Run the required local input preflight before either analyzer command.
Run the committed changed-scope ratchet only after the local commit.

## Publication

Keep this branch unpublished at position 33.
The observed main SHA is not a publication grant.
The coordinator must supply the explicit full verified-main SHA before publication.
