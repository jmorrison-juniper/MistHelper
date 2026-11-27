# Contract: Top-Five Complexity Check Command

## Command

- Working directory: the repository root.
- Windows: `.venv\Scripts\python.exe scripts\check_top5_complexity.py`
- macOS and Linux: `.venv/bin/python scripts/check_top5_complexity.py`

Caution: the utility resolves each target file from the working directory. Another working directory gives a missing-path error.

## Input

The command takes no argument. The utility reads the target map `TARGETS` (R01, R46). It runs radon 6.0.1 once for each target file (R22). Each radon run stops after 300 seconds (R02).

## Standard Output

Line 1 is the header `Target cyclomatic complexity results:`.

Lines 2 to 6 hold one row for each target. The rows follow the order of `TARGETS`. Each row has this form:

`- <name>: CC=<complexity> Rank=<rank> (<file>:<line>)`

- `<name>` is the bare function name.
- `<complexity>` is the cyclomatic complexity from radon.
- `<rank>` is the radon letter, from A to F.
- `<file>` is the key of the target map, exactly as written.
- `<line>` is the line number that radon reports.

Line 7 is blank. Line 8 is one of these two lines:

- `PASS: All target functions are CC <= 10`
- `FAIL: One or more target functions exceed CC 10`

## Exit Codes

| Code | Meaning |
| - | - |
| 0 | Every target has CC 10 or below. The line `PASS` prints. |
| 1 | At least one target has CC above 10. The line `FAIL` prints. |
| Non-zero | The utility raised an error. A traceback prints to standard error. |

Caution: a traceback and a FAIL result both end with a non-zero exit code. Read the last output line to tell them apart.

## Error Text

The four messages below keep their current wording (R03, R47, R48).

- `FileNotFoundError: Missing path: <file>` when a target file is absent.
- `RuntimeError: radon passed the 300s bound for <file>` when a radon run stalls.
- `RuntimeError: radon failed for <file>: <stderr>` when a radon run fails.
- `RuntimeError: Target function not found in radon output: <name>` when no radon record matches a target. The guard test names the file as well (FR-004).

## Compatibility

- The module-level names `TARGETS`, `_RADON_TIMEOUT_SECONDS`, `_run_radon`, and `main` keep their names and signatures (R02, R16).
- The map keys change from one key to four keys. Existing tests call `_run_radon` only (R16). The new guard tests read the keys.
