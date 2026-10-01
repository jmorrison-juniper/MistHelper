# Analysis: Remove unused output defaults

## Result

The local repair matches option 2 from [issue #3314](https://github.com/jmorrison-juniper/MistHelper/issues/3314).
The product diff contains three declaration deletions and one sentence replacement.
CSV remains the default.
Explicit SQLite selection remains supported.
Compose, readiness, session credentials, isolation, and restart behavior remain unchanged.

The analysis found two defects in the new test helpers.
Both defects are repaired and have direct failure-path tests.
No product defect remains within this repair.
The final writing checks pass.
The local commit remains pending at this analysis revision.
Publication requires the parent's separate verified-base grant.

## Artifact consistency

The [specification](spec.md), [plan](plan.md), [tasks](tasks.md), and [validation record](validation.md) describe the same option-2 repair.
All 15 functional requirements and seven success criteria have task coverage.
The feature owns exactly 15 paths.
The test package and feature directory each contain five files.
No shared feature state, existing test, dependency pin, schema, primary key, or quality setting changed.

The initial specification and planning instructions describe their historical phases.
They do not grant publication permission.
The validation record separates historical worker evidence from final local corrections.
The changed-scope ratchet requires a committed `HEAD`.
Its post-commit result must remain outside the checkout.
The local commit must not be amended to add that result.

## Resolved implementation findings

| ID | Finding | Repair | Direct proof |
| --- | --- | --- | --- |
| I1 | Text reads normalized newline bytes before hashing. | Contract and original-source reads now use raw bytes and explicit UTF-8 decoding. | CRLF mutations fail both protected-source guards. Altered newline bytes fail original replay for all six inputs. |
| I2 | A failed process launch left its output handle open. | `OwnedProcess.__enter__` uses `ExitStack`. It transfers cleanup ownership only after `Popen` succeeds. | Synthetic `OSError` and `ValueError` launch failures leave the capture handle closed and no application record. |

The final original-source replay uses no old Git object.
It restores only the removed declarations and the replaced sentence.
Each original copy must match its recorded raw SHA-256 value.
The tests prohibit Git subprocess calls during replay.
A changed original source raises an explicit error.
No fallback weakens the original-byte proof.

The earlier quality ratchet also found two weak assertions.
The final assertions require a real process, a positive PID, the exact SIGKILL result, and a closed capture handle.
The final ratchet reports no new finding.
No suppression or baseline change hides these repairs.

## Requirement coverage

| Requirement or criterion | Tasks | Evidence |
| --- | --- | --- |
| FR-001, FR-002, SC-001, SC-004 | T022-T025, T029-T031 | Raw-byte comparison confirms only the three deletions and the explicit SQLite instruction. Both image files are identical. |
| FR-003, FR-004, SC-002 | T009, T026, T028, T039 | All 15 environment and flag combinations use the real parser, runtime selection, and local writers. Both records remain intact. |
| FR-005, FR-006 | T003, T005, T008, T032-T033 | Protected sources match the original bytes. Both CRLF mutations fail. All 23 readiness outcomes preserve exact checks and responses. |
| FR-007, FR-008, FR-010, SC-005 | T006, T011-T016, T019, T034-T037 | Actual Bash preserves invocation, credentials, markers, PID treatment, signals, and restart controls. Tests use synthetic values and owned paths. |
| FR-009, SC-003 | T005, T007-T008, T017-T020, T031, T038 | Original success decision rejects four of six inputs. Live green rejects none. All 14 required negative cases and additional cases pass. |
| FR-011 | T023-T025, T027, T047-T049 | Both owned arm64 image builds passed. Their environment metadata contains no output declaration. Cleanup completed without a container start. |
| FR-012, SC-006 | T039-T046, T052-T054 | Configured local gates pass. Helper coverage has a nonzero denominator. Capability limits and post-commit evidence remain explicit. |
| FR-013, SC-007 | T001, T050-T054 | All five named phase records have unique paths. Final local completion remains separate from publication. |
| FR-014 | T046, T052 | The writing guide applies. Heuristic STE checks pass. Dictionary-backed scoring remains unavailable. |
| FR-015 | T050, T053-T054 | No push, pull request, merge, workflow, or deployment occurred. The initial base and observed PR state grant no permission. |

Planned requirement coverage is 22 of 22.
No task lacks an associated requirement.
The local commit and its post-commit checks remain pending until their operations succeed.

## Final measured evidence

The final expanded focused run passed **342 tests** in 57.61 seconds.
It has zero failures and zero skips.
It includes 114 new contract cases and 27 new session cases.
The existing container, image, readiness, environment, and export tests remain unchanged.

The same guard still reports original red with six checked inputs and four rejected inputs.
The live green reports six checked inputs and zero rejected inputs.
The direct shell parser rejects malformed source with status 2.
The explicit unsupported `polyglot` flag retains parser status 2.
All 15 actual export cases preserve both records and exclusive local selection.
Six healthy and 17 failed readiness cases retain their exact responses.

| Helper | Covered lines / lines | Covered branches / branches | Missing lines or arcs |
| --- | ---: | ---: | --- |
| `contract.py` | 166 / 166 | 44 / 44 | None |
| `session.py` | 172 / 172 | 22 / 22 | None |
| Total | 338 / 338 | 66 / 66 | None |

The combined helper coverage is **404 / 404**, or 100 percent.
The floor remains 90 percent.
This supplemental report does not establish the combined repository source coverage gate.
The final structure check measured 61 methods.
The maximum method length is 25 lines.
The maximum parameter count is five.

Full configured Ruff and Black pass.
Black checked 2,005 files.
The exact CI mypy scope passes for 663 source files.
That scope excludes the new tests.
Configured all-severity Bandit and both separator samples pass.
The full quality ratchet checks 994 files and 725 findings.
It reports zero new findings and zero parse errors.
Its unchanged SDK predicate excludes 48 files.

The strict hashed runtime audit measures 105 dependencies and zero known vulnerabilities.
It ignores no advisory.
It does not audit the Git-sourced development tools.
The normal macOS pip resolver failure remains recorded separately.

Both local builds produced the same arm64 image.
Both image tags are removed.
The final inventory contains no owned image tag, container, volume, or network.
No production port, stack, datastore, or unrelated image tag changed.

## Governance context and capability limits

The read-only agent reported five conflicts with older general constitution text.
These concern parent child counts, blanket comments, image builds, commit subjects, and branch names.
The current task explicitly reserves unique files and requires a local image build and a Conventional Commit.
The [authoritative Git workflow](../../.github/instructions/git-flow-multi-agent.instructions.md) requires local checks and Conventional Commits.
The app owns this isolated branch.
This repair does not change any shared instruction or constitution.
It does not claim complete compliance with inherited structural debt.

The fixed reservation uses five-file feature and test directories.
It does not reorganize shared parent directories.
The parent child counts and the separate maintenance work remain recorded in the plan.
The product diff does not add a comment or logging sweep.
It preserves all non-target product bytes.
These dispositions do not authorize another issue or a shared governance change.

PowerShell and its prerequisite or companion commands remain unavailable.
No successful PowerShell result is claimed.
The configured STE dictionary is absent.
The recorded STE scores use heuristic checks only.
External Markdown links remain unmeasured.
The final offline link check reads all seven owned Markdown files and finds no broken local link.
The final writing check reads all twelve owned Python and Markdown files.
Scores range from 93 through 100.
The missing dictionary remains an explicit skipped capability.

## Local completion boundary

The base remains `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
The authorized local commit remains pending.
The parent must separately grant publication against a verified current base.
Publication remains position 18 after #3300.
The closed parent PR does not grant that permission.
Protected merge and exact-main local proof remain deferred.
