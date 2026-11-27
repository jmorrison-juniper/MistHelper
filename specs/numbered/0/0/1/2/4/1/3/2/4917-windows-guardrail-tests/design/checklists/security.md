# Security Checklist: Windows guardrail test failures

**Purpose**: Review the skip, lookup, and path changes for security effects before the pull request

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Skip Behavior

- [x] Each new skip names one platform condition or one privilege condition (FR-002, FR-006).
- [x] The symlink case re-raises every error except WinError 1314 (T005, FR-006).
- [x] The Windows skips cover only Bash cases and the symlink privilege case. The YAML-only and path cases still run on Windows (FR-004).
- [x] Ubuntu CI keeps the Bash and symlink proofs, because the shard runs `tests/guardrails` on `ubuntu-latest` (RC-13).

## Lookup and Execution

- [x] The fallback lookup searches one fixed directory, the interpreter folder, for the fixed name `uv` (T004).
- [x] The lookup runs no command. The existing export command runs with the resolved path, as it does today.
- [x] The guard keeps its failure when neither lookup finds `uv`. No silent pass is added (FR-005).
- [x] The pinned version matches `requirements-dev.txt` (RC-21).

## Path Handling

- [x] The Git root check compares `Path` objects and runs no new Git command (T006).
- [x] The analytics message prints POSIX paths of directories that the test creates under `tmp_path` or the repository (T007).
- [x] The symlink fixture stays under `tmp_path`, as the existing test already does.

## Secrets and Output

- [x] No token, password, or credential appears in a message, a skip reason, or a log line (FR-011, constitution Principle V).
- [x] The log lines for the new lookup and the symlink creation name only the action and the result (T004, T005).

## Suppressions and Dependencies

- [x] The change adds no `# nosec`, `# noqa`, or `# type: ignore` comment (T011).
- [x] The change adds no dependency and changes no lock file (FR-013).
- [x] The change adds no network call (plan, Constitution Check, Principle III).

## Notes

- All items are checked. No item needs an explanation.
- Caution: a Windows skip removes the local proof for the Bash cases. Ubuntu CI remains the proof, and the follow-up issue in T012 tracks the Windows gap.
