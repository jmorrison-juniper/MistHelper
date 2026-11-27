# Research: Top-Five Complexity Target Map

This file holds the decisions, the remote verification table, the route check, the complexity evidence, the sources, and the unverified items. Each remote check ID (R01 to R48) matches one object in the `remote_checks` array of STATUS.json.

## Decisions

### D-1 Map each target to its current file

- Alternatives: (a) search every file under `src/` and `MistHelper.py` for each name. (b) Qualify each name with its class. (c) Map each target to its file.
- Chosen: (c).
- Reason: The map is small and explicit. Radon runs on four files only. The lookup matches the file suffix and the bare name (R46).
- Risk: A future move needs a map edit. Guard test 1 detects the move (FR-004).

### D-2 Keep the five bare target names

- Alternatives: (a) qualified names, such as `PacketCaptureManager._execute_site_capture_loop`. (b) Bare names.
- Chosen: (b).
- Reason: The integration module and the fixture use bare names (R14, R15). The spec-195 record uses them (R45). Radon reports methods by bare name (R25).
- Risk: Two files that define one bare name need the file key to tell them apart. The lookup uses the file key (R46).

### D-3 Keep one radon run per target file through `_run_radon(path)`

- Alternatives: (a) one radon run for every file. (b) Change `_run_radon` to accept a list. (c) One radon run for each file.
- Chosen: (c).
- Reason: The timeout test calls `_run_radon("MistHelper.py")` (R16). The 300-second bound applies to each run (R02).
- Risk: Four runs take longer than one run. The added time is unmeasured (U-3).

### D-4 Build each map key with `pathlib.Path`

- Alternatives: (a) literal strings with forward slashes. (b) `os.path.join`. (c) `str` applied to a `pathlib.Path` object.
- Chosen: (c).
- Reason: The constitution forbids hard-coded separators (R39). Radon returns the path string unchanged (R23). The key and the lookup therefore match on each operating system.
- Risk: Windows keys contain backslashes. Guard test 2 runs the real utility. The runtime result is unverified until task T004 (U-6).

### D-5 Add three guard tests to the existing integration module

- Alternatives: (a) a new module under `tests/unit/`. (b) The existing integration module. (c) `test_subprocess_timeouts.py`.
- Chosen: (b).
- Reason: The module already imports `MistHelper` and covers the five names (R14). AGENTS.md prefers existing test files.
- Risk: None new. The new tests reuse the existing import.

### D-6 Leave `main()` and the module layout unchanged

- Alternatives: (a) convert the utility into a class. (b) Split `main()` into helpers. (c) Leave both unchanged and record the debt.
- Chosen: (c).
- Reason: This issue fixes the map. A class conversion renames names that the timeout test uses (R16). It also widens the review.
- Risk: The debt remains until a follow-up issue closes it. The debt appears in plan.md, Complexity Tracking.

### D-7 Add no CI job and no `RADON_PATHS` change

- Alternatives: (a) a CI job that runs the utility. (b) Add the script to `RADON_PATHS`. (c) No CI change.
- Chosen: (c).
- Reason: A new job spends runner minutes (AGENTS.md, GitHub Actions minutes). Adding the script to `RADON_PATHS` gates a file whose `main()` is estimated at CC 13 (U-2). CI would then fail on debt that exists before this change.
- Risk: The utility stays outside CI. The guard tests in the pytest run cover the map.

### D-8 Keep the changelog fragment name after the pull request opens

- Alternatives: (a) rename the fragment to `pr-<number>.md` after the pull request opens, as R43 describes. (b) Keep `issue-4837-check-top5-stale-target.md`.
- Chosen: (b).
- Reason: The README says a rename creates a delete and an add, and a reviewer reads the pair as a conflict (R28).
- Risk: A reviewer expects the `pr-` name. The pull request body explains the choice.

### D-9 Add one changelog fragment

- Alternatives: (a) omit the fragment and state the reason in the pull request body (R29). (b) Add one fragment.
- Chosen: (b).
- Reason: The constitution says each change MUST add one fragment (R41). The constitution sets the rule for every change, and the README gives the file rules.
- Risk: The release coordinator reads one more internal fragment. The cost is low.

### D-10 Record Principle IV steps 10 to 12 as not triggered

