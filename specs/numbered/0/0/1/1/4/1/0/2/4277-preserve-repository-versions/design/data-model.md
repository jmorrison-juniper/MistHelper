# Data Model: Preserve Repository Versions and Update the Local Main Checkout

This model defines the records that the preservation evidence uses. The record stores no database. Each entity has a natural key and a set of states.

## LocalHead

- **Natural key**: The full ref name, for example `refs/heads/main`.
- **Fields**: `tip_sha` (40 lower-case hexadecimal characters), `origin_state` (`same-tip`, `different-tip`, or `absent`), `merged_into_main` (`yes` or `no`), and `disposition`.
- **Disposition rule**: The disposition follows from the two fields in the table below.

| merged_into_main | origin_state | disposition |
| - | - | - |
| yes | same-tip | integrated-remote-copy |
| yes | absent | integrated-local-only |
| yes | different-tip | integrated-diverged |
| no | same-tip | preserved-remote-copy |
| no | absent | preserved-local-only |
| no | different-tip | preserved-diverged |

- **Measured counts (2026-11-26)**: `integrated-remote-copy` 1 (`main`). `integrated-local-only` 4. `preserved-remote-copy` 7. `preserved-local-only` 318. `integrated-diverged` 0. `preserved-diverged` 0. The total is 330 (research L-04).
- **State transitions**: This record makes no transition. A disposition changes only when the owner pushes, merges, or deletes the ref. Each of those actions occurs outside this record. The owner records each decision in the recovery register.

## CitedCommit

- **Natural key**: The full commit SHA.
- **Fields**: `remote_presence` (`present` or `absent`), `local_presence` (`present`, `absent`, or `not-required`), and `source` (the issue, comment, or pull request that names the commit).
- **State transitions**: `unknown` changes to `present` or `absent` after one check. This record deletes no commit. A `present` result stays `present` unless the owner removes the commit outside this record.
- **Measured values**: `9ba3a7e5`, `3ead4ec4`, `6e197710`, `29c54897`, and `31b752f0` are `present` on GitHub. `7d16297d`, `3cf37c7c`, and `d8900984` are `absent` on GitHub. `7d16297d`, `3cf37c7c`, and `d8900984` are `absent` locally. The local presence of `85086493` is `not-required`, because the merged head check uses GitHub only (research R-04).

## RecoveryItem

- **Natural key**: An identifier from `U-001` to `U-009`.
- **Fields**: `severity` (`warning`, `caution`, or `note`), `owner`, `close_condition`, and `status` (`open`, `partial`, `accepted`, or `resolved`).
- **State transitions**: `open` changes to `partial` when some evidence exists. `partial` or `open` changes to `accepted` when the owner records a risk decision. `partial` or `accepted` changes to `resolved` when the close condition holds. A `resolved` item stays in the register with its evidence.

## BackupEvidence

- **Natural key**: The issue comment identifier that states the evidence, for example `IC_kwDOQltU8c8AAAABc1wR8A`.
- **Fields**: `storage_class` (`same-disk`), `recovery_window_hours` (`24`), `evidence_source` (`owner-reported`), and `figures` (3,718 references, 75,803 objects, 54,109 working files, seven dirty worktrees, and 3,947 version catalog rows).
- **State transitions**: `owner-reported` changes to `verified` only when three conditions hold. The owner supplies the bundle. `git bundle verify` exits with code 0. `git bundle list-heads` reports the stated reference count (git-bundle documentation, research section 4.3).

## ValidationRun

- **Natural key**: The validation identifier from `V-01` to `V-15`, with the baseline commit SHA.
- **Fields**: `command`, `exit_code`, `summary_line`, `result` (`pass`, `fail`, or `not-run`), `cause` (required when the result is not `pass`), and `run_time_utc`.
- **State transitions**: `not-run` changes to `pass` or `fail` after a run. A `fail` result reruns only after the cause is recorded. A `not-run` result stays final only when a cause is recorded. Validation V-05 uses this final state.
