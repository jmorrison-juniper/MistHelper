# Implementation Plan: Release Publication

**Branch**: `release/4756-release-publication` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric record route `specs\numbered\0\0\1\2\3\0\1\1\4756-release-publication`. The route digits 0, 0, 1, 2, 3, 0, 1, 1 equal 4756 in base 5. The route width 8 and base 5 appear in `.specify/scripts/powershell/spec-route.ps1` at lines 7 and 17 (RC-52).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`. Keep five children or fewer at every level.

## Summary

Collect the 334 fragments on `main` into one release section of `CHANGELOG.md`. Merge that change through one serial merge slot. The owner then creates the release tag, verifies the assets and the container image, and sets the release text. The agent creates no tag and no release.

## Technical Context

**Language/Version**: Python 3.15 or newer. `pyproject.toml` requires `>=3.15` at line 23 (RC-41). This release changes no Python code.

**Primary Dependencies**: git, the GitHub CLI `gh`, pytest for the existing guard tests, and Podman for the owner image checks. The operator steps use `podman image inspect` for the revision label (RC-50).

**Storage**: `CHANGELOG.md` at 527,193 bytes (RC-06). `changelog.d/` holds 334 fragments at 83,416 bytes, excluding `README.md` (RC-15).

**Testing**: Existing guard tests TEST-1 to TEST-3, a one-time reconciliation TEST-4, and owner checks TEST-5. CI runs the guard tests in the shard job, because the shard paths include `tests/contract` and `tests/guardrails` (RC-33 and RC-34).

**Target Platform**: The implementer runs local gates on Windows 11 (RC-65). The release workflow runs on `ubuntu-latest` (RC-24).

**Project Type**: Command-line tool release with a container image.

**Performance Goals**: None. The release changes no runtime behavior.

**Constraints**: 15 required checks, strict up-to-date branches, and linear history (RC-22). One serial merge slot (RC-45). Owner-only publication (D-8).

**Scale/Scope**: 334 fragments, 9 of them added since the last release (RC-16). One release section, one tag, three assets, and two container tags.

## Constitution Check

Gate result: pass. One scope note applies to Principle IV step 12, which covers deployment and stays outside this issue.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule (RC-62, line 38) | Pass | The release adds no direct child. `changelog.d/` falls from 334 children to one child, `README.md`. The folder debt appears under Complexity Tracking. |
| II. Class-based architecture (RC-62, line 91) | Pass | The release changes no code. |
| III. Safety-first (RC-62, line 113) | Pass | The one-time collection reads fragments. It writes only under `test-artifacts/`. |
| IV. Full deployment pipeline (RC-63, lines 166 to 171) | Pass with scope note | Local gates, pull request, CI, squash merge, main build, and revision check apply. Step 12, deployment, is outside this issue. |
| V. Observability (RC-62, line 182) | Pass | No code is committed. |
| VI. Inline comments (RC-62, line 204) | Pass | No code is committed. |
| VII. Action logging (RC-62, line 235) | Pass | No code is committed. |
| Technology: Python 3.15 (RC-41) | Pass | No Python change. |
| Technology: mistapi (RC-64, line 274) | Not applicable | The release makes no Mist API call. |
| Technology: Podman (RC-64, line 300) | Pass | The owner image checks use Podman. The agent starts no container. |
| Technology: Zscaler (RC-48, line 334) | Pass | Image builds run in CI. The agent pushes no image. |
| Testing: Windows local development (RC-65, line 363) | Pass | Local gates run on Windows 11 with the worktree environment. |
| Data directory (RC-61, RC-46) | Pass | No product output is written. Generated evidence goes to `test-artifacts/`, which Git ignores. |
| Version format (RC-47, line 406) | Pass | The release stamp uses `YY.MM.DD.HH.MM` in UTC. |
| Release notes (RC-44, lines 67 to 72) | Pass | The release coordinator writes the release section. The fragments leave `changelog.d/` in the same release. |
| Specifications (AGENTS, RC-49) | Pass | This change touches more than three files, so a record is required. |

## Architecture

```text
release branch from origin/main
  -> collect every fragment into one release section in CHANGELOG.md
  -> delete the collected fragments and keep README.md
  -> run local gates (TEST-1 to TEST-4)
  -> release pull request with 15 required checks
  -> serial merge (orchestrator authorizes)
  -> merge-triggered container build (RC-31 and RC-30)
  -> owner tags the release merge commit (OWN-001)
  -> release workflow publishes assets and the image (RC-23 to RC-28)
  -> owner verifies assets, digests, and revision label (OWN-002 to OWN-004)
  -> owner sets release title and body (OWN-005)
