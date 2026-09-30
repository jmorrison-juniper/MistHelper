# Contract: Workflow and dependency policy

**Issue**: #3550
**Workflow path**: `.github/workflows/pull-request-title.yml`

## Workflow identity and events

Use the workflow label `Pull request title`.
Use one job with the exact name `Conventional Commits PR title`.
The job reports the check. Do not substitute the older workflow label for the check name.

Declare only `pull_request`.
Its activity list must contain each item below exactly once.

```text
opened
edited
reopened
synchronize
ready_for_review
```

Do not declare `push`, `schedule`, `pull_request_target`, or another trigger.
Do not add branch filters, path filters, or their ignore variants.
Do not use a job or step condition to skip drafts, bots, forks, or documentation-only changes.
One supported event must start one title-check run.

## Concurrency

Use these exact expressions.

```text
group: ${{ github.workflow }}-${{ github.head_ref || github.ref }}
cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

A newer run replaces an older run in the same workflow and head-branch group outside `main`.
Another head branch keeps its separate group.
The reference provides the fallback when the head branch is unavailable.
Do not remove the `main` cancellation guard.

## Permission and execution boundary

- Grant only `contents: read`. Do not add or inherit a job-level write grant.
- Use a standard Linux runner and one five-minute timeout.
- Use the repository's approved checkout and setup-python action references.
- Set checkout `persist-credentials: false`.
- Use Python `3.13`.
- Run exactly `python -m scripts.pr_title_guard` as the checker command.
- Let the checker read the runner-provided `GITHUB_EVENT_PATH`.
- Do not insert `${{ github.event.pull_request.title }}` into any executable source.
- Do not use secrets, privileged events, network title lookups, or bot exemptions.
- Do not suppress a failed checker exit or use `continue-on-error`.

The workflow needs no package-install step or application import.
Untrusted PR code must never receive trusted permissions through this workflow.
The module CLI must fail on unreadable input with count zero.

## Dependabot changes

Only two scalar prefix values may change in `.github/dependabot.yml`.

| Ecosystem | Directory | Existing prefix | New prefix |
| --- | --- | --- | --- |
| `pip` | `/` | `deps` | `chore` |
| `github-actions` | `/` | `ci` | `ci` |
| `npm` | `/ops-portal` | `deps(ops-portal)` | `chore(ops-portal)` |

Keep `version: 2`, the three streams, and their current order.
Keep each weekly schedule and each limit of five open pull requests.
Keep the `dependencies` label in all streams.
Keep the extra `ci` label in the github-actions stream.
Keep all existing comments and other keys.

Keep the npm `react` group with these four patterns.

```text
react
react-dom
@types/react
@types/react-dom
```

Keep the npm ignore entry for `typescript` with `version-update:semver-major`.
Do not add or remove a group, ignore, label, directory, limit, or schedule.

In the owned test, compare the complete parsed configuration with the pre-change policy.
Restore only the pip and npm prefixes before that comparison.
The expected policy must be a fixed snapshot, not a copy of the current file under test.
No extra snapshot file is needed.

New compliant bot titles pass the same title rule as contributor titles.
Existing `deps` and `deps(ops-portal)` titles fail.
A maintainer must rename those titles and allow the `edited` event to start a new check.
Do not close an update PR, disable a stream, or grant a bot exemption.

## Part 6 documentation

Change only Part 6 of `.github/instructions/git-flow-multi-agent.instructions.md`.
Name the `Pull request title` workflow and its `Conventional Commits PR title` check.
Document the four accepted forms, nine types, scope rule, description rule, and forbidden characters.
Document title correction and the title-edit rerun.
Document the common bot policy, two new prefixes, unchanged Actions prefix, and existing-title maintainer rename.

State that the check is not a new merge requirement.
Require separate owner approval before anyone adds it to required statuses.
Retain Conventional Commits and the existing squash-merge rules.
Preserve every other Part and every other shared instruction file.
Use semantic Part 6 tests that remain valid after legitimate changes to another Part.
Prove this issue's Part 6-only instruction diff once with git during implementation.
Record that evidence in the feature-owned context, not a permanent hash in the test.

## Enforcement and release boundary

Do not change repository settings, protection, or required statuses.
Keep strict protection and the current required checks, including CodeQL.
Keep `squash_merge_commit_title=PR_TITLE`.
Use only the owned `changelog.d/issue-3550-pull-request-title-guard.md` release fragment.
Do not edit `ci.yml`, `quality-gates.md`, or `CHANGELOG.md`.

## Contract evidence

The owned guardrail test must check parsed settings, not only loose substrings.
It must fail if an event disappears, a filter appears, cancellation changes, or a write permission appears.
It must also fail for unsafe title interpolation, bot exemptions, unrelated bot-policy changes, or a missing Part 6 check name.
Import the existing YAML parser directly. Missing parser capability must fail, not report a successful skip.
