# Quickstart: Validate Delay Metrics Integrity

## Prerequisites

- Use the current issue #4033 branch.
- Use Python 3.13 or newer.
- Bootstrap the worktree if `.venv` does not exist.
- Use no production credential.

## 1. Add and run the red proof

Add the concurrent-writer test before any source repair.
Use thread events to expose the current direct-write window.

Run only the new test:

```powershell
python -m pytest tests\unit\test_rate_limiting.py -k concurrent_writer -vv
```

Expected result before repair:

- The test fails.
- The captured log contains `File I/O: Failed to read data/delay_metrics.json`.
- The result loses a row or exposes an incomplete row.

Keep the test.
Do not weaken its final assertions after the source repair.

## 2. Implement the persistence repair

Edit only `src/foundation/support/utils/rate_limiting.py`.
Use one process lock around the complete cycle.
Write to a same-directory temporary file.
Use `os.replace` after the complete temporary write.
Clean the temporary path after each failed cycle.

## 3. Run the target tests

```powershell
python -m pytest tests\unit\test_rate_limiting.py
```

Expected result:

- All tests pass.
- Every concurrent row is complete and present.
- The zero-byte case produces one valid row.
- Replacement failure preserves the previous bytes.
- Successful and failed cycles leave no temporary file.

## 4. Run the applicable gates

```powershell
python -m py_compile src\foundation\support\utils\rate_limiting.py
python -m mypy src\foundation\support\utils\rate_limiting.py --config-file pyproject.toml
python -m ruff check .
python -m black --check .
```

Expected result:

- Compile produces no output.
- Mypy reports success.
- Ruff reports that all checks passed.
- Black reports that no file needs a change.

Ruff and Black must examine the full repository tree.

## 5. Verify the implementation manifest

The implementation commit contains only these files:

```text
src/foundation/support/utils/rate_limiting.py
tests/unit/test_rate_limiting.py
changelog.d/issue-4033-menu-56-jsi-failure.md
```

The planning commit can contain only files in this issue specification directory.

## 6. Rebase and push once

Fetch `origin/main`.
Rebase the committed branch before the push.
Repeat the target test, Ruff, and Black after the rebase.

Push exactly once:

```powershell
git push --force-with-lease origin HEAD
```

Do not add the `auto-merge` label.
Do not merge the pull request.

## 7. Verify the draft state after the push

```powershell
gh pr view --json isDraft,state,headRefName,headRefOid,labels,url
git rev-parse HEAD
```

Expected result:

- `isDraft` is `true`.
- `state` is `OPEN`.
- `headRefOid` equals local `HEAD`.
- The label list does not contain `auto-merge`.
