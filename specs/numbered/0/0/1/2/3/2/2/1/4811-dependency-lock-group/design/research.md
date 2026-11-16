# Dependency group research

## Decision

Combine the requested updates in pull request #4806 if resolution and compatibility checks succeed.

## Rationale

All five current pull requests change shared dependency records.
None changes `uv.lock`, so their generated exports cannot satisfy the existing exact-export contract.
`uv lock --check` reproduces the stale-lock failure on the original #4806 head.
The repository already tests missing inputs, rejected versions, and stale exports.

Gunicorn 27 rejects malformed HTTP framing that earlier releases accepted.
Retain normal portal request behavior and check existing Gunicorn control-socket contracts.
Do not broaden this change into application repairs if compatibility fails.

Stevedore is a Bandit dependency rather than a direct application requirement.
Use a package-manager upgrade selector instead of adding an unnecessary direct declaration.
Ruff and UV are development tools. Their requested versions need a full lint check and exact export comparison.
The Paramiko stubs need the existing mypy selection and SSH compatibility checks.

## Alternatives considered

- Repair five branches separately. Rejected because each branch changes the same generated lock and export files.
- Update only the Paramiko stubs. Keep this option only if another update has an independent compatibility blocker.
- Hand-edit the lock or exports. Rejected because it breaks the package-manager source of truth.
- Reuse credentials from another checkout or tool. Rejected because no authorization establishes that source for this assignment.

## Preservation evidence

| Pull request | Local recovery reference | Original revision |
| --- | --- | --- |
| #4802 | `refs/recovery/issue4811/pr-4802` | `f6b174c9d9d1fbd39ddf2f410f0847e8003d1752` |
| #4803 | `refs/recovery/issue4811/pr-4803` | `079f31b68bee40fcbafc19d3ff013880a5476d42` |
| #4804 | `refs/recovery/issue4811/pr-4804` | `11dbd126ea2f93bdf380c360ec84653bef75d01a` |
| #4805 | `refs/recovery/issue4811/pr-4805` | `e7b42fdc8faab93401c26c464c0addec5e7020f7` |
| #4806 | `refs/recovery/issue4811/pr-4806` | `78dcf00086f4487c3f243dcafc7d7f3a8282890d` |

These references are local. Publish recovery references before replacing remote work when the coordinator permits publication.
No original pull request or issue can close before the merged replacement is verified on `main`.

## Environment findings

- Python 3.15.2 is available.
- The worktree has no `.venv`. The initial test probe reports `No module named pytest`.
- Podman responds and reports ARM64.
- The worktree has no `.env`, Mist token, or organization setting.
- All five inspected pull requests have no assignee and no ownership comment.
