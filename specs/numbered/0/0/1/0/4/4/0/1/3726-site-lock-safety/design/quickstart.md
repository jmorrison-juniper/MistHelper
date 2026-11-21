# Quickstart: Site Lock Safety for Uncertain Upgrade Replies

## Prerequisites

- Use the repository's Python 3.13 environment.
- Do not set or use a Mist API credential for these tests.
- Do not start a service or run a firmware operation.

## Validate the Outcome Rules

Run the focused unit tests:

```sh
python -B -m pytest -p no:cacheprovider -q \
  tests/unit/firmware/test_aggregate_upgrade_service.py \
  tests/unit/upgrade_portal/test_org_upgrade_lock_release.py \
  tests/unit/upgrade_portal/test_org_cancel_outcomes.py
```

Expected result: all tested uncertain replies remain unknown, every uncertain operation keeps its site locks, and documented refusals retain the existing release behavior.

Run the existing repeat-submission contract:

```sh
python -B -m pytest -p no:cacheprovider -q \
  tests/contract/upgrade_portal/test_org_upgrade_routes.py::test_unknown_submission_blocks_a_repeat
```

Expected result: an unknown submission does not permit a second firmware request.

Run lint and formatting checks on the changed Python files:

```sh
python -m ruff check <changed-python-files>
python -m black --check <changed-python-files>
```

Expected result: Ruff reports no findings, and Black reports no formatting changes.

## Expected Outcome Matrix

| Reply | Child state | Site lock |
|---|---|---|
| HTTP 400, 401, 403, or 404 without an identifier | `rejected` | Eligible for release |
| HTTP 408, 429, 5xx, 499, or missing status | `submission_unknown` | Held |
| Malformed success or missing identifier | `submission_unknown` | Held |
| Transport exception after the write | Existing `submission_unknown` | Held |
| Known `not_submitted` child | `not_submitted` | Eligible for release |

All tests use offline stand-ins. They do not call Mist Cloud or modify a production lock.
