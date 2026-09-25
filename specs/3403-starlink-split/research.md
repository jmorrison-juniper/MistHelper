# Research: Move the Starlink dashboard to its own repository

**Issue**: #3403 | **Spec**: [spec.md](spec.md)

## Decision 1: Keep the history with git-filter-repo

**Evidence**: `git log --all` for the four Starlink paths found 12 commits. Two
paths, `starlink_tui.py` and `starlink_requirements.txt`, left the tree in
earlier commits.

**Decision**: run `git-filter-repo` on a new clone with the four paths. The
result holds 12 commits. At the tip of that history, each file matches
MistHelper `origin/main`. One more commit then adds the README, the license,
and the CI workflow.

**Why not a copy**: a copy loses the authors, the dates, and the reasons.

## Decision 2: Keep the old commit messages

**Evidence**: the old messages name MistHelper issues with a `#N` reference.

**Decision**: keep the messages. The README states that each `#N` in the old
history names a MistHelper issue. A rewrite gains nothing. A rewritten
`Closes #N` in the new repository can close the wrong issue.

## Decision 3: A public repository with the MistHelper license

**Evidence**: MistHelper is public, and the dashboard code was public there.
MistHelper uses CC BY-NC-SA 4.0. The dashboard header read "License: MIT".
That line came back when a later commit added the file again. No commit chose
MIT for the project.

**Decision**: make the repository public. Copy the MistHelper `LICENSE` file,
and change the header to name CC BY-NC-SA 4.0. A public repository spends no
Actions minutes.

## Decision 4: A submodule for the SpaceX protocol files

**Evidence**: the dashboard loads the protocol files from
`<script folder>/starlink-api-reference/device-api`. The upstream repository,
`SpaceExplorationTechnologies/enterprise-api`, has no license file. Its
`.gitignore` file ignores `*_pb2*`, so the generated modules keep the submodule
clean.

**Decision**: pin the upstream repository as a submodule at `0cc45a7`. The new
repository then holds a pointer and no copy.

## Decision 5: Keep the CodeQL register rows

**Evidence**: the register job reads the dismissed alerts through the API. It
does not read the source files, and it ignores a change of line. On
2026-09-25, alerts #55, #56, and #57 on the deleted file `maps_manager.py` had
a `fixed_at` date, and their state stayed `dismissed`.

**Decision**: keep rows #193 and #194. The two alerts stay in the dismissed
set, so the register still matches the API.

## Decision 6: Remove the dashboard rows from the performance catalog

**Evidence**: the first CI run of pull request #3407 failed three tests in
`tests/guardrails/test_performance_hook_catalog.py`. The catalog of #2448
named `starlink_dashboard.py` in the inventory and in four hook rows. A local
search had skipped the `specs/` folders, so it missed these rows. Pull request
#2915 set the pattern: it removed the rows of two deleted files and counted
each summary again.

**Decision**: remove the 2 inventory rows and the 4 hook rows. Count
`hook-catalog-summary.json`, `scan-summary.json`, and `strategy-coverage.csv`
again. A script first proved that its count gave the current summaries. It
then wrote the new counts, and the same check passed on the new files.
