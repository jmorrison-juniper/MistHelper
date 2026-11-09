# Local validation

Use the worktree environment. Do not run the bootstrap script.
If the environment is absent, restore the locked development dependencies without changing Git settings.

Run the dedicated checks:

```sh
.venv/bin/python -m pytest -q tests/unit/web_portal/verification_masking tests/e2e/web_portal/verification_masking --tracing retain-on-failure --output test-artifacts/verification-masking
```

The browser test serves the actual Operations script through Flask client dispatch.
It blocks nonlocal requests and replaces the operation executor.
No Mist session or real verification value is necessary.

Confirm the control type, required behavior, label association, ordinary text controls, and exact positional submission.
Keep the resulting commit local until the publication hold ends.
