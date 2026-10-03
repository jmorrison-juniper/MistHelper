# Local Verification

## Preconditions

Use only the owned worktree and its `.venv`.
Keep all publication windows closed.
Use controlled transport, temporary output, and no Mist credentials.

## Runtime Cases

Run both new scopes with the owned interpreter.

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/unit/export/test_wifi_clients_response_failures.py tests/integration/export/test_wifi_clients_native_response_failures.py
```

Each failed response must produce zero final output writes.
Successful controls must retain complete records and valid empty-data meaning.
Every native case must make zero live HTTP requests.

## Quality Inputs

Run the current required-input preflight before either test-quality ratchet.

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Use unchanged settings and baseline for the complete ratchet.
After the local commit, use fetched `origin/main` for the committed changed-scope ratchet.
Force native module analysis separately and record analyzed counts.

## Evidence Boundary

Private session artifacts hold exact commands, results, hashes, and runtime counts.
The offline pull request body retains the current template.
The public issue handoff contains safe counts and local commit identities only.
No push, pull request, Actions request, merge, production operation, or release occurs.
