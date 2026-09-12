# Contract: `echo()` Helper

**Module**: `src/utils/console.py`
**Feature**: `1031-warning-echo-refactor`

## Signature

```python
def echo(msg: str, *args: object) -> None: ...
```

## Semantics

For every call `echo(msg, *args)`:

1. **stdout effect**. The helper writes `msg % args if args else msg` to `sys.stdout`, followed by a single newline (via `print(...)`). The write must be equivalent, byte for byte, to what `logging.warning(msg, *args)` produced through the pre-refactor console handler for the same `(msg, args)`.
2. **log effect**. The helper calls `_LOGGER.info(msg, *args)` on the module logger `_LOGGER = logging.getLogger(__name__)`. Formatting is deferred to the `logging` layer per constitution principle VII.
3. **no other effect**. The helper never touches handler configuration. It never writes to stderr. It never emits at `WARNING`, `ERROR`, or `CRITICAL`. It never raises for any `(msg, args)` that the legacy `logging.warning(msg, *args)` would have accepted.

## Contract clauses (Given / When / Then)

### C-1: plain literal, no args

- **Given** `echo("Menu")` is called.
- **When** the call returns.
- **Then** `sys.stdout` has received exactly `"Menu\n"`.
- **And** exactly one log record has been emitted at level `INFO` on `logging.getLogger("src.utils.console")` (or the resolved `__name__`) with `record.msg == "Menu"` and `record.args in ((), None)`.

### C-2: format string with args

- **Given** `echo("Site %s has %d APs", "hq-london", 42)` is called.
- **When** the call returns.
- **Then** `sys.stdout` has received exactly `"Site hq-london has 42 APs\n"`.
- **And** exactly one log record has been emitted at level `INFO` with `record.msg == "Site %s has %d APs"` and `record.args == ("hq-london", 42)`.
- **And** `record.getMessage() == "Site hq-london has 42 APs"`.

### C-3: literal containing `%` with no args

- **Given** `echo("100% signal")` is called.
- **When** the call returns.
- **Then** no exception is raised.
- **And** `sys.stdout` has received exactly `"100% signal\n"` (the literal `%` is preserved, not interpreted as a format specifier).
- **And** exactly one log record has been emitted at level `INFO` with `record.msg == "100% signal"` and `record.args in ((), None)`.

### C-4: never emits at WARNING

- **Given** any sequence of `echo(...)` calls is made.
- **When** all calls return.
- **Then** for every log record emitted by `src.utils.console`, `record.levelno == logging.INFO`. No record is at `WARNING`, `ERROR`, or `CRITICAL`.

### C-5: multiple calls do not attach handlers

- **Given** the `console` module has been imported and `echo(...)` has been called any number of times.
- **When** an observer inspects `logging.getLogger("src.utils.console").handlers`.
- **Then** the handler count is unchanged from the state that existed immediately after the first import of the module (typically zero handlers on the named logger; records propagate to the root logger's handlers).

### C-6: import path is stable

- **Given** any file in the tree wants to use the helper.
- **When** it imports the helper.
- **Then** the import statement is exactly `from src.utils.console import echo`.
- **And** the same import statement works from `MistHelper.py`, from any `src/reports/*.py`, and from any `src/auth/interactive/*.py`.

## Non-contract (out of scope)

- The helper does not accept a `level` argument. It always logs at `INFO`.
- The helper does not accept an `exc_info` argument. If a caller needs to log an exception, they use `logging.error(...)` or `logging.exception(...)` directly, not `echo()`.
- The helper does not accept an `end=` argument. It always terminates with a single newline.
- The helper does not accept a `file=` argument. It always writes to `sys.stdout`.
- The helper does not swallow exceptions from `print()` or from `logger.info()`. If the underlying stdout stream is closed and `print` raises `BrokenPipeError`, the exception propagates. This matches the pre-refactor behavior of `logging.warning` when its stream handler encountered the same fault.

## Verification map (contract clause -> test case)

| Clause | Test file | Test function |
|---|---|---|
| C-1 | `tests/unit/utils/test_console.py` | `test_echo_plain_literal_prints_stdout_and_logs_info` |
| C-2 | `tests/unit/utils/test_console.py` | `test_echo_percent_s_percent_d_formats_stdout_and_log_args` |
| C-3 | `tests/unit/utils/test_console.py` | `test_echo_literal_percent_no_args_does_not_raise` |
| C-4 | `tests/unit/utils/test_console.py` | `test_echo_never_emits_at_warning` |
| C-5 | `tests/unit/utils/test_console.py` | `test_echo_multiple_calls_do_not_duplicate_handlers` |
| C-6 | `tests/unit/utils/test_console.py` (import at top of test file) plus SC-002 grep | implicit — the test file's own import proves the path resolves; the grep in quickstart proves every migrated file uses it. |
