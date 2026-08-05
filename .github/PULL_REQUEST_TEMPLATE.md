# Spec Conformance Checklist

**Linked Spec Issue**: #<!-- Issue number -->

## Acceptance Criteria
- [ ] All acceptance criteria from the linked Spec Issue are met
- [ ] Each criterion has a corresponding test or verification

## Quality
- [ ] Tests added or updated for all changed functionality
- [ ] Coverage meets or exceeds 80% threshold
- [ ] No new Ruff lint violations (`ruff check .`)
- [ ] Code formatted with Ruff (`ruff format --check .`)
- [ ] mypy passes (`mypy MistHelper.py`)

## Security
- [ ] No hardcoded secrets, tokens, or passwords
- [ ] Bandit passes with no new findings (`bandit -r MistHelper.py -c pyproject.toml`)
- [ ] pip-audit clean (`pip-audit -r requirements.txt`)
- [ ] Sensitive data handled via `.env` / environment variables only

## Deployment
- [ ] Dry-run verified locally (ran affected menu operations)
- [ ] `.env` changes documented in `deploy/.env.example` (if applicable)
- [ ] Container builds successfully (if Containerfile changed)

## UI / E2E Testing (if web UI changed)
- [ ] Playwright E2E tests added/updated for changed UI flows in `tests/e2e/`
- [ ] Stable `data-testid` attributes added for new interactive elements
- [ ] AI agent verified selectors via VS Code Browser Agent Tools
- [ ] Screenshots/traces captured for main UI flows (attached or in CI artifacts)

## Documentation
- [ ] README.md updated (if user-facing changes)
- [ ] Changelog entry added with version `YY.MM.DD.HH.MM` format
