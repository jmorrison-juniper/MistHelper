# Contract: Preservation Pull Request and Proof

**Scope**: The GitHub requests and read fields that the preservation procedure uses.

**Source**: FR-005, FR-006, FR-008, and FR-009 in `../../spec.md`.

## Create Request

Create one request for each ready branch. Keep one preservation pull request open at a time.

```text
gh pr create --repo jmorrison-juniper/MistHelper --draft --base main --head <branch> --title "chore(git): preserve stranded branch <branch>" --body "Preservation only. The head of <branch> stays at <head SHA>. The pull request closes without merge in the same step. Refs #4583."
```

| Field | Required value | Rule |
| - | - | - |
| `--draft` | Present | A draft pull request cannot merge. |
| `--base` | `main` | The base branch is fixed. |
| `--head` | Exact branch name | Use the name from the work order row. |
| `--title` | `chore(git): preserve stranded branch <branch>` | Must match the Conventional Commits form. |
| `--body` | Text in the example | Must name the head SHA and `Refs #4583`. |

## Close Request

Close each preservation pull request in the same step that creates it.

```text
gh pr close <number> --repo jmorrison-juniper/MistHelper --comment "Preservation proof. Branch <branch> keeps head <head SHA> on origin. This pull request closed without merge. Reopen it to review the branch. Issue #4583."
```

Warning: The option `--delete-branch` deletes the branch from origin. Never add it to this command.

## Verification Read

```text
gh pr view <number> --repo jmorrison-juniper/MistHelper --json state,mergedAt,headRefName,headRefOid,title
```

| Field | Expected value |
| - | - |
| `state` | `CLOSED` |
| `mergedAt` | `null` |
| `headRefName` | The exact branch name |
| `headRefOid` | The head SHA from the work order |
| `title` | Matches `^chore\(git\): preserve stranded branch .+$` |

Read the branch head next:

```text
gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/<branch> --jq .object.sha
```

The output must equal the head SHA from the work order.

## Work Order Columns

Command Q-2 in `../quickstart.md` prints one row for each in-scope branch. The columns follow.

| Column | Meaning |
| - | - |
| Row | Position in the work order, starting at 1 |
| Branch | Exact branch name |
| Head | Full head commit SHA at the time of the read |
| Ahead | Commits that the branch holds above `main` |
| Behind | Commits on `main` that the branch does not hold |
| Files | Count of paths in the diff from the merge base to the head |
| Lane | `ready`, or the number of the open pull request that blocks the branch |

## Hold Record

| Field | Meaning |
| - | - |
| Branch | Exact held branch name |
| Blocking pull request | Open pull request that changes a path in the branch diff |
| Release condition | The blocking pull request has state `CLOSED` or `MERGED` |
