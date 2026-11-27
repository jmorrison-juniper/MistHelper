# Contract: Selection link fixture

This contract describes the method `SpecCommandFixture.link_selection` in `tests/guardrails/test_spec_route_contract.py`. The method is a test fixture. It has no operator-facing output.

## Input

- `link`: a path that does not exist yet. The test places it under `tmp_path`.
- `target`: an existing directory. The test places it under `tmp_path`.

## Order of attempts

1. Write an info log line that names the link and the target.
2. Call `link.symlink_to(target, target_is_directory=True)`.
3. When the call succeeds, write a debug log line and return `symlink`.
4. When the call raises `OSError` with `winerror` 1314, write an info log line.
5. Run `cmd /c mklink /J` with the link path and the target path as arguments. Capture the output and do not use `check`.
6. When `mklink` returns 0, write a debug log line and return `junction`.
7. When `mklink` returns a non-zero code, write an error log line and call `pytest.skip`. The reason states that the symlink privilege and the junction creation both failed. It includes the `mklink` output.
8. For any other `OSError`, write an error log line and raise the same error again.

## Outcomes

| Outcome | Return or effect | Condition | Test |
|---------|------------------|-----------|------|
| Symlink | Returns `symlink` | Symlink creation succeeds | TEST-01 |
| Junction | Returns `junction` | WinError 1314, then `mklink` returns 0 | TEST-02 |
| Skip | Calls `pytest.skip` | WinError 1314, then `mklink` returns non-zero | TEST-03 |
| Error | Raises `OSError` again | Any other `OSError` | TEST-04 |

## Logging

- Each info line names the action before the action runs.
- Each debug line names the result. It prints paths only.
- Each log line uses ASCII characters only.
- No log line prints a token or a secret.

## Limits

- The target must stay inside `tmp_path`.

Warning: a recursive delete that follows a junction removes the files at the junction target. Keep every target inside `tmp_path`.
