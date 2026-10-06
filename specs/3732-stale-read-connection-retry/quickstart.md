# Quickstart: Validate safe read recovery

## Prerequisites

1. Run `python3 scripts/bootstrap_worktree.py` if `.venv` does not exist.
2. Activate `.venv`.
3. Do not set a production Mist credential for these tests.

## Reserved feature tests

Run:

```bash
python -m pytest \
  tests/unit/refactors/test_issue_3732_read_retry.py \
  tests/integration/web_portal/test_issue_3732_pick_list_failures.py
```

Expected result:

- The local GET reset test records two attempts and succeeds.
- The local HEAD reset test records two attempts and succeeds.
- The local POST reset test records one attempt and fails.
- Each write-method case records one attempt.
- The status test records one attempt for an HTTP error.
- Each picker reports the fixed reason for an unavailable response.
- Each empty HTTP 2xx picker reports the existing no-rows reason.
- The run makes zero live Mist API calls.

## Related regression tests

Run:

```bash
python -m pytest \
  tests/unit/refactors/test_initialize_mist_session.py \
  tests/unit/refactors/test_app_context_session_state.py \
  tests/unit/web_portal/test_portal_picklist_reason.py \
  tests/unit/web_portal/test_portal_sdk_calls.py \
  tests/unit/upgrade_portal/test_org_upgrade_service.py
```

Expected result:

- The session configures once.
- The timeout contract remains active.
- The picker reasons remain compatible.
- Each picker still uses the installed mistapi method.
- The upgrade write session keeps zero SDK and transport retries.

## Static gates

Run:

```bash
python -m ruff check \
  src/foundation/support/refactors/initialize_mist_session.py \
  web_portal/routes/operations.py \
  tests/unit/refactors/test_issue_3732_read_retry.py \
  tests/integration/web_portal/test_issue_3732_pick_list_failures.py

python -m black --check \
  src/foundation/support/refactors/initialize_mist_session.py \
  web_portal/routes/operations.py \
  tests/unit/refactors/test_issue_3732_read_retry.py \
  tests/integration/web_portal/test_issue_3732_pick_list_failures.py

python -m mypy \
  src/foundation/support/refactors/initialize_mist_session.py \
  web_portal/routes/operations.py \
  --config-file pyproject.toml

bandit -c pyproject.toml -q \
  src/foundation/support/refactors/initialize_mist_session.py \
  web_portal/routes/operations.py
```

Expected result:

- Ruff prints `All checks passed`.
- Black reports no file change.
- mypy reports success.
- Bandit reports no finding.

## Symbol and test-quality gates

Run `symbol-diff` against the pull request base for each production file.
Run the repository test-quality preflight.
After the implementation commit, run the changed-test quality gate against `origin/main`.

Expected result:

- No module-level name changes.
- The preflight reads each required input.
- The analyzer reports zero new findings.

## STE gate

Run:

```bash
ste-linter --config .ste-linter.toml --min-score 80 \
  specs/3732-stale-read-connection-retry/plan.md \
  specs/3732-stale-read-connection-retry/research.md \
  specs/3732-stale-read-connection-retry/data-model.md \
  specs/3732-stale-read-connection-retry/quickstart.md \
  specs/3732-stale-read-connection-retry/contracts/transport-retry.md \
  specs/3732-stale-read-connection-retry/contracts/pick-list-read.md \
  changelog.d/issue-3732-stale-read-connection-retry.md
```

Expected result:

- Each file scores 80 or more.
- The linter reports zero errors.

## Changelog text

Create `changelog.d/issue-3732-stale-read-connection-retry.md` during implementation.
Use one `###` heading and one `Fixed` bullet.
Name issue #3732 in the bullet.
