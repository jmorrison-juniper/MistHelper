# Release-note fragments

Each change owns one file in this directory. A feature branch never edits
`CHANGELOG.md`.

## Why this directory exists

Every open pull request edited the `## [Unreleased]` section of `CHANGELOG.md`.
Each pull request touched the same lines near the top of that file. Git reported
a conflict on every rebase, and an engineer repaired the same lines again and
again. A unique file for each change removes the shared line.

The repository also marks `CHANGELOG.md` with `merge=union` in `.gitattributes`.
That merge rule protects old branches while they drain. It is a safety net, not
the long-term process. A union merge can keep duplicate entries and cannot prove
that each pull request kept a complete release note. Fragments keep ownership
explicit and let the release coordinator review one file for each change.

## Name the file

Give the file a name that no other change can choose. Use the first rule that
fits.

| Condition | File name | Example |
| - | - | - |
| The pull request exists. | `pr-<number>.md` | `pr-2451.md` |
| The issue exists, and the pull request does not. | `issue-<number>-<slug>.md` | `issue-2439-dashboard-summary.md` |
| No issue and no pull request exist. | `<YYYY-MM-DD>-<slug>.md` | `2026-09-11-token-refresh.md` |

Take the slug from the branch name. Replace each separator with a hyphen.

Keep the first name after the pull request opens. A rename creates a delete and
an add, and a reviewer then reads the pair as a conflict.

## Write the fragment

Copy the shape of an entry in `CHANGELOG.md`. Write one `###` heading that names
the change. Write one bullet for each change type. Use `Added`, `Changed`,
`Fixed`, `Removed`, or `Security`. Name the issue at the end of the bullet.

```markdown
### Search organization Mist Edges (menu 253)

- **Added**: Menu 253 calls `searchOrgMxEdges` for an organization and exports
  the rows through CSV, SQLite, or ArangoDB. Issue #1375.
- **Fixed**: The filter prompts are skipped under `--test`, so the unattended
  sweep never blocks on stdin. Issue #1765.
```

A fragment carries no version number. The release coordinator writes the
`version YY.MM.DD.HH.MM` heading, because that stamp belongs to the release.

## Obey these five rules

1. Edit your own fragment only.
2. Do not edit `CHANGELOG.md` on a feature branch.
3. Do not edit the fragment of another change.
4. Add no fragment for an internal-only change. State that reason in the pull
   request body.
5. Create no index file and no summary file here. An index is a shared file, and
   a shared file conflicts again.

Warning: never resolve a conflict in `CHANGELOG.md` by deleting the entry of
another change. That delete removes a released record, and no run reports the
loss. Move each entry into its own fragment instead.

## The release coordinator writes the aggregate

Only the release coordinator moves the merged fragments into `CHANGELOG.md`. The
coordinator does that work on the release branch, after the feature merges. The
coordinator deletes the fragments in that release only, and keeps each issue
link.
