# Quickstart: CI/CD Quality Pipeline & Deployment Infrastructure

**Feature**: 013-ci-quality-pipeline

## Prerequisites

- Python 3.13+
- UV or pip
- Git
- Podman (for container deployment)
- GitHub CLI (`gh`) for workflow monitoring

## Local Development Setup

### 1. Install dev dependencies

```bash
# Using UV (preferred)
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

### 2. Install pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```

### 3. Run quality gates locally

```bash
# Lint
ruff check MistHelper.py
ruff format --check MistHelper.py

# Type check
mypy MistHelper.py

# Tests with coverage
pytest --cov --cov-fail-under=70

# Security scan
bandit -r MistHelper.py -c pyproject.toml

# Dependency audit
pip-audit -r requirements.txt
```

## CI Pipeline Usage

### Branch Protection Configuration

Configure these required status checks under **Settings > Branches > Branch protection rules** for `main`:

- `quality-gates (ruff)`
- `quality-gates (mypy)`
- `quality-gates (pytest)`
- `quality-gates (bandit)`
- `quality-gates (pip-audit)`

Enable **Require status checks to pass before merging** and **Require branches to be up to date before merging**.

### PR Workflow

1. Push changes to a feature branch
2. Open a PR targeting `main`
3. CI automatically runs all 5 quality gates in parallel
4. Fix any failures shown in PR checks
5. All green = merge-eligible

### Release Workflow

1. Merge PR to `main`
2. Tag a release: `git tag v1.0.0 && git push --tags`
3. Release workflow automatically builds and publishes:
   - Standalone zip
   - Python wheel + sdist
   - Container image to GHCR

## Deployment

### Option A: Systemd (standalone)

```bash
# Copy files
sudo cp deploy/misthelper.service /etc/systemd/system/
sudo cp .env /opt/misthelper/.env
sudo cp MistHelper.py /opt/misthelper/

# Create user and start
sudo useradd -r -s /usr/sbin/nologin misthelper
sudo systemctl daemon-reload
sudo systemctl enable --now misthelper
```

### Option B: Podman Quadlet (containerized)

```bash
# Copy Quadlet file
cp deploy/misthelper.container ~/.config/containers/systemd/
cp .env ~/.config/containers/systemd/

# Reload and start
systemctl --user daemon-reload
systemctl --user start misthelper
```

### Option C: Docker Compose

```bash
docker compose up -d
```

## Verification

```bash
# Check service status
systemctl status misthelper      # systemd
systemctl --user status misthelper  # Quadlet
podman ps                        # container

# Check CI status
gh run list --workflow=ci.yml --limit 5
```

## AI-Driven Browser Testing

### Browser Agent Requirements

- VS Code with browser agent tools enabled (Insiders or Stable with experimental setting)
- MistHelper web UI running locally (`python MistHelper.py` then select web portal option, or `gunicorn wsgi:app --bind 127.0.0.1:8055`)

### Workflow

1. Start the Gunicorn web UI locally
2. In VS Code, enable browser agent tools via settings
3. Ask the AI agent to open the local URL (e.g., `http://127.0.0.1:8055`)
4. The AI reads the DOM, interacts with elements, and validates behavior
5. Ask the AI to generate Playwright tests for the observed interactions
6. Save generated tests to `tests/e2e/` and commit

### Running E2E Tests Locally

```bash
# Install Playwright
pip install playwright
playwright install chromium

# Run E2E tests
pytest tests/e2e/ -v
```

E2E tests run automatically in CI via the `playwright` job in `.github/workflows/ci.yml`.
