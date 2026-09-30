# Wiring Manifest: PSK Hygiene Report

**Issue**: #3555
**Branch**: `feat/3555-psk-hygiene-report`
**Spec Directory**: `specs/3555-psk-hygiene-report/`
**Status**: Implementation validated

## 1. Issue Claim

- Issue #3555 owns this feature.
- The branch already exists and is checked out.
- No branch hook ran during this specify step.

## 2. Branch Contract

- Branch name: `feat/3555-psk-hygiene-report`.
- Target branch: `main`.
- The branch must rebase on `origin/main` before push.

## 3. Scope Boundary

- The feature adds menu 274 for a PSK hygiene report.
- The report reads PSK data and organization WLAN SSIDs.
- Site-level WLANs are outside scope.
- Passphrase values are outside output and log scope.

## 4. Feature Artifacts

- `specs/3555-psk-hygiene-report/spec.md`
- `specs/3555-psk-hygiene-report/checklists/requirements.md`
- `specs/3555-psk-hygiene-report/wiring.md`
- `changelog.d/issue-3555-psk-hygiene-report.md` must be added during implementation.

## 5. Hot File Check

- `MistHelper.py` is a hot file.
- Any implementation that edits it must check for open pull requests that also edit it.
- If another active PR owns the file, the implementer must stop or record a handoff.

## 6. Overlap Check

- Before implementation, compare planned files with open pull request files.
- Do not edit files that another active feature owns unless a handoff is recorded.
- Keep unrelated files out of the feature manifest.

## 7. Data and Output Contract

- Runtime report output must go under `data/`.
- The CSV file name must be `PskHygiene.csv`.
- The CSV must not contain `passphrase` or `old_passphrase` values.
- Logs and console output must not contain `passphrase` or `old_passphrase` values.

## 8. Test and Gate Contract

- The operation must pass a `--test` run with no prompt.
- Tests must prove each finding count and CSV finding.
- Tests must prove secret values do not appear in logs or output files.
- Local gates that apply to changed files must run before commit.

## 9. Release Note Contract

- Add one release note fragment at `changelog.d/issue-3555-psk-hygiene-report.md` during implementation.
- Do not edit `CHANGELOG.md` on the feature branch.

## 10. Deployment Contract

- Stage only feature-owned files.
- Commit with the repository release message format.
- Push the rebased branch.
- Open a pull request that closes #3555.
- Wait for required checks before merge.

## 11. Reviewer Evidence

- Reviewer can open the CSV produced by a test run and see all required columns.
- Reviewer can compare console counts to CSV findings.
- Reviewer can inspect logs and output files for secret absence.
- Reviewer can confirm this manifest and the release note fragment exist before release.

## 12. Local Validation Evidence

- `python -m py_compile` passed for all new PSK hygiene source and test Python files.
- `python -m ruff check src\reports\psk_hygiene tests\unit\reports\psk_hygiene` passed.
- `python -m black --check src\reports\psk_hygiene tests\unit\reports\psk_hygiene` passed.
- `python -m mypy src\reports\psk_hygiene --config-file pyproject.toml` passed.
- `python -m pydocstyle src\reports\psk_hygiene` passed.
- `python -m pytest tests\unit\reports\psk_hygiene -q --timeout=120` passed with 23 tests.
- The validation proves passphrase and old passphrase values stay out of rows, logs, and console output.
- Menu wiring stays deferred to the integration pull request.
