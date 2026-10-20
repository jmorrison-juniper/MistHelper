# Quickstart: Explicit Portal Run Outcomes

## Prerequisites

Use the repository virtual environment created by `python3 scripts/bootstrap_worktree.py`.

## Validate

Run:

```sh
python -m pytest tests/unit/web_portal/test_portal_silent_completion.py
python -m pytest tests/e2e/web_portal/test_issue_4037_menu_93_output.py
python -m ruff check web_portal/services/operation.py tests/unit/web_portal/test_portal_silent_completion.py
python -m black --check web_portal/services/operation.py tests/unit/web_portal/test_portal_silent_completion.py
python -m py_compile web_portal/services/operation.py tests/unit/web_portal/test_portal_silent_completion.py
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
ste-linter --config .ste-linter.toml --min-score 80 \
  changelog.d/issue-3168-explicit-handler-outcomes.md \
  specs/numbered/0/0/1/0/0/1/3/3/3168-run-outcome-values/spec.md \
  specs/numbered/0/0/1/0/0/1/3/3/3168-run-outcome-values/plan.md \
  specs/numbered/0/0/1/0/0/1/3/3/3168-run-outcome-values/tasks.md \
  specs/numbered/0/0/1/0/0/1/3/3/3168-run-outcome-values/design/checklists/requirements.md \
  specs/numbered/0/0/1/0/0/1/3/3/3168-run-outcome-values/design/contracts/handler-outcome.md \
  specs/numbered/0/0/1/0/0/1/3/3/3168-run-outcome-values/design/data-model.md \
  specs/numbered/0/0/1/0/0/1/3/3/3168-run-outcome-values/design/quickstart.md \
  specs/numbered/0/0/1/0/0/1/3/3/3168-run-outcome-values/design/research.md
```

The unit test must prove that a migrated handler's returned outcome controls the run despite unrelated log wording. It must also prove that an unmigrated handler uses the marker fallback and logs its count.
