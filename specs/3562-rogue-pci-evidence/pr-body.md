# Spec Conformance Checklist

**Linked Spec Issue**: #3562

Closes #3562

## Summary

This draft pull request adds the menu 282 rogue and PCI evidence pack package. Menu wiring is deferred to the integration pull request through `specs/3562-rogue-pci-evidence/wiring.md`.

This branch is a package-only precursor. The operation is not integration-complete until the integration pull request applies menu registration, primary key registration, README updates, and generated references.

## Files changed

- `src/mist/intelligence/reports/rogue_pci_evidence/`
- `tests/unit/reports/rogue_pci_evidence/`
- `specs/3562-rogue-pci-evidence/`
- `changelog.d/issue-3562-rogue-pci-evidence.md`

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met in package tests or deferred wiring.
- [x] Each criterion has a corresponding test or verification.

## Quality

- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds 80% threshold.
- [x] New or changed guards state the measured count and prove one failing path.
- [x] No new Ruff lint violations for the changed package and tests.
- [x] Code formatted with Black for the changed package and tests.
- [x] mypy passes for the changed package.

## Security

- [x] No hardcoded secrets, tokens, or passwords.
- [x] Bandit passed for this scoped package change.
- [x] pip-audit is not run locally for this scoped package change.
- [x] Sensitive data is handled through existing environment and session helpers only.

## Deployment

- [x] Dry-run verified locally through no-network unit tests.
- [x] `.env` changes are not applicable.
- [x] Container changes are not applicable.

## UI / E2E Testing

- [x] Web UI changes are not applicable.

## Documentation

- [x] README.md update is deferred to the integration pull request.
- [x] Release note added as one new fragment under `changelog.d/`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Local gate results

- `py_compile`: passed.
- `ruff check src\mist\intelligence\reports\rogue_pci_evidence tests\unit\reports\rogue_pci_evidence`: passed.
- `black --check src\mist\intelligence\reports\rogue_pci_evidence tests\unit\reports\rogue_pci_evidence`: passed.
- `mypy src\mist\intelligence\reports\rogue_pci_evidence --config-file pyproject.toml`: passed.
- `pydocstyle src\mist\intelligence\reports\rogue_pci_evidence`: passed.
- `pytest tests\unit\reports\rogue_pci_evidence -q --timeout=120`: 12 passed.
- `pytest tests\unit\reports\rogue_pci_evidence -q --timeout=120 --cov=src\mist\intelligence\reports\rogue_pci_evidence --cov-report=term --cov-fail-under=80`: 12 passed, 85.96 percent coverage.
- `vulture src\mist\intelligence\reports\rogue_pci_evidence --min-confidence 70`: passed.
- `interrogate -v src\mist\intelligence\reports\rogue_pci_evidence`: 100.0 percent.
- `bandit -c pyproject.toml -r src\mist\intelligence\reports\rogue_pci_evidence -q`: passed.
- `radon cc src\mist\intelligence\reports\rogue_pci_evidence -j | complexity-gate --max 10`: passed.
- `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main`: passed.
- `pytest tests\integration\test_mistapi_sdk_compatibility.py -q --timeout=120`: 8 passed, checked 488 Mist SDK call signatures.
- `pytest tests\unit\web_portal\test_output_scan_runtime_files.py -q --timeout=120`: 27 passed.

## CI status confirmation

- The previous CI run failed `Radon (complexity)` and `Test quality ratchet (gate)`.
- The local replacement gates now pass. A new CI run must confirm the pushed commit.
- This pull request stays draft until the new CI run reports every required check green.
- The `auto-merge` label must not be added until every required check, including CodeQL, reports green.

## Rollback plan

- Revert this package-only pull request to remove the new package, tests, specification artifacts, and release note.
- No Mist cloud rollback is required because the operation is read-only and not wired into the menu yet.

## Request cost evidence

- `test_site_settings_uses_one_pacer_call_per_site` proves one pacer call and one `getSiteSetting` call for each site.

## Deferred wiring

The integration pull request must apply `specs/3562-rogue-pci-evidence/wiring.md` to:

- register menu 282 in `MistHelper.py`,
- register menu 282 in `src/foundation/support/utils/operation_registry.py`,
- add primary key strategy entries,
- update generated menu references,
- update README operation counts and menu documentation.
