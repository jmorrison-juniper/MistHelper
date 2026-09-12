# Contract: Release Workflow

**File**: `.github/workflows/release.yml`
**Type**: GitHub Actions Workflow YAML
**Consumers**: GitHub Releases, GHCR

## Trigger Contract

```yaml
on:
  push:
    tags: ['v*.*.*']
```

## Artifact Contract

On tag push, the workflow MUST produce:

| Artifact | Format | Destination | Naming |
|----------|--------|-------------|--------|
| Standalone bundle | `.zip` | GitHub Release attachment | `misthelper-{version}.zip` |
| Python wheel | `.whl` | GitHub Release attachment | Standard wheel naming |
| Python sdist | `.tar.gz` | GitHub Release attachment | Standard sdist naming |
| Container image | OCI | `ghcr.io/jmorrison-juniper/misthelper:{version}` | Tag = version |

## Standalone Bundle Contents

The zip MUST include:
- `MistHelper.py`
- `requirements.txt`
- `pyproject.toml`
- `README.md`
- `LICENSE`
- `web_portal/` (complete directory)
- `maps_manager.py`
- `wsgi.py`
- `__init__.py`

The zip MUST NOT include:
- `.git/`
- `tests/`
- `.github/`
- `.specify/`
- `data/`
- `.env`
- `__pycache__/`
- `*.pyc`

## Non-Trigger Contract

- Pushes to `main` without tags MUST NOT trigger this workflow
- PRs MUST NOT trigger this workflow
