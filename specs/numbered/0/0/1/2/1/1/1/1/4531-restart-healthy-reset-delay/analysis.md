# Analysis: Restart healthy reset test repair

This review checks the spec, plan, and tasks against the remote code on main. It lists each defect in the merged work and each unresolved item. Remote line numbers cite the main branch.

## Consistency review

- **Spec and plan**: FR-005 and FR-006 map to T005. FR-008 maps to T-REMOTE-CI and T-MERGE. Principle IV scope note D-6 matches the plan Principle IV table.
- **Spec and out of scope**: The out-of-scope items match the plan file map. The plan leaves `container/scripts/misthelper-session.sh` and `tests/unit/container/output_defaults/session.py` unchanged.
- **Plan and tasks**: Each file change appears in one task. T001 to T004 are verified tasks. T005 is the only open repair to the test file.
- **Tasks and remote code**: The test file blob on main is `4c4bc48bd5071c438fd7d02a5cbb8caacb02a313`. The record cites line numbers from that blob.
- **Local and remote copies**: The local `Containerfile` is 10338 bytes. The remote file is 10144 bytes. The local `spec-route.ps1` is 4572 bytes. The remote file is 4455 bytes. This record uses remote values only for those files.
- **Issue text and repository**: The issue reports Python 3.13.13 and pytest 9.1.1. The repository requires Python 3.15 (remote line 23 of `pyproject.toml`) and pins pytest 9.2.0 (remote line 325 of `requirements-dev.txt`). The `in-progress` label from the October 31 comment is absent now. T-PR adds it.
- **Issue text and baseline**: The issue states that the test inputs and the session script did not change. The session script blob is equal at baseline and on main. The plan row for plan2 is the same at baseline (line 254) and on main (line 292).

## Defects in merged work and related code

- **A1. Logging gap (Principle VII)**: Two functions added by PR 4555 log no action (remote lines 351 to 370 and 372 to 380). Severity: medium, because the constitution calls Principle VII non-negotiable. Repair: T005.
- **A2. Comment gap (Principle VI)**: Only line 238 of `CLOCK_SOURCE` has a bash comment. The other bash lines (remote lines 239 to 259) carry no comment. Severity: medium. Repair: T005.
- **A3. Five-item violation**: `TestSessionRestarts` holds six members after PR 4555. Severity: low, because the members form one feature. Recorded as justified with remediation R-1.
- **A4. Stall docstring check**: The docstring of the stall regression says "fourth launch". The injection tests `count == 3`. The recorder sets `count` to the number of prior launch entries (`session.py` line 51). So `count == 3` is the fourth launch. No defect.
- **A5. Real-time baseline case**: At baseline, the healthy threshold was 2 seconds (baseline line 257). The recorder slept real time (`session.py` line 67). The plan2 case therefore depended on real timing. PR 4555 added the one-second and two-second boundary cases (remote lines 302 and 312). The controlled clock makes them independent of real timing. PR 4555 resolves this defect.
- **A6. Environment mismatch**: The issue environment is outside the supported set (Python 3.13.13 and pytest 9.1.1). The reported result cannot serve as a supported reproduction. D-10 records the chosen environment.
- **A7. Separate failure in the same folder**: CI run 45459366990 on branch `fix/4912-observium-init` failed `tests/unit/container/output_defaults/test_contract.py::TestSourceContract::test_live_sources_require_option_two` with `AssertionError: expected=6 checked=6 rejected=1`. This failure is outside issue 4531. File a separate issue if it recurs on main.
- **A8. Shared helper import change**: The shared helper imports `bash_support` from a new path (remote line 21). The old path is absent on main (R13). The behavior is unchanged. No action.
- **A9. Threshold resolution (production)**: The session script compares a whole-second difference with the 30-second threshold (remote lines 141 and 150). If `SECONDS` counts whole seconds (U-2), a run longer than 29 real seconds can count as healthy. This effect is small and outside this issue. Record it for a later review.

## Unresolved items

The IDs in this list (N-1 to N-6) are separate from the Unverified IDs (U-1 to U-8) in `design/research.md`. Each entry names its Unverified counterpart where one exists.

- **N-1. Original timing** (research U-1): The original failing run recorded no launch timing. The cause of that one occurrence stays unverified.
- **N-2. Whole-second semantics** (research U-2): The Bash manual could not be fetched. The claim that `SECONDS` gives whole seconds is unverified. The test author assumes it (remote line 265 asserts `int(duration) == duration`).
- **N-3. Principle VI interpretation**: The rule exempts blank lines, closing braces, and decorators. This record also exempts three line types. The exempt types are the opening line of `CLOCK_SOURCE`, the def and class headers that carry docstrings, and the data rows of the parametrize lists. A reviewer may require comments on these lines.
- **N-4. Separate issues**: GitHub writes are outside this agent's scope. A human or the orchestrator must file the R-1 remediation issue and the separate `test_contract.py` issue.
- **N-5. Human review**: The issue carries `needs-human-review`. The merge waits for the human review.
- **N-6. Type checks in the test file** (research U-6): PR 4555 reports three mypy errors at lines 47, 50, and 83 of the test file. The configured mypy paths exclude tests (remote line 93 of `ci.yml`). The errors do not block CI. This record does not repeat that check.
