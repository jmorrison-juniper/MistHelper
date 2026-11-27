# Contract: Locked Sync Source Policy

This contract defines the command-line behavior and the child environment of the locked sync. It applies after option C of decision D-1 is approved. Each message uses ASCII text and names no URL, host, or credential.

## Command

```text
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py [--recreate] [--public-lock-index]
```

| Option | Effect after the change |
| - | - |
| `--recreate` | Deletes `.venv` before the bootstrap creates it again. Unchanged. |
| `--public-lock-index` | Sets the locked sync primary index to the public index for one run. Keeps the name and arguments (FR-010). Matches the default under option C. |

Exit codes:

- `0`: the environment is ready. The locked sync succeeded.
- `1`: a required step failed. The locked sync failed, or the lock has no registry.

## Messages

| Condition | Log level | Text |
| - | - | - |
| The configured index differs from the lock registry | warning | `Caution: the locked sync uses the registry in uv.lock. The configured package index does not change this sync. Your pip configuration is not changed.` |
| `uv.lock` names no registry | error | `The lock file names no registry, so the locked sync cannot start. Check uv.lock, then run the bootstrap again.` |
| The lock check reports a stale lock | error | The existing lock drift message (research.md, R38 branch). |
| The lock check reports a current or unknown lock | error | The original locked sync error. Unchanged (FR-011). |

The Caution text describes the rule, not the value. It contains no URL, host, or credential (FR-017).

## Child environment of the locked sync

| Variable | Value | Source |
| - | - | - |
| `UV_INDEX_URL` | Lock registry | First registry line in `uv.lock` (research.md, R31, R43). |
| `UV_EXTRA_INDEX_URL` | Removed | Alias removal (R92). Configured extra indexes never reach the locked sync. |
| `UV_INDEX` | Removed | Alias removal (R92). |
| `UV_DEFAULT_INDEX` | Removed | Alias removal (R92). |
| `UV_CONFIG_FILE` | Removed | Existing behavior (R91). |
| `UV_NO_CONFIG` | `1` | Existing behavior (R90). |
| Other uv settings (UV_LINK_MODE, UV_NATIVE_TLS, UV_SYSTEM_CERTS, UV_HTTP_RETRIES, UV_HTTP_TIMEOUT) | Unchanged | Design rule: this change edits no other uv setting. |
| `PIP_*` variables | Unchanged | Design rule: this change edits no pip variable. |

## Locked sync command

```text
uv sync --locked --extra dev
```

The command runs from the worktree root. The bootstrap never adds `--frozen` and never skips the command (FR-001, FR-006).

## Files the contract never changes

- `uv.lock`
- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- Any pip configuration file
- Any uv configuration file

## Verification

Each row maps to a test. TST-01 covers the child environment. TST-03 covers the Caution text. TST-04 covers the missing registry. TST-02 covers redaction. KT-01 covers the locked command. KT-02 covers configuration files and redaction. KT-04 covers the opt-in option. KT-05 covers the original error.
