# Implementation Plan: Mando pin conflict in the pip-audit gate

**Branch**: `fix/4896-mando-radon-pin-conflict` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification at `specs/numbered/0/0/1/2/4/0/4/1/4896-mando-radon-pin-conflict/spec.md`. The route uses base 5 with eight digits, as `.specify/scripts/powershell/spec-route.ps1` lines 7 and 17 define (R-39, R-54).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Hold mando at 0.7.1, the value on main. Add a Dependabot ignore rule for mando minor and major updates. Add guard cases to an existing guard module. Document the hold, and add one changelog fragment. The job `pip_audit` and its check name stay unchanged.

## Technical Context

- **Language/Version**: Python 3.15. The CI variable `PYTHON_VERSION` is `'3.15'` (`.github/workflows/ci.yml` line 77).
- **Primary Dependencies**: pip installs `requirements-dev.txt` (ci.yml line 483). The gate runs pip-audit 2.10.1 (`pyproject.toml` line 116). radon 6.0.1 (`pyproject.toml` line 118) requires mando. mando 0.7.1 is locked (`uv.lock` lines 1300-1301). PyYAML 6.0.4 is pinned (`requirements-dev.txt` line 356). No new package is added.
- **Storage**: None.
- **Testing**: pytest in `tests/guardrails/test_dependency_lock_file.py`, with the `packaging` library and PyYAML.
- **Target Platform**: GitHub Actions `ubuntu-latest` (ci.yml line 465) for the job. Windows 11 for local development.
- **Project Type**: CI configuration and one guard test module.
- **Performance Goals**: Not applicable. The guard reads three small files.
- **Constraints**: `tests/guardrails` holds 79 tracked entries (R-30). `.github` holds 14 entries (R-69), and `changelog.d` holds 335 (R-31). Edit existing files only in these folders.
- **Scale/Scope**: Four files change, and one record is added.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Principle or rule | Gate | Evidence in this plan | Result |
| - | - | - | - |
| I. Five-item rule | No new direct child under a parent with more than five children. | `tests/guardrails` has 79 entries (R-30). The change edits an existing module. `.github` is grandfathered (R-69). The change edits `dependabot.yml` in place. `changelog.d` holds 335 entries (R-31). The fragment is one required unique record. The route leaf is absent on main (R-42), so the record is its only child. | Pass, with recorded debt |
| II. Class-based, no wrappers | Logic lives in a named class. | The new checks are methods of the class `DependencyLock` (R-28). Test functions call those methods. | Pass |
| III. Safety first | No keyboard input, no destructive action, no secret. | The change reads files and asserts results. The negative fixtures use `tmp_path`. | Pass |
| IV. Full deployment pipeline | Local gates, commit, rebase, push, pull request, CI, squash merge, main build, revision check, deploy. | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Steps 10 and 11 run in T-MERGE, because `auto-merge.yml` dispatches `container-build.yml` after each merge (R-52, R-68). Step 12 stays with the owner (D-8). | Pass, with one recorded owner step |
| V. Observability | ASCII log output, no secret in a log. | New log messages use ASCII text and `%s` values. | Pass |
| VI. Inline comments | Each executable line has an inline comment. | T003 acceptance requires a comment on each new executable line. | Pass when T003 is verified |
| VII. Action logging | An `info` line before and a `debug` line after each file read. | T003 acceptance requires both lines around each read. | Pass when T003 is verified |
| Technology: mistapi | Each REST call uses a mistapi method. | The change calls no Mist REST endpoint. | Not applicable |
| Technology: Podman | Test containers join the compose group. | The change starts no container. | Not applicable |
| Technology: file paths | Use `pathlib.Path`. | T003 builds each path with `Path`. | Pass |
| Security findings | No suppression and no ignore flag. | FR-008. The change adds no `#nosec` comment. | Pass |
| Documentation | Update the document in the same change. | T004 updates `documentation/quality-gates.md`. | Pass |
| Release notes | One fragment per change. | T005 adds `changelog.d/issue-4896-mando-radon-pin-conflict.md`. Constitution line 409 (R-33) supersedes the internal-only rule in the changelog README (R-32). Decision D-6. | Pass |

