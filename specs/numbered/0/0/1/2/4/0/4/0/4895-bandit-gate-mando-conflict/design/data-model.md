# Data Model: Bandit Gate Dependency Conflict

This change stores no data. The entities below describe CI and package state. Each entity lists its natural key and its state transitions.

## GateJob

- **Natural key**: The job database ID. The Bandit job ID is 137336719159 in run 45064243269.
- **Fields**: Name `Bandit (security)`, workflow `Quality Gates`, head SHA, conclusion, and steps.
- **Transitions**: Step 5 `failure`, steps 6 and 7 `skipped`, and the job `failure`. After the fix, steps 5 to 7 show `success` on the fix head.

## DependencyPin

- **Natural key**: The package name in `requirements-dev.txt`. For this change, the key is `mando`.
- **Fields**: Version, line number, and source commit.
- **Values**: `0.7.1` at line 179 on `main`. `0.8.2` at line 179 on the PR #4888 head. `0.7.1` at line 179 after the fix.
- **Transitions**: `0.7.1` changes to `0.8.2` in PR #4888. The value returns to `0.7.1` when PR #4888 closes without a merge.

## DependencyConstraint

- **Natural key**: The declaring package and the required package. For this change, the key is `radon` and `mando`.
- **Fields**: Specifier `<0.8,>=0.6`, and its sources. The sources are the installed METADATA line 31 and the PyPI `requires_dist` field.
- **Transitions**: None for radon 6.0.1. A newer radon release can change the specifier. The Dependabot ignore rule then changes too.

## DependabotIgnoreRule

- **Natural key**: The ecosystem `pip` and the dependency name `mando`.
- **Fields**: Update types `version-update:semver-major` and `version-update:semver-minor`.
- **Transitions**: Absent on `main`. Present after the fix merges. Removed in the pull request that raises radon to a release that accepts `mando` 0.8.

## DependabotUpdate

- **Natural key**: The pull request number 4888.
- **Fields**: Head branch `dependabot/pip/mando-0.8.2`, head SHA `e86098cdc2b189d217805b3b4060ef609cbc37af`, and state.
- **Transitions**: `OPEN` today. `CLOSED` after T-MERGE, with a closing comment that names the surviving branch.

## GateIssue

- **Natural key**: The issue number. Issues 4891 to 4905 name PR #4888.
- **Fields**: Title, labels, and state. The title of issue 4895 reads `CI: quality-gate `bandit` failed (PR #4888)`. The other 14 titles follow the same pattern with another gate name.
- **Transitions**: `OPEN` today. `CLOSED` after PR #4888 closes and a `main` run completes.

## Relationships

- `GateJob` runs the install of each `DependencyPin`. It fails when a `DependencyConstraint` rejects the pinned version.
- `DependabotUpdate` proposes a change to a `DependencyPin`.
- `DependabotIgnoreRule` prevents a new `DependabotUpdate` for the same pin.
- `GateIssue` reports a `GateJob` failure on a pull request.
