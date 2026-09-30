# Spec Conformance Checklist

**Linked Spec Issue**: #3560

Closes #3560

## Summary

This pull request adds the organization WAN edge scorecard package.
The package builds gateway, DHCP pool, site, and organization summaries from
gateway statistics.

## Spec

- Spec: `specs/3560-wan-edge-scorecard/spec.md`
- Plan: `specs/3560-wan-edge-scorecard/plan.md`
- Tasks: `specs/3560-wan-edge-scorecard/tasks.md`
- Wiring manifest: `specs/3560-wan-edge-scorecard/wiring.md`

## Files

- `src/reports/wan_edge_scorecard/`
- `tests/unit/reports/wan_edge_scorecard/`
- `changelog.d/issue-3560-wan-edge-scorecard.md`
- `specs/3560-wan-edge-scorecard/`

## Deferred wiring

Menu registration is deferred to the integration pull request for this tier.
The exact menu, registry, documentation, and import changes are in
`specs/3560-wan-edge-scorecard/wiring.md`.

## Acceptance Criteria

- [x] Package-scope acceptance criteria from the linked Spec Issue are met.
- [x] Each non-deferred criterion has a corresponding test or verification.
- [x] Menu `--test` verification is deferred to the integration pull request because menu wiring is deferred.

## Quality

- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds 80% threshold. Package coverage is 96%.
- [x] New or changed guards state the measured count and prove one failing path.
- [x] No new Ruff lint violations.
- [x] Code formatted with Black.
- [x] mypy passes.

## Security

- [x] No hardcoded secrets, tokens, or passwords.
- [ ] Bandit passes with no new findings. Not run for this package-only change.
- [ ] pip-audit clean. Not run because dependencies did not change.
- [x] Sensitive data handled via `.env` or environment variables only.

## Deployment

- [x] Dry-run verified locally with unit tests for the operation seam.
- [x] `.env` changes documented in `deploy/.env.example` if applicable. Not applicable.
- [x] Container builds successfully if Containerfile changed. Not applicable.

## UI / E2E Testing

- [x] Playwright E2E tests added or updated for changed UI flows. Not applicable.
- [x] Stable `data-testid` attributes added for new interactive elements. Not applicable.
- [x] AI agent verified selectors via VS Code Browser Agent Tools. Not applicable.
- [x] Screenshots or traces captured for main UI flows. Not applicable.

## Documentation

- [ ] README.md updated. Deferred to the integration pull request.
- [x] Release note added as one new fragment under `changelog.d/`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Local validation

- `python -m pytest tests\unit\reports\wan_edge_scorecard -q --timeout=120`: 18 passed.
- `python -m pytest tests\unit\reports\wan_edge_scorecard -q --timeout=120 --cov=src.reports.wan_edge_scorecard --cov-report=term-missing`: 18 passed, 96% coverage.
- `python -m py_compile src\reports\wan_edge_scorecard\__init__.py src\reports\wan_edge_scorecard\client.py src\reports\wan_edge_scorecard\models.py src\reports\wan_edge_scorecard\scorecard.py src\reports\wan_edge_scorecard\scoring.py`: passed.
- `python -m py_compile MistHelper.py`: passed.
- `python -m ruff check MistHelper.py src\reports\wan_edge_scorecard tests\unit\reports\wan_edge_scorecard`: passed.
- `python -m black --check MistHelper.py src\reports\wan_edge_scorecard tests\unit\reports\wan_edge_scorecard`: passed.
- `python -m mypy src\reports\wan_edge_scorecard --config-file pyproject.toml`: passed.
- `python -m pydocstyle src\reports\wan_edge_scorecard`: passed.
- `python -m vulture src\reports\wan_edge_scorecard --min-confidence 70`: passed.
- `python -m interrogate -v src\reports\wan_edge_scorecard`: 100 percent.
- `python -m radon cc src\reports\wan_edge_scorecard -j | complexity-gate --max 10`: passed.
- `test-quality-analyzer --gate --config .github\test-quality-config.toml --baseline .github\test-quality-baseline.json --changed-from origin/main`: passed, 0 new findings.
