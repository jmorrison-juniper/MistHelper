# Validation: Juniper RMA prompt audit

Use the worktree environment.
If it is absent, run `python3 scripts/bootstrap_worktree.py`.

```text
.venv/bin/python -m misthelper_devtools.prompt_audit --menus 294,295,296,297,300,303,304 --json
.venv/bin/python -m pytest tests/unit/web_portal/test_portal_required_controls.py -q
.venv/bin/python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py -q
```

The audit must report ordered prompt counts of 2, 2, 3, 3, 2, 3, and 1.
The guard must examine both identifier choices.
Mutation cases must detect missing, extra, and misplaced dependent controls.
Browser tests must use synthetic responses.

Run Ruff and Black on the changed test module.
Run the documented test-quality procedure after the commit.
Record exact results in the pull request.
Remove the seven exemptions only after the audit and comparisons pass.

## Partial Validation on 2026-10-19

| Command | Actual result |
| --- | --- |
| `.venv/bin/python -m pytest tests/unit/web_portal/test_portal_required_controls.py -q` | 87 passed. |
| `.venv/bin/python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py -q` | 18 passed. |
| `.venv/bin/python -m ruff check tests/unit/web_portal/test_portal_required_controls.py` | `All checks passed!` |
| `.venv/bin/python -m black --check tests/unit/web_portal/test_portal_required_controls.py` | One file would remain unchanged. |
| `.venv/bin/python -m pytest tests/guardrails/test_process_folder_structure.py tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides -q` | 12 passed. |
| `.venv/bin/ste-linter --config .ste-linter.toml --min-score 80` with the seven feature Markdown paths | Exit 0. All seven files passed. |
| `.venv/bin/radon cc tests/unit/web_portal/test_portal_required_controls.py -j` through `complexity-gate --max 10` | Failed on two unchanged functions with complexity 18 and 14. |
| The same complexity check on the `HEAD` copy | The same two pre-existing violations. |

The new complexity blocks remain below 10.
The audit still reports zero prompts for all seven affected menus.
Seven exact audit assertions failed as expected against the old tool.
Those assertions remain a session artifact, not an active failing test.
The current branch keeps all seven exemptions.
No shared-tool pin, runtime code, browser test, or cloud state changed.
No completion pull request or merge occurred.
