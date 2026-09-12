# The stranded branch review of issue #1980

Issue #1980 found five branches that held commits above `main`. Each branch had
one copy. This page records the verdict for each one, and it records the loss
that followed.

Read [contributing.md](./contributing.md) for the rule that this review produced.

## The verdicts (measured 2026-09-03)

| Branch | Verdict | Evidence |
| - | - | - |
| `jmorrison-jnpr-sse-dropped-event-counter` | Merged | Commit `c7b811ed` in `main`, pull request #1981 |
| `jmorrison-jnpr-ci-pytest-gate-failure` | Superseded | `main` holds `_sleep_recorder` with the same thread guard |
| `fix-1840-thread-scan` | Superseded | Issue #1840 merged as commit `5b2a251d` |
| `jmorrison-jnpr-production-readiness-sweep` | Superseded | Issue #1863 added the `HEALTHCHECK`, and `container/scripts/start.sh` now reports a crash status |
| `ops-gate-fix` | Merged | The head subject is present in `main` |

No repair from any of the five branches is missing from `main`. No pull request
is needed for any of them.

## The loss

All five branches are gone from `origin` and from every local checkout. Issue
#2251 records the deletion.

Two heads were recoverable.

- `jmorrison-jnpr-ci-pytest-gate-failure` came back from `refs/pull/1848/head`,
  because pull request #1848 named it as the head.
- `jmorrison-jnpr-production-readiness-sweep` came back from a dangling commit,
  `8f1bf72d`, in one local checkout.

One head was not recoverable. `fix-1840-thread-scan` reached no pull request, and
no dangling object survived. Its 3 commits and 397 added lines are gone. The
content loss is zero, because issue #1840 delivers the same repair.

## What the review proved

A dangling commit is not a backup. `git gc` removes an unreachable object after
90 days, and it exists in one checkout only.

`refs/pull/<n>/head` is the only permanent copy. Open a pull request before any
cleanup, even a pull request that you plan to close without a merge.

## The check

`scripts/report_stranded_branches.py` names every branch that holds commits above
the base branch and has no open pull request. The `Stranded Branch Report`
workflow runs it every Monday and keeps one open issue with the result.

```powershell
python scripts/report_stranded_branches.py
python scripts/report_stranded_branches.py --min-age-days 14 --fail-on-find
```

The report skips a branch that is younger than the quiet period, because recent
work is active work. It also skips a bot branch, because a bot branch follows its
own lifecycle.
