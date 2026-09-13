# Contract: `src/utils/subprocess_runner.py` Helper

**Feature**: `specs/1016-misthelper-suppression-cleanup/`

**Owning Story**: Story 7 / Issue #900

**Date**: 2026-07-13

**Status**: Conditional. Introduced only if the post-audit subprocess call-site count in `MistHelper.py` is ≥ 3 per `research.md` §4.

## Purpose

Centralize the `import subprocess` statement at a single audited entry point so that `B404` (subprocess module import) can be justified in exactly one place, and `B603` (subprocess call without shell review) resolves at every `MistHelper.py` call site because each routes through a validating helper.

## File location and structure

```
src/utils/subprocess_runner.py
```

The file is one of only two permitted `src/` additions in this workflow per FR-012 (the other is `src/utils/misthelper_facade.py`).

## Public entry point

```python
class SubprocessRunner:
    """Centralized, audited subprocess dispatch for MistHelper.py callers."""

    ALLOWED_EXECUTABLES: frozenset[str] = frozenset({
        # populated during Story 7 audit from the actual set MistHelper.py invokes
    })

    @classmethod
    def run(
        cls,
        argv: Sequence[str],
        *,
        timeout: float,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Validate `argv` and dispatch. Raises ValueError on validation failure."""
```

## Input validation contract

Every call to `SubprocessRunner.run(argv, timeout=..., check=...)` MUST validate:

1. `argv` is a non-empty sequence.
2. `argv[0]` is a member of `SubprocessRunner.ALLOWED_EXECUTABLES`.
3. Each element of `argv[1:]` matches a conservative character allow-list (alphanumeric, dash, underscore, dot, slash, colon, equals). Elements containing shell metacharacters (`;`, `&`, `|`, `>`, `<`, backtick, `$`, newline) are rejected with `ValueError`.
4. `timeout` is a positive finite float.
5. `shell=True` is never surfaced to callers; the parameter is not part of the signature.

Validation failure raises `ValueError` with a message that identifies the offending element by index but does NOT log the argument value itself (constitution: secrets never in logs).

## Logging contract

Per constitution Principle VII:

- `logging.info("SubprocessRunner dispatching %s", argv[0])` before invocation.
- `logging.debug("SubprocessRunner completed %s rc=%s", argv[0], result.returncode)` after invocation.
- `logging.error("SubprocessRunner failed %s: %s", argv[0], exc)` on exception, with traceback context.
- Argument values (`argv[1:]`) are NEVER logged, only the executable name and result code.

## Error-handling contract

- `subprocess.TimeoutExpired`: allowed to propagate to caller after `error` log.
- `subprocess.CalledProcessError`: propagates when `check=True`; caller catches and handles.
- `ValueError` from validation: propagates immediately; no subprocess is spawned.

## Consumption pattern

At each `MistHelper.py` call site that previously carried `# nosec`:

```python
# Before (with suppression):
# subprocess.run([...], timeout=30)  # nosec B603

# After (routed through helper):
from src.utils.subprocess_runner import SubprocessRunner
SubprocessRunner.run([...], timeout=30)
```

The `import subprocess` line in `MistHelper.py` is removed (satisfying `B404`).

## Test coverage contract

- Unit tests cover: valid dispatch, allow-list rejection, metacharacter rejection, timeout propagation, empty-argv rejection.
- Coverage ≥ 90% per Story 7 Acceptance Scenario 3.

## Validation checklist (Story 7 PR review)

- [ ] `src/utils/subprocess_runner.py` created (only if threshold met).
- [ ] `SubprocessRunner.ALLOWED_EXECUTABLES` matches the actual set of executables `MistHelper.py` invokes.
- [ ] Every `MistHelper.py` subprocess call site routes through `SubprocessRunner.run(...)`.
- [ ] `import subprocess` removed from `MistHelper.py` (or reduced to the single point required for type-hint imports if any remain).
- [ ] `bandit -r MistHelper.py` reports zero findings.
- [ ] Zero `# nosec` comments remain in `MistHelper.py`.
- [ ] `SubprocessRunner` test coverage ≥ 90%.
- [ ] Constitution Principles VI and VII (inline comments, action logging) satisfied on new lines.
