# The commit citations of the capture portal branch

Issue #1997 asked what to do about the hash citations of the feature branch
`feat/1823-upgrade-capture-portal`. This page answers that question.

## What happened

Pull request #1825 merged on 2026-08-26. GitHub squashed the 85 commits of the
branch into one commit on `main`:

```
f60974288249e5381110fec1f00cf0365a30eedb
feat(web-portal): pre-upgrade and post-upgrade capture portal with comparison (#1823) (#1825)
```

The branch itself is deleted. `git ls-remote --heads origin
feat/1823-upgrade-capture-portal` answers nothing.

## What that costs a reader

Two documents of this feature cite branch commits as evidence.
`audit-2026-08-20.md` and `HANDOFF.md` hold 19 such citations between them.

Every one of those commits is now unreachable from a remote reference. A fresh
clone cannot resolve any of them. A reader who runs `git show <hash>` gets a
fatal error and no evidence.

The issue weighed a rebase against a merge and asked which one to take. Neither
choice remains. The squash merge already voided the citations, so the only work
left is to make the record readable again.

## The record

Every citation below names work that reached `main` inside the squash commit
`f6097428`. The subject line came from the commit itself while the objects were
still readable in a local clone.

Read the subject to learn what the citation claims. Read `f6097428` to see the
delivered code.

| Cited hash | Subject of the branch commit |
| - | - |
| `1f49202f` | docs(1823): mark the second changelog as an archive |
| `1f8176a6` | fix(1823): stop a takeover that no audit record can account for |
| `2af9a567` | fix(1823): refuse a start time that no upgrade can use |
| `3d83930` | fix(1823): make the lock lease outlive the cooldown so a takeover can run |
| `4a9d028` | fix(1823): report an unreadable device state as unknown, never as stopped |
| `506250b` | fix(1823): let the portal read a run back when no database answers |
| `6ce6fb4` | fix(1823): make the browser suite fail on a broken portal, never skip |
| `6ec72769` | fix(1823): keep the one reading of a site before its upgrade |
| `776dddd` | fix(1823): close the three comparison items of the audit |
| `7b094a9f` | fix(1823): tell the log when a page walk loses a page |
| `83b5c9e` | test(1823): drive the whole upgrade journey in a real browser |
| `9282eaa4` | fix(1823): name a refused cloud call instead of blaming the SDK |
| `952d83f` | test(1823): seed the stored captures the browser comparison and history need |
| `98acead7` | fix(1823): keep the uptime of a member that just rebooted |
| `9ddbe13` | fix(1823): give the options page a device row, so the run reaches a device |
| `b2bd098` | fix(1823): write the verified pre-check onto the run that owns it |
| `cc92b79` | fix(1823): refuse an upgrade start that names no device |
| `f49d11b0` | fix(1823): give the site back when a run never reaches its driver |
| `fc11b9e0` | fix(1823): keep a foreign fault message out of the run record |

## The rule this sets

Warning: do not cite a hash from a branch that a squash merge will replace. The
citation dies with the branch, and a reader then holds a reference to nothing.

Cite one of these instead.

1. The pull request number. It survives every merge strategy.
2. The issue number. It survives even longer.
3. The file and the identifier. A reader can search for both.

A hash on `main` is safe to cite, because `main` keeps its history.
