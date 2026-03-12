## Spec Conformance Checklist

**Linked Spec Issue**: #<!-- Issue number -->

### Acceptance Criteria
- [ ] All acceptance criteria from the linked Spec Issue are met
- [ ] Each criterion has a corresponding test or verification

### Quality
- [ ] Tests added or updated for all changed functionality
- [ ] Coverage meets or exceeds 70% threshold
- [ ] No new Ruff lint violations (`ruff check .`)
- [ ] Code formatted with Ruff (`ruff format --check .`)
- [ ] mypy passes (`mypy MistHelper.py`)

### Security
- [ ] No hardcoded secrets, tokens, or passwords
- [ ] Bandit passes with no new findings (`bandit -r MistHelper.py -c pyproject.toml`)
- [ ] pip-audit clean (`pip-audit -r requirements.txt`)
- [ ] Sensitive data handled via `.env` / environment variables only

### Deployment
- [ ] Dry-run verified locally (ran affected menu operations)
- [ ] `.env` changes documented in `deploy/.env.example` (if applicable)
- [ ] Container builds successfully (if Containerfile changed)

### Documentation
- [ ] README.md updated (if user-facing changes)
- [ ] Changelog entry added with version `YY.MM.DD.HH.MM` format
