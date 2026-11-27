# Contract: Bootstrap Locked-Sync Cause

**Scope**: The observable behavior of `scripts/bootstrap_worktree.py` when the locked sync fails. This contract covers the command, the environment names, the messages, and the invariants. The PowerShell wrapper `scripts/bootstrap_worktree.ps1` keeps its behavior.

## 1. Invocation

- Python: `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py [--recreate] [--public-lock-index]`
- PowerShell: `.\scripts\bootstrap_worktree.ps1 [-Recreate] [-PublicLockIndex]`. The wrapper passes `--public-lock-index` when `-PublicLockIndex` is set (`scripts/bootstrap_worktree.ps1` line 68, RC-13).

## 2. Command

`uv sync --locked --extra dev`, run from the repository root. The command has no other option (`scripts/bootstrap_worktree.py` line 466, RC-01). The comment on that line states that the command enforces the committed lock.

## 3. Child Environment (names only)

| Name | Value or role | Change by this record |
|---|---|---|
| `UV_INDEX_URL` | The primary index, from the pip primary index or the public override | Unchanged |
| `UV_EXTRA_INDEX_URL` | The extra index, from the pip extra index | Unchanged |
| `UV_DEFAULT_INDEX`, `UV_INDEX` | Removed before the mapping (lines 407 to 411) | Unchanged |
| `UV_CONFIG_FILE` | Removed (line 424) | Unchanged |
| `UV_NO_CONFIG` | `1` (line 419) | Unchanged |
| `UV_SYSTEM_CERTS` | `1` (line 418, RC-03) | Unchanged |
| `UV_NATIVE_TLS` | Set to `1` (line 417, RC-02) | Removed from the child environment (FR-006) |
| `UV_LINK_MODE` | `copy` (line 416) | Unchanged |
| `UV_HTTP_RETRIES`, `UV_HTTP_TIMEOUT` | `1` and `15` (lines 420 and 421) | Unchanged |
| `PIP_INDEX_URL`, `PIP_EXTRA_INDEX_URL` | Read by the mapping (lines 432 to 446, RC-04). The bootstrap does not change them. | Unchanged |

## 4. Failure Verdicts and Final Messages

| Verdict | Condition | Final message |
|---|---|---|
| index-mismatch | The lock check output holds "needs to be updated", and the primary index differs from the first registry source. | The text of `INDEX_MISMATCH_MESSAGE` (line 136, RC-06), followed by the text ` Active index variables: ` and the comma-separated names of the index variables that hold a value in the child environment. If no name holds a value, the text reads `none`. |
| lock-drift | The lock check output holds "needs to be updated", and no primary index exists, or the primary index equals the registry source. | The text of `LOCK_DRIFT_MESSAGE` (line 141, RC-07), unchanged. |
| unknown | The lock check passes, cannot start, or prints no stale phrase. | The original failure text, unchanged. The text reads `The locked UV sync failed with code` followed by the exit code. |

The stale phrase is "needs to be updated" (`STALE_LOCK_TEXT`, line 153, RC-08).

## 5. Output Rules

- Every log line uses ASCII characters only.
- An info line runs before the locked sync. It names the active index variables and holds no value.
- A debug line runs after the locked sync. It reports the exit code.
- An error line reports a failed locked sync. The error line keeps the existing text.
- No output contains an index URL, a host name, or a credential.
- `main` prints the text `The bootstrap failed:` followed by the message, and it returns exit code 1 for a failed run (line 900, RC-08 context).

## 6. Invariants

- The locked sync never falls back to a frozen sync.
- The bootstrap never writes the pip configuration.
- The public index serves the locked sync when `--public-lock-index` is set. The existing probe also uses the public index when the configured index does not answer (lines 235 to 258).
- The lock check runs with the same child environment as the locked sync (line 495 onward).

## 7. Compatibility

- The existing contract test `tests/contract/packaging/test_bootstrap_compose_provider.py` expects the same locked sync command. It stays valid.
- Existing callers that read the exit code keep the same codes: 0 for success and 1 for a failed run.