For repository structure and generated files:

- The commit subject and the pull request title use the form `fix(ci): description`, which the title guard accepts.
- The change adds one record under `specs/numbered/` and one fragment under `changelog.d/`.
- The plan records the existing folder debt in Complexity Tracking.

For a feature that uses Juniper Mist Cloud: not applicable, because the change calls no Mist Cloud endpoint.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/0/4/1/4896-mando-radon-pin-conflict/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      dependency-pin-rule.md
    checklists/
      requirements.md
      security.md
```

### File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `.github/dependabot.yml` | Modify | Add an `ignore` block to the pip entry, which starts at line 3 (R-22). The block holds one rule for `mando` with `update-types` for minor and major updates (R-24). |
| `tests/guardrails/test_dependency_lock_file.py` | Modify | Add a range constant for radon 6.0.1, two methods on `DependencyLock`, and five test functions. |
| `documentation/quality-gates.md` | Modify | Add one paragraph below the job table. The paragraph states the hold, the source of the range, and the review trigger (FR-009). |
| `changelog.d/issue-4896-mando-radon-pin-conflict.md` | Add | One `###` heading and one `Fixed` bullet that names issue #4896. |
| `specs/numbered/0/0/1/2/4/0/4/1/4896-mando-radon-pin-conflict/` | Add | This record. |
| `requirements-dev.txt` | No change | Main already pins mando 0.7.1 (R-13). |
| `requirements.txt`, `pyproject.toml`, `uv.lock` | No change | The CVE scan target and the lock stay the same. |
| `.github/workflows/ci.yml` | No change | The job ID, the check name, the install line, and the audit command stay the same (FR-007, FR-008). |

No file is deleted.

### Design Decisions

Research section "Decisions" records D-1 to D-8, with the alternatives, the reason, and the risk for each.

### Contracts

`design/contracts/` holds one file, `dependency-pin-rule.md`. The file defines the pin rule, the Dependabot rule, and the result of each guard case.

### Dependencies

- No new package is added.
- The range check reads `requirements-dev.txt`. The range constant cites the radon 6.0.1 metadata (R-46, R-51).
- The Dependabot check reads `.github/dependabot.yml` through `yaml.safe_load`. PyYAML 6.0.4 is pinned in `requirements-dev.txt` (R-14).

### Risks and Mitigations

| Risk | Mitigation |
| - | - |
| A mando advisory above 0.8 is not proposed to Dependabot. | `requirements.txt` does not list mando, so pip-audit does not scan it (R-18). PyPI lists no vulnerability for mando 0.7.1 (R-49). The owner reviews the hold when radon changes. |
| radon stops receiving updates, so the conflict returns. | The range check fails for an unknown radon version (T003). A separate issue tracks a replacement. |
| The Dependabot ignore rule also blocks security updates for mando. | Unverified (research U-1). The owner checks the Dependabot pull requests after the merge. |
| The replacement pull request fails another check. | T-REMOTE-CI stops the merge. Each new failure gets its own issue. |
| The range constant becomes stale. | The range check fails when radon changes, so the constant must change with the pin. |

### Rollback

1. Revert the replacement commit on `main` with a new pull request.
2. Remove the `ignore` block from `.github/dependabot.yml` in that revert.
3. Reopen pull request #4888 only when the owner wants the Dependabot update. Reopened, it fails the same way until radon accepts mando 0.8.

### Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `tests/guardrails` holds 79 tracked entries (R-30). | The guard module already reads both requirements files. | A new module in that folder adds a direct child to a noncompliant parent. Remediation: a separate issue restructures `tests/guardrails`. |
| `changelog.d` holds 335 entries (R-31). | The fragment is one required unique record. | No other fragment path meets the README rule. Remediation: a separate issue. |
| `.github` holds more than five children (R-69). | The Dependabot file is an existing child, edited in place. | A new file adds a child to a noncompliant parent. Remediation: a separate issue. |
| Principle IV step 12 stays with the owner. | Deployment changes the running service, and the constitution calls for an approved image. | The agent holds no deployment authority in this record. Decision D-8 records the split. |
