# Research: Windows Audit Report Portability

## Decision 1: Keep the POSIX safety path

**Decision**: Create report stages with exclusive temporary-file creation on every platform. Keep `fchmod` on POSIX and replace final paths atomically. Do not treat a missing capability as a zero-valued flag.

**Rationale**: Exclusive creation prevents a staging-name collision, and atomic replacement does not follow a final symbolic link. POSIX stages still receive mode `0600`. The issue reports that Windows does not provide the `O_NOFOLLOW` and `fchmod` members used by the prior writer.

**Alternatives considered**: Use `getattr(os, "O_NOFOLLOW", 0)` or skip `fchmod`. Both choices silently weaken the current safety contract.

**Evidence**: `tests/e2e/websockets_tab/dialog_audit/support/reporting.py` stages each report exclusively, applies POSIX mode `0600`, and replaces final paths only after validation.

## Decision 2: Use Windows reparse attributes and protected access controls

**Decision**: On Windows, inspect `st_file_attributes` and reject `FILE_ATTRIBUTE_REPARSE_POINT`. Use a no-follow Windows handle for existing paths and apply a protected owner-only DACL before report data is written.

**Rationale**: A Windows junction or other reparse point can redirect a path without being a POSIX symbolic link. `os.chmod` does not provide the owner-only ACL required by the report contract. Native Windows calls avoid a new Python dependency.

**Alternatives considered**: A path-only `lstat` check has a race before open. `os.chmod` cannot replace ACL enforcement. A missing reparse attribute must fail closed.

**Evidence**: `src/operations/execution/firmware_policy/recovery/backup.py` requires Windows file attributes and verifies ACL ownership and access through a fixed PowerShell query.

## Decision 3: Stage and replace reports only after both writes succeed

**Decision**: Create exclusive temporary files in the approved directory, write both reports, and replace the destinations after both writes complete. Remove staged files on failure and roll back replaced destinations if a commit step fails.

**Rationale**: This avoids truncating earlier reports while the new content is still being written. The same-directory replacement keeps each individual update atomic.

**Alternatives considered**: Truncate each existing file before writing. A failure during the second write can then leave a mixed or incomplete report pair.

**Evidence**: `AuditReportWriter.write` currently truncates each destination in sequence.

## Decision 4: Run native Windows checks from a feature-branch push

**Decision**: Add a separate optional workflow that runs the real helper and writer tests on `windows-latest` after a non-main branch push that changes a listed test input. Require two collected tests, zero skips, and zero failures.

**Rationale**: This workflow file can run from the pushed branch before it exists on the default branch. A narrow path filter avoids runs for unrelated changes. The separate job can test native APIs without changing the required CI workflow or status names.

**Alternatives considered**: A manual dispatch requires the workflow file on the default branch. A simulated Windows test cannot prove that `CreateFileW` grants the rights needed by the real ACL update.

**Evidence**: GitHub documents that a push event can run an unmerged workflow file in the pushed commit. See [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## Decision 5: Request READ_CONTROL and verify the DACL through the same handle

**Decision**: Keep `SetSecurityInfo` with `PROTECTED_DACL_SECURITY_INFORMATION` and `DACL_SECURITY_INFORMATION` on the verified handle. Request `READ_CONTROL`, `WRITE_DAC`, and `FILE_READ_ATTRIBUTES` on the directory and staged-file handles. Read the DACL back with `GetSecurityInfo` through the same handle, and fail when `SE_DACL_PROTECTED` or `SE_DACL_PRESENT` is absent.

**Rationale**: Native run 43795918169 failed with Win32 status 5 at `SetSecurityInfo` on a directory handle that had `WRITE_DAC` and `FILE_READ_ATTRIBUTES` only. The hypothesis was that the call also needs `READ_CONTROL` on the handle. Native run 43797470577 passed after the handle added `READ_CONTROL`, so the native evidence supports this hypothesis. The readback makes a silent change fail closed. The extra right is on the writer handle only, and it gives no access to other accounts.

**Alternatives considered**: `SetKernelObjectSecurity` writes a descriptor directly to a handle. Microsoft documentation tells callers to use `SetSecurityInfo` for file-system objects, so this design does not use it.

**Evidence**: The failed log shows the error at `_set_owner_dacl` after `SetSecurityInfo`. The boundary tests model the handle rights and fail against the previous writer. Native run 43797470577 at commit `d51c2790269cdc66c74dcce12b9f5565570f9c5a` reported 2 passed, 0 skipped, and 0 failures on win32 Python 3.15.2.
