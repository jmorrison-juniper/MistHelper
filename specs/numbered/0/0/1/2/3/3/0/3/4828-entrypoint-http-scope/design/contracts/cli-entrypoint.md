# Contract: CLI entry point for help and argument parsing

## Scope

This contract covers the arguments that `python MistHelper.py` receives. `MainEntrypoint.run` handles the process arguments (RC-10). The parser inside `ApplicationBootstrap` reads them (RC-08).

## Behavior

The first element of process arguments is the program name. The parser never reads it as a flag (lines 51 to 69 of the help test file).

| Process arguments after the program name | Exit code | Output | Startup reached | Evidence |
| - | - | - | - | - |
| `--help`, `-h`, `--menu 1 --help`, `-h --testinteractive`, `-help`, `--h` | 0 | stdout contains `usage:` | No | Help file, lines 20 to 35 |
| `--helpme`, `help`, `--HELP` | 2 | stderr contains `error:` | No | Help file, lines 37 to 49 |
| `--test-interactive` | 2 | stderr contains `unrecognized arguments` and does not contain `Did you mean` | No | Reject-flag file, lines 128 to 138 |
| None, or `--menu 1`, or `--menu 1 --org abc` | None. The run continues. | Startup helper raises the stub error | Yes | Help file, lines 51 to 69 |
| `--skip-deps` | None. The run continues. | The parser runs once and the stored namespace is reused | Yes | Reject-flag file, lines 105 to 125 |
| `--help` in a fresh process | 0 | stdout contains `usage:` | No. The `data` folder is not created. | Help file, lines 72 to 91 |

## Guarantees

- Help and invalid input stop before `activate_context` runs.
- The command line is parsed once for each invocation.
- Importing `MistHelper` runs no startup side effect. The guarded probe records no event (reject-flag file, lines 19 to 85).

## Not in this contract

- Mist API behavior. This command path makes no API call in the cases above.
- Analyzer behavior. The contract for the test quality gate is in `test-quality-gate.md`.
