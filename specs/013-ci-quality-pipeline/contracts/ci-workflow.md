# Contract: GitHub Actions CI Workflow

**File**: `.github/workflows/ci.yml`
**Type**: GitHub Actions Workflow YAML
**Consumers**: GitHub Actions runners, PR status checks, branch protection

## Trigger Contract

```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
```

## Job Matrix Contract

The `quality-gates` job MUST run these checks in parallel:

| Matrix Entry | Command | Failure Blocks Merge |
|-------------|---------|---------------------|
| `ruff` | `ruff check . && ruff format --check .` | Yes |
| `mypy` | `mypy MistHelper.py` | Yes |
| `pytest` | `pytest --cov --cov-fail-under=70` | Yes |
| `bandit` | `bandit -r MistHelper.py -c pyproject.toml` | Yes |
| `pip-audit` | `pip-audit -r requirements.txt` | Yes |

## Status Check Names

Branch protection MUST reference these check names:
- `quality-gates (ruff)`
- `quality-gates (mypy)`
- `quality-gates (pytest)`
- `quality-gates (bandit)`
- `quality-gates (pip-audit)`

## Performance Contract

- Total wall-clock time for all parallel gates: **<= 10 minutes**
- Each individual gate: **<= 5 minutes** (timeout enforced in workflow)
- Runner: `ubuntu-latest`
- Python: `3.13`
