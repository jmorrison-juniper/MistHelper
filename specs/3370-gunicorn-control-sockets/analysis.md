# Analysis: Distinct Gunicorn control sockets

## Requirement Coverage

| Requirement | Delivered evidence |
| - | - |
| FR-001 and FR-002 | The actual startup contract and image readings confirm both exact socket paths. |
| FR-003 | Both live control servers answer before and after every tested reload. Neither command disables control access. |
| FR-004 | The preservation contract checks all 15 other startup options. The source adds two options and two comments only. |
| FR-005 | The parser reports two active startup commands and two socket paths. Invalid or unreadable input fails. |
| FR-006 | The host tests cover both reload orders. The image proof sends four SIGHUP events under UID 1000. |
| FR-007 | The tests retain both master log sets and JSON identity readings. Both log sets contain zero control errors or collisions. |
| FR-008 | The proofs use temporary applications and owned processes. The compose proof has no production dependency or published host port. |

## Success Criteria

The focused suite passed all 152 cases with zero skips.
All 22 new cases ran.
The real process cases checked both masters after each SIGHUP.
The image proof checked four SIGHUP events and both `0600` sockets.
Cleanup verified two image masters, six image workers, and both socket removals.
The final resource lists contain zero owned containers, volumes, or networks.

The [implementation record](implementation.md) holds the commands, counts, and proof limits.
The [task record](tasks.md) separates local delivery from parent-controlled publication.

## Design Review

The repair adds no runtime class or wrapper.
The startup script retains its existing ports, workers, threads, timeouts, environment, entrypoints, and shutdown path.
Each master receives its own absolute socket path.
The image's `misthelper` account can write both paths.
The default socket mode stays `0600`.

The contract parses the active launch commands.
A comment that names a socket cannot satisfy the contract.
The guard rejects absent, disabled, repeated, relative, empty, shared, and normalized shared paths.
The input cases also reject missing, comment-only, repeated-master, and wrong-count scripts.

The readiness probe waits for both HTTP and control access.
It does not increase the original 10-second deadline.
The control probe uses the installed SDK protocol and closes each socket on every outcome.
The failure case proves descriptor closure when the socket is unavailable.

The process support uses an argument list, not a shell.
Each master receives an environment without inherited credentials.
Each master owns a separate process group.
The cleanup signals only owned process identifiers.
A failed graceful stop causes an explicit failure after bounded owned cleanup.

## Quality Review

The new helpers pass strict types, Ruff, Black, Bandit, docstring, and complexity checks.
Every new method meets the 25-line limit.
The complete new test module adds zero findings against the unchanged quality ratchet.
The two Python modules and the release note score 100 in the available writing check.
The checker cannot measure dictionary compliance because the worktree holds no dictionary.

The host runtime audit checked 105 packages with zero known vulnerabilities and zero skips.
The Linux arm64 runtime audit checked 107 packages with zero known vulnerabilities and zero skips.
It does not supply an advisory result for the Git-only development tool.
No dependency pin or quality exclusion changed.

## Scope and Publication

The feature owns ten reserved files.
It changes no shared SpecKit state, menu registry, browser test support, image recipe, database, or primary key.
The legacy branch hook refused the existing app-managed branch.
The five isolated feature records supply the file-only SpecKit stages.

No unresolved implementation defect remains in the local repair.
Publication still requires the parent's verified-main release after issue #3215.
The proof starts fake applications in an isolated image.
It does not start the complete production entrypoint or authorize a production restart.

## Local Refresh Review

The authorized refresh base is `0d1cfffbcdef3f1f66cb49b5abcfbbd3d90e0b95`.
The original `a542f9aae7568ac3d040da81557e2f5eabcaa23e` remains in a local preservation tag.
The rebased repair still changes only its ten reserved files.
The runtime difference remains two socket options and two comments.
The accepted output-default cleanup remains intact.

The repeated suite passed 293 cases, including all 22 required socket cases.
The additional 141 cases prove the current container output-default contracts.
The native image proof passed four SIGHUP events under UID 1000.
Both exact sockets retained their correct master identities and `0600` permissions.
Cleanup removed all owned masters, workers, sockets, containers, volumes, networks, and the image tag.

The current preflight validates six inputs and three guide procedures.
The full test-quality ratchet reports zero new findings across 1007 discovered files.
It retains 725 accepted findings and 48 configured exclusions.
The full Ruff, Black, configured mypy, and configured Bandit checks pass.
The new helper also passes the direct checks outside the test exclusions.

All evidence applies only to the immutable local refresh boundary.
The local-only commit comparison is not a fresh remote-base publication check.
No workflow, pull request, merge, deployment, or actual-main delivery result exists for this refresh.
The parent must grant publication after the actual verified issue #3215 result.