```

## File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `CHANGELOG.md` | Modify | Insert the release section after the blank line at line 14. The `## [Unreleased]` heading stays at line 13 (RC-09). Lines 1 to 14 and all older sections stay unchanged. |
| `changelog.d/2026-10-03-multisite-child-failure-accounting.md` | Delete | Collected fragment. Dated fragment. |
| `changelog.d/2026-10-04-agent-instructions.md` | Delete | Collected fragment. Dated fragment. |
| `changelog.d/2026-10-07-documentation-identifier-redaction.md` | Delete | Collected fragment. Dated fragment. |
| `changelog.d/issue-4869-speckit-1-4-3.md` | Delete | Collected fragment. Added after the last release (RC-16). |
| `changelog.d/issue-4873-routed-core-port.md` | Delete | Collected fragment. Added after the last release (RC-16). |
| `changelog.d/issue-4882-speckit-gitignore.md` | Delete | Collected fragment. Added after the last release (RC-16). |
| `changelog.d/issue-4912-observium-init.md` | Delete | Collected fragment. Added after the last release (RC-16). |
| `changelog.d/issue-4916-readme-lean.md` | Delete | Collected fragment. Added after the last release (RC-16). |
| `changelog.d/issue-4920-ex-hardware-inventory-csv.md` | Delete | Collected fragment. Added after the last release (RC-16). |
| `changelog.d/issue-4934-mist-netcool-runbook.md` | Delete | Collected fragment. Added after the last release (RC-16). |
| `changelog.d/issue-4938-hardware-shell-lock.md` | Delete | Collected fragment. Added after the last release (RC-16). |
| `changelog.d/pr-4806.md` | Delete | Collected fragment. Added after the last release (RC-16). |
| The other 322 `changelog.d/*.md` fragments | Delete | Collected fragments. The complete list comes from quickstart Scenario 1 at branch time. The count at `f03c6c9` is 334 (RC-15). |
| `changelog.d/README.md` | Keep | Policy file. The release coordinator keeps it (RC-44). |
| `test-artifacts/release-4756/` | Create, not committed | Holds the section text, the commit message, the pull request body, and the reconciliation output. Git ignores this folder (RC-61). |

No other path changes. The plan does not touch `pyproject.toml`, `Containerfile`, workflow files, `README.md`, or the documentation folder.

## Dependencies

- A git worktree for the release branch (AGENTS line 198, RC-49).
- Python 3.15.2 and `uv`, created by the bootstrap command in `.github/copilot-instructions.md` lines 27 to 30 (RC-67).
- The GitHub CLI. The local version is `gh` 2.103.3.
- pytest, installed by the bootstrap.
- No new package and no dependency pin change.

## Verification Approach

- Local gates: the Tests row of the local gates table (RC-68) runs TEST-1 to TEST-3. The rows for Compile, Lint, Format, Types, and Complexity check Python files, and this release changes no Python file.
- Reconciliation: TEST-4 compares the fragment inventory, the section entry count, the verbatim text, and the changed paths.
- Remote checks: the 15 required checks on the release pull request (RC-22).
- Owner checks: TEST-5 uses read-only `git`, `gh`, and `podman` commands. The local gates table has no row for tags, releases, or images. Quickstart Scenarios 11 to 15 hold these commands.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `changelog.d/` holds 334 direct children (existing debt, RC-15) | Each fragment is a unique process record, which the constitution allows (RC-62, Principle I). | Keeping the fragments leaves the release notes outside `CHANGELOG.md`. The owner acceptance criteria reject that result. Remediation: T004 to T006 remove the children, which a separate remediation action tracks. |

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| A fragment merges after the inventory. | Repeat T004 to T007 on a rebased branch before T-MERGE (FR-009). |
| PR 4208 merges before T-PR. | Its fragment joins the collection. Recount before the branch opens. |
| A copied entry holds a relative link that breaks at the root. | Rewrite the link to resolve from the root. TEST-2 proves each relative link resolves (RC-37). |
| The merge starts a container build with an automatic stamp, and that build moves `latest` (RC-30 and RC-31). | The owner records both builds. The release build moves `latest` last. A separate issue tracks the workflow change (D-11). |
| `Closes #4756` closes the issue at merge (RC-32). | The summary comment lists OWN-001 to OWN-005 as open. |
| The release body exceeds the size limit (RC-39). | The summary form is complete. The owner keeps it. |
| The owner tags the wrong commit. | OWN-001 compares the peeled tag commit with the release merge commit. |
| The package version `2.1.0` differs from the stamp (RC-41). | Accepted by D-5. The owner records the observed image version label (OWN-004). |
| The image version label reads `2.1.0` (RC-42). | Recorded as observed evidence. The cause is named in the owner report. Unverified: U-3. |
| A pull through the corporate proxy fails. | The owner records the failure. The agent does not push an image (D-10). |
| Remote evidence changes before the branch opens. | Repeat quickstart Scenarios 1 and 2, then update the research rows. |

## Rollback Steps

Warning: deleting a published GitHub release removes its assets. Do not delete a release before the owner confirms the cause.

Caution: a pushed release tag starts the release workflow. Remove the remote tag only before the workflow finishes. The same commit can receive the tag again.

1. Before the tag push, revert the release merge commit with a new pull request. The revert restores the fragments and the old `CHANGELOG.md`. The revert needs the same required checks.
2. After the tag push and before the workflow finishes, delete the remote tag with `git push origin --delete` and the tag name. The release tag can be created again on the same commit.
3. After publication, edit the release title or body. Do not delete the release unless the owner confirms that the assets are wrong.
4. For the container image, a new build from an older commit moves `latest` back. The owner runs that build through CI, not from a local push. GHCR version deletion has a restore window of 30 days (`05-managed/01-ghcr-package-identity-and-restoration.md` lines 169 to 170). This plan does not delete a version.
