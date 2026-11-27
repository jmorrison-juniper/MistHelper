# Contract: Gate and prune output

This contract lists the stdout lines and exit codes of the analyzer after this change. Lines that already exist keep their text. Lines marked new are added by this change.

## Gate run (`--gate`)

| Order | Stream | Line format | Status |
| - | - | - | - |
| 1 | stdout | `gate_scope: %d files checked, %d findings checked` | Existing. Printed on every gate run (R-37, R-38, R-51). |
| 2 | stdout | `gate_new: %s %s:%d %s` | Existing. Printed for at most 20 new findings (R-42). |
| 3 | stdout | `gate_new: %d additional findings not shown` | Existing. Printed when more than 20 new findings exist. |
| 4 | stdout | `gate_removed: %d baseline occurrences no longer match in analyzed files` | New. Printed on every gate run. |
| 5 | stdout | `gate: %d new findings vs baseline` | Existing. Printed last in the gate decision (`baseline.py`, blob a5b505cd). |

The `gate_new` fields are rule identifier, file path, line number, and explanation. The line number is information only.

The `gate_removed` count includes only baseline occurrences in analyzed files. An analyzed file is a file the run parsed without a parse error.

## Exit codes

| Code | Meaning |
| - | - |
| 0 | The run has no new findings. |
| 1 | The run has at least one new finding. |
| 2 | The run has an input or usage error. Causes include a missing baseline, malformed JSON, an invalid `content_anchor`, a source file that cannot be read, or conflicting mode flags. |

Caution: exit code 2 stops the gate before any comparison. A consumer must not read exit code 2 as a pass.

## Prune run (`--prune-baseline`)

| Order | Stream | Line format | Status |
| - | - | - | - |
| 1 | stdout | `prune: dropped %d stale baseline path(s)` | Existing (R-41). Counts paths of unscanned files. |
| 2 | stdout | `prune: dropped %d baseline occurrence(s)` | New. Counts unmatched occurrences in analyzed files. |

Prune exits 0 after it writes the baseline file. It exits 2 for a usage error, such as a missing `--baseline` value.

## Write run (`--write-baseline`)

The write run keeps its existing output lines and its existing exit behavior. The baseline file it writes contains `content_anchor` for every entry, as the baseline schema contract describes.

## Output rules

- Every line uses ASCII characters only.
- No line prints a secret, a token, or a password.
- A changed-scope run (`--changed-from`) counts only the files in scope for `gate_removed`.