- Alternatives: (a) dispatch the container build by hand with `gh workflow run container-build.yml`. (b) Wait for an automatic build. (c) Record that the steps do not trigger, with the trigger evidence.
- Chosen: (c).
- Reason: The container build triggers only on product paths (R21). This change touches none of them. A manual build makes an identical image and spends runner minutes.
- Risk: A reviewer reads the skipped steps as a missed step. The pull request body gives the reason and cites R21 and R40.

### D-11 Expect PASS and record the actual result

- Alternatives: (a) expect FAIL and raise the limit. (b) Expect PASS from CI evidence and record the actual result. (c) Skip the run.
- Chosen: (b).
- Reason: The CI radon gate passed on main. The gate reports no block above CC 10 in its paths (R18 to R20). Option (a) changes the gate, and option (c) breaks AGENTS.md.
- Risk: A target above CC 10 prints FAIL. The fix then needs a follow-up issue. The limit stays at 10.

## Remote Verification

Each row is one check. The ref is `main` on GitHub unless the row names a local path. A local path row lists `not applicable: local file` as its blob SHA. Result values are `present`, `absent`, `partial`, or `stale`.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | TARGETS names MistHelper.py as the only key | scripts/check_top5_complexity.py | main | 7e13d7f70518c21621535e7732b901ab800af765 | stale | 14 |
| R02 | _run_radon sets the subprocess timeout to the bound | scripts/check_top5_complexity.py | main | 7e13d7f70518c21621535e7732b901ab800af765 | present | 30 |
| R03 | main raises the missing-target error text | scripts/check_top5_complexity.py | main | 7e13d7f70518c21621535e7732b901ab800af765 | present | 66 |
| R04 | early_dependency_check is a module-level function | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1043 |
| R05 | _execute_site_capture_loop is absent from MistHelper.py | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | absent | 0 |
| R06 | start_org_packet_capture is absent from MistHelper.py | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | absent | 0 |
| R07 | device_events_52w is absent from MistHelper.py | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | absent | 0 |
| R08 | with_wan_overrides is absent from MistHelper.py | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | absent | 0 |
| R09 | The PacketCaptureManager class is defined | src/operations/execution/capture/packet_capture.py | main | c116511efd3ea2b8679e7fe7aab633fa07642c00 | present | 125 |
| R10 | _execute_site_capture_loop is a method of PacketCaptureManager | src/operations/execution/capture/packet_capture.py | main | c116511efd3ea2b8679e7fe7aab633fa07642c00 | present | 1118 |
| R11 | start_org_packet_capture is a method of PacketCaptureManager | src/operations/execution/capture/packet_capture.py | main | c116511efd3ea2b8679e7fe7aab633fa07642c00 | present | 1225 |
| R12 | device_events_52w is a static method of OrgAlarmEventExporter | src/operations/exporting/export/org_alarm_event_exporter.py | main | b46c4b156f1bccac870aa469375c90927bd4f9c9 | present | 151 |
| R13 | with_wan_overrides is a static method of GatewayExportUtils | src/mist/resources/gateway/gateway_export_utils.py | main | 5ea396219ddc3791f8fdf45720dc4a28c961b21a | present | 527 |
| R14 | The integration module imports four names (line 3) and asserts callables only (lines 11 to 38) | tests/integration/test_top5_compatibility_paths.py | main | c2d32be3fa66a54b583c990b3e727bd4bad29ae7 | present | 3 |
| R15 | The fixture top5_target_names lists the canonical names | tests/integration/top5_fixtures.py | main | dee983fd44d33e9c1f4510667ad8736b0800c32f | present | 9 |
| R16 | The timeout test calls _run_radon through the utility | tests/unit/prod_readiness/operations/execution/prod_readiness/test_subprocess_timeouts.py | main | cffdc8c54186c33ba24fa9c6e96135c8654f5171 | present | 114 |
| R17 | No line of ci.yml names the utility | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 0 |
| R18 | RADON_PATHS lists src/ and MistHelper.py, and it does not list the utility | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 99 |
| R19 | The radon job runs radon cc and complexity-gate with a maximum of 10 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 549 |
| R20 | Run 45774119357 on head f03c6c9b passed the radon job 139753527500 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 531 |
| R21 | The container build push paths list src/** and no scripts or tests path | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 16 |
| R22 | requirements-dev.txt pins radon 6.0.1 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| R23 | iter_filenames yields a file argument unchanged | .venv\Lib\site-packages\radon\cli\tools.py | local .venv | not applicable: local file | present | 266 |
| R24 | cc_to_dict copies the Function fields, including name | .venv\Lib\site-packages\radon\cli\tools.py | local .venv | not applicable: local file | present | 307 |
| R25 | The Function fields include name, lineno, complexity, and classname | .venv\Lib\site-packages\radon\visitors.py | local .venv | not applicable: local file | present | 15 |
| R26 | Radon counts If, For, BoolOp, and comprehension nodes (lines 234 to 252) | .venv\Lib\site-packages\radon\visitors.py | local .venv | not applicable: local file | present | 234 |
| R27 | quality-gates.md lists radon cc into complexity-gate | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 59 |
| R28 | The changelog README keeps the first fragment name after the pull request opens | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 32 |
| R29 | The changelog README omits fragments for internal-only changes | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R30 | spec-route uses base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R31 | spec-route uses a default route width of eight | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| R32 | The route parent 0/0/1/2/3/3/2 holds one record, 4838 | specs/numbered/0/0/1/2/3/3/2/3/4838-cross-org-subscription-inventory/spec.md | main | 2eb6afffbfebba8ad53510c5723e04f20e82a62d | present | 0 |
| R33 | The record folder for 4837 is absent on main | specs/numbered/0/0/1/2/3/3/2/2/4837-check-top5-stale-target | main | not applicable: path absent | absent | 0 |
| R34 | AGENTS.md requires a specification for three or more files | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 349 |
| R35 | AGENTS.md requires an inline comment on each executable line | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 99 |
| R36 | AGENTS.md requires logging when a touched block lacks logging | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 115 |
| R37 | Constitution Principle I sets the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R38 | Constitution Principle II requires class-based architecture | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| R39 | Constitution requires pathlib or os.path.join for file paths | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 310 |
| R40 | Constitution Principle IV step 10 waits for container-build.yml | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 166 |
| R41 | Constitution requires one changelog fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R42 | Copilot instructions set the managed roots and the base-5 route | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R43 | Copilot instructions add a fragment for each user-visible change | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R44 | Copilot instructions require Python 3.15 or newer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| R45 | Spec-195 task T007 marks the utility complete | specs/195-decompose-top5-functions/tasks.md | main | e9a8969bf124c4f81e84997cca9292cb9189bb81 | present | 35 |
| R46 | main runs _run_radon for each TARGETS key and matches the file suffix and the bare name | scripts/check_top5_complexity.py | main | 7e13d7f70518c21621535e7732b901ab800af765 | present | 54 |
| R47 | main prints the header (line 68), one row for each target (line 70), FAIL and return 1 (lines 73 and 74), PASS and return 0 (lines 75 and 76), and the entry point exits with the return value of main (line 80) | scripts/check_top5_complexity.py | main | 7e13d7f70518c21621535e7732b901ab800af765 | present | 68 |
| R48 | main and _run_radon raise the missing-path, radon-bound, and radon-failure errors (lines 33, 35, and 56) | scripts/check_top5_complexity.py | main | 7e13d7f70518c21621535e7732b901ab800af765 | present | 33 |

The table holds 48 rows. The STATUS.json array `remote_checks` holds 48 objects. The summary states 48.

## Route Check

- The brief sets ROUTE to `specs\numbered\0\0\1\2\3\3\2\2`.
- `spec-route.ps1` (R30, R31) writes the number in base 5, most significant digit first, padded to eight digits.
- Arithmetic: 4837 equals 1 x 5^5 + 2 x 5^4 + 3 x 5^3 + 3 x 5^2 + 2 x 5 + 2.
- The base-5 digits are 1, 2, 3, 3, 2, 2. Padded to eight digits, they give 0, 0, 1, 2, 3, 3, 2, 2.
- The route matches ROUTE.
- Sibling check: issue 4838 uses the route `0/0/1/2/3/3/2/3` on main (R32). The method gives the same result for 4838.
- Parent check: the parent `0/0/1/2/3/3/2` holds one child on main (R32). The new record adds one child, so the parent holds two children.

## Complexity Evidence

- Radon rules (R26): each function starts at 1. Each `if` adds 1. Each `for` adds 1. Each `BoolOp` adds its operand count minus 1. Each comprehension adds 1 and one more for each `if` clause.
- Estimate for `main()` (U-2): the base is 1. Four `for` loops add 4. Three `if` statements add 3. The generator comprehension with one `if` adds 2, and its `and` adds 1. The list comprehension with one `if` adds 2. The total is 13.
- CI log evidence (R19, R20): the radon job runs `radon cc` with the options `-a -nb` on the paths in `RADON_PATHS`. The `-nb` output lists blocks of rank B or worse only. The filtered job log holds no line for any target name, and it holds no line for the other three target files. Each target therefore ranks A, with CC 1 to 5 (U-1).
- Gate evidence (R19, R20): the `complexity-gate --max 10` step passed. The gate reports no block above CC 10 in its paths.

## Sources

1. GitHub issue #4837, read with `gh issue view 4837 -R jmorrison-juniper/MistHelper`. The state is OPEN. The labels are `bug` and `ci`. The issue has no comments.
2. Pull requests: `gh pr list --state all --search "4837"` returned no entry. `gh pr list --state all --search "check_top5_complexity"` returned no entry.
3. Issues: `gh issue list --state all --search "check_top5_complexity in:title,body"` returned no entry.
4. Remote tree: `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. It listed 11,404 entries, and it was not truncated. Every blob SHA in the table comes from this tree.
5. Remote file bodies: `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`, decoded from base64. Each line number in the table comes from these bodies.
6. Main head: commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, committed 2026-11-26T07:15:01Z. Its 31 added files lie outside `src/`, outside `MistHelper.py`, and outside the four files of the change.
7. CI run 45774119357. Event `workflow_dispatch`, conclusion success, on the main head. Job 139753527500, "Radon (complexity)", conclusion success. Its log was read for the radon lines only (U-7).
8. CI run 45124200240. Conclusion success on head 1d478930cdbe583ec5f320b1929142fd9a74ee79. Job 137524686650, "Radon (complexity)", conclusion success. Read for consistency only.
9. Issue #1943, "fix(tools): four subprocess calls have no timeout, so a stalled git or gh call hangs a CI gate for six hours". State CLOSED on 2026-08-23. The timeout test docstring in R16 cites this issue.
10. Spec-195: the remote folder `specs/195-decompose-top5-functions` exists (R45). Its name is not an issue number. `gh issue view 195` returned a merged pull request titled "feat(arango): site-level guest authorization graph storage".
11. Radon 6.0.1 source, local path `.venv\Lib\site-packages\radon\`. The files `cli\tools.py` and `visitors.py` hold the claims R23 to R26. The folder `radon-6.0.1.dist-info` confirms the installed version.
12. Local search for the five names and for the utility name. The search covered `scripts`, `tests`, `.github`, `documentation`, `src`, `MistHelper.py`, `changelog.d`, `specs`, `pyproject.toml`, and `README.md` in the local checkout. The search found no documentation page for the utility. It informs discovery only, and each claim rests on a remote check.
13. Governing documents read in full from the local checkout: `AGENTS.md`, `.github\copilot-instructions.md`, `.specify\memory\constitution.md`, `documentation\quality-gates.md`, and `changelog.d\README.md`. Each remote check cites its line on main.
14. Templates read from `.specify\templates\`: spec, plan, tasks, and checklist.
15. Reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`, read locally for shape only. Its content is not copied.
16. Validator `spec-drafts\_meta\validate-drafts.ps1` was read for its checks. It was not run, because the brief bars linters. The self-review repeats its checks by hand.
17. Not read: `documentation\architecture.md`, `documentation\development-setup.md`, `documentation\container-deployment.md`, and `documentation\operator-guide.md`. Reason: the utility is a developer script, and the documentation search found no reference to it.
18. Mist OpenAPI files and endpoint catalogs: not read, because the utility calls no Mist API.
19. Skills: the skill tool is available. No skill was loaded, because the issue touches no Podman, container, or Juniper device behavior.
20. `web_fetch`: not used. No external source was needed.

## Unverified

- U-1: The exact CC values of the five targets on main. Reason: the brief bars radon runs. The CI log omits blocks below rank B. Task T004 records the values.
- U-2: The CC of `main()`, estimated at 13. Reason: the estimate comes from the radon rules in R26. No radon run measured it.
- U-3: The run time of four radon runs. Reason: no run measured it. Task T004 records the time.
- U-4: The result of the test-quality analyzer. Reason: the procedure needs a commit first. Task T-LOCAL-GATES records the result.
- U-5: The result of the CI integration shard. Reason: CI has not run for this change. Task T-REMOTE-CI records the result.
- U-6: The radon key format on Windows at run time. Reason: the source reading (R23, R24) shows that radon returns the path unchanged. No run has executed it yet. Task T004 checks it.
- U-7: The other jobs of run 45774119357. Reason: only the radon job was read.
