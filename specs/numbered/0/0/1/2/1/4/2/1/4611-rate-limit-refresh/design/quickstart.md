# Quickstart: Verify Rate-Limit Refresh Status Handling

## Prerequisites

- Use the repository virtual environment.
- Do not set or use Mist credentials.
- Keep all SDK responses local to the test process.

## Focused test

```bash
python -m pytest tests/unit/test_rate_limiting.py -q
```

Expected result: all rate-limit unit tests pass. The new cases cover HTTP 403, HTTP 503, and HTTP 200 responses.

## Quality gate

After committing the intended test changes, run the documented test-quality ratchet against `origin/main`.

Expected result: the selected test module has no new findings, and the gate reports zero new findings against the baseline.

## Network safety

The focused tests replace the SDK endpoint method with local `APIResponse` objects. They must not call `getSelfApiUsage` over a network.
