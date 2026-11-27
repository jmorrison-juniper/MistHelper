# Quickstart: Mist Identity Object Sign-In

These steps reproduce the defect and verify the fix. Run each command from the `mist-ops-platform` directory unless the step says another directory. The tests run offline. No step makes a live Mist call.

## Prerequisites

- A repository checkout of branch `fix/4749-mist-identity-object-login`, or of `main` before the change.
- The Python environment of `mist-ops-platform`. Follow the bootstrap note in development-setup.md (research row 68). The note warns that a global interpreter hides the environment.
- No Mist credential. Every test patches the SDK method.

## Scenario 1: Reproduce the defect on main

1. Run the object-path contract tests.

   ```text
   python -m pytest tests/contract/test_self_identity_response_contract.py -q
   ```

   Expected before the change: TC-01 fails because the list holds no identity record. TC-06 fails because the call follows a `next` cursor and makes a second call.

2. Run the token-check tests.

   ```text
   python -m pytest tests/contract/test_validation_token_guard.py -q
   ```

   Expected before the change: TG-01 fails because the identity object is dropped. TG-02 fails because no warning is logged.

3. Confirm that the dictionary drop is in place. The change point is `_extract_list`.

   ```text
   python -m pytest tests/unit/mist/test_list_status.py -q -k drops_a_dict_body
   ```

   Expected: one test passes. This test pins the drop rule that the change keeps for list endpoints (research row 19).

## Scenario 2: Verify the fix

1. Run both new modules. Expected: 13 tests pass.

   ```text
   python -m pytest tests/contract/test_self_identity_response_contract.py tests/contract/test_validation_token_guard.py -q
   ```

2. Run the four existing modules that cover the changed path. Expected: all tests pass, and no file changes.

   ```text
   python -m pytest tests/unit/mist/test_list_status.py tests/unit/mist/test_consumer_registry_usage.py tests/unit/api/test_auth.py tests/unit/api/test_session_security.py -q
   ```

3. Run the Ops platform gate. Expected: at least 390 collected tests and coverage of at least 56 percent.

   ```text
   python -m pytest --cov=src --cov-fail-under=56 -q
   ```

4. Run the symbol gate on the service file. Expected: `no module-level name changed`, exit code 0.

   ```text
   symbol-diff --base origin/main mist-ops-platform/src/shared/services/auth.py
   ```

5. Run the lint gate at the repository root. Expected: `All checks passed`.

   ```text
   python -m ruff check .
   ```

## Scenario 3: Check the changelog fragment

Run the STE gate on the fragment. Expected: a score of 80 or above.

```text
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4749-mist-identity-object-login.md
```

## Scenario 4: Check the change set

List the changed paths against `main`. Expected: exactly the six paths in plan.md, and no change to `CHANGELOG.md` or to an existing test module.

```text
git diff --name-only origin/main
```

## Scope of this record

This record includes no live check. A live Mist call would need a credential, and the brief forbids that step for this record.
