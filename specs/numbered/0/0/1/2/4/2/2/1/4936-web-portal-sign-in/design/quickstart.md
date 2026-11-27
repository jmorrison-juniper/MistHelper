# Quickstart: Browser sign-in with 2FA for the web portal

This page gives the exact steps to reproduce the issue, and the exact commands that verify the change. Run each command from the repository root with the `.venv` environment active. Each result in "Expected" comes from the source on `main`. Nothing in this record ran these steps.

## Reproduce the current behavior

1. Remove `MIST_APITOKEN` and `MIST_API_TOKEN` from `.env`, then start the web portal with `python MistHelper.py --web-portal`.
   - Expected: The portal starts on port 8055 and shows no sign-in form. The page text says the portal page has no sign-in form (R-47).
2. Open `http://127.0.0.1:8055/auth/signin` in a browser.
   - Expected: HTTP 404. No route exists for this path on `main` (R-73, R-19).
3. Start the portal in a container with `podman compose up -d`, and read the container log.
   - Expected: The log warning starts with `WSGI: API auth failed (` and ends with `) - maps/execution disabled`. It appears when the startup login fails with no token (R-01). The text between them is the exception (`wsgi.py` line 59 on `main`).
4. Start the portal with `python MistHelper.py --login --web-portal` and answer the terminal prompts.
   - Expected: The terminal asks for the cloud, the email, the password, and the `Enter 2FA code:` prompt (R-31). The browser page still has no sign-in form.

## Verify the change

Run these commands in order after the implementation tasks finish.

```powershell
python -m py_compile wsgi.py web_portal/app.py src/mist/access/auth/browser/routes.py src/mist/access/auth/browser/cloud/login.py src/mist/access/auth/browser/state/holder.py src/mist/access/auth/browser/state/pending.py src/mist/access/auth/browser/state/lifetime.py src/mist/access/auth/browser/state/outcome.py src/interfaces/portals/upgrade_portal/app/routes/auth.py
python -m pytest tests/unit/marvis/mist/access/auth/browser -q
python -m pytest tests/contract/upgrade_portal/test_auth.py tests/unit/upgrade_portal/test_auth.py tests/unit/upgrade_portal/test_identity.py -q
python -m pytest tests/e2e/web_portal/test_portal_smoke.py -q
python -m pytest tests/guardrails/test_hardware_shell_lock_docs.py -q
python -m pytest tests/unit/ex_hardware_inventory/scope -q
python -c "import src.mist.access.auth.browser.routes"
```

Expected results:

- Each `py_compile` command prints no output.
- The browser test folder reports 34 tests. The two extended modules add three tests, and the commands that cover them report those counts.
- The capture contract tests pass with the same count as before the change, plus one new test.
- The documentation guard passes.
- The scope tests pass without any change to their expected output.
- The import command prints no output.

## Check the page by hand

1. Start the portal with no token: `python MistHelper.py --web-portal`.
2. Open `http://127.0.0.1:8055/auth/signin`.
   - Expected: The sign-in form shows the email field, the password field, and the cloud choice. The inputs carry the `data-testid` values `sign-in-email`, `sign-in-password`, and `sign-in-cloud`.
3. Submit a wrong password with a test account.
   - Expected: The page shows the `bad_credentials` sentence. The navigation still shows "Sign in".
4. Submit a correct password for an account with 2FA, then a correct code.
   - Expected: The 2FA step shows after the password step. After the code, the dashboard shows the account name.
5. Open "Multi Site", then preview the action "Collect EX hardware inventory".
   - Expected: The preview shows `Credential:`, `Scope:`, and `Organizations in scope:` lines that match the account (R-36).

Warning: The steps above use a real Mist account. Use a test account and a test organization. Do not start a container that publishes port 8055 on the production stack (copilot-instructions.md, containers and ports).

## Live check (owner)

The owner runs the live MSP check that issue #4925 tracks. The result is recorded in that issue, not in this record. The 2FA path with a live account remains unverified (U-1).

## Remove test resources and stop the portal

- Remove each test container whose name starts with `misthelper-tmp-issue4936-`. Remove its volume and network by exact name.
- Stop the local portal process with `Stop-Process -Id` and the process ID that the terminal shows.
