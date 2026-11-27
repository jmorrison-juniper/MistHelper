# Security Requirements Quality Checklist: Mando pin conflict in the pip-audit gate

**Purpose**: Check that the change keeps the security gate intact.
**Created**: 2026-11-26
**Feature**: `spec.md`

## Suppression and Scanning

- [x] No `--ignore-vuln` flag is added (FR-008).
- [x] No `#nosec`, `# noqa`, or `# type: ignore` annotation is added.
- [x] The pip-audit command stays `pip-audit -r requirements.txt` (R-11).
- [x] The change does not narrow the CVE scan. The scan target stays `requirements.txt`.

## Supply Chain

- [x] No new package is added (`plan.md`, Dependencies).
- [x] The mando pin stays at 0.7.1. PyPI lists no vulnerability for that version (R-49).
- [x] The Dependabot rule limits minor and major updates for mando. Its effect on security updates is unverified (U-1). T-MERGE checks the next Dependabot pull requests.
- [x] The radon pin stays at 6.0.1. PyPI lists no vulnerability for that version (R-46).

## Secrets and Output

- [x] The record names no token value. It names only the account variable.
- [x] The guard logs use ASCII text and `%s` values (constitution Principle V).
- [x] The guard does not log the content of the configuration files.

## Process Safety

- [x] No merge occurs without the owner authorization (`spec.md`, Assumptions).
- [x] Closing pull request #4888 is reversible. The task list states the caution.
- [x] No branch is force-pushed (T-PR, step 6).
- [x] No file outside the change map is edited (`plan.md`, File-by-File Change Map).
