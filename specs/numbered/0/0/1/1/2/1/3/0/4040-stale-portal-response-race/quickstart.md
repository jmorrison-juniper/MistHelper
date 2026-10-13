# Quickstart: Stale Portal Response Ownership

## Prerequisites

- Build the worktree environment with `python3 scripts/bootstrap_worktree.py`.
- Activate the environment with `source .venv/bin/activate`.
- Confirm that Chromium is installed by the bootstrap command.

## Validate the Browser Flow

Run:

```sh
python -m pytest tests/e2e/web_portal/test_web_interactivity_quickstart.py -q
```

The test must delay the menu 241 response, select menu 242, and release the delayed response. It must confirm that the title remains `Menu 242` and `#cliOnlyPanel` stays hidden.

The test must also confirm that a delayed failure does not show a menu 241 error and that a current menu 241 response still shows its SSH-only warning.

This validation uses mocked browser responses. It does not call Mist or change a network device.
