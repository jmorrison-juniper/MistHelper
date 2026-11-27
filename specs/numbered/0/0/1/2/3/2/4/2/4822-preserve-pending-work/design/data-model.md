# Data Model: Preserve Pending Work Before Branch Cleanup

This model names each entity, its natural key, its fields, and its allowed state changes. The entities are records of Git objects, private files, and GitHub reads. The record holds no product data.

## Snapshot

- Natural key: the snapshot tag name under `refs/tags/recovery/4822/`, such as `ap-report`.
- Fields: the full commit identifier, the parent identifier, the tracked file count, and the counts of identical, different, and absent files.
- Values: the nine rows of the snapshot table in `design/research.md`.
- States: `inventoried`, then `archived`, then `bundled`, then `reviewed`. Publication follows only after FR-009 approval.
- Rule: A snapshot tag never moves. A new capture uses a new tag name.

## Recovery branch

- Natural key: the local branch name, such as `chore/2746-recovered-specification`.
- Fields: the tip identifier, the base identifier, and the count of commits above the base.
- Values: the four rows of the recovery branch table in `design/research.md`.
- States: `local-only`, then `reviewed`, then `published` after approval.
- Rule: No recovery branch is deleted in this issue (D-13).

## Archive

- Natural key: the SHA-256 hash of the ZIP file.
- Fields: the entry count and the name of the snapshot or worktree that it holds.
- States: `hashed`, then `verified`, then `retained`.
- Rule: A hash mismatch sets the archive to `rejected`. A rejected archive is never a copy.

## Bundle

- Natural key: the SHA-256 hash of the bundle file.
- Fields: the reference count and the results of `git bundle verify` and `git fsck`.
- States: `created`, then `verified`, then `restored`.
- Rule: The restore must hold each reference that the bundle lists.

## Registration

- Natural key: the worktree folder name in `git worktree list --porcelain`.
- Fields: the head identifier, the branch name, and the prunable flag.
- States: `active`, then `prunable`, then `removed`.
- Current values: 34 entries in total. One is the main checkout. Thirty-one linked entries are active. Two linked entries are prunable.

## Admin directory

- Natural key: the directory name under `.git\worktrees\`.
- Fields: the registration that it names.
- States: `present`, then `pruned`.
- Current values: `dynamic-jvd-labs-offline-preview` and `ok-make-that-change-then-reun-that-report`. Both are blocked (B-01).

## Merge candidate

- Natural key: the local branch name.
- Fields: the tip identifier, the count of commits above main, and the count of pull requests with that head.
- States: `unmerged`, then `merged-by-git`, then `deleted`.
- Current values:

| Branch | Tip identifier | Commits above main | Pull requests | State |
| - | - | - | - | - |
| feat/4631-offline-jvd-preview | 02d7d1798d9d5ab17d9de33da122d0b224adaf64 | 0 | 0 | merged-by-git |
| agents/ok-make-that-change-then-reun-that-report | d29cfd3984bcd00074d7b73c6d786be9edce249c | 0 | 0 | merged-by-git |
| jmorrison-juniper-github-sync-update-merge | 6ea93b1074550ea5d89fbdb661e3c3b6e00cc38b | 0 | 0 | merged-by-git, registration active (B-05) |

- Rule: `git branch -d` deletes a candidate only after T007, T009, and T010 finish.

## Remote check

- Natural key: the check identifier, such as `RC-01`.
- Fields: the claim, the path, the ref, the blob SHA, the result, and the line.
- States: `present`, `absent`, or `partial`.
- Rule: Each check appears once in `design/research.md` and once in `STATUS.json`.

## Blocker

- Natural key: the blocker identifier, such as `B-01`.
- Fields: the cause, the next action, and the owner.
- States: `open`, then `resolved`.
- Rule: A resolved blocker stays in the issue report with its resolution.
