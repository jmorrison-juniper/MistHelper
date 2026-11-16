### Windows audit report portability

- **Fixed**: The audit report writer saves reports on Windows with owner-only access, rejects reparse points, and preserves earlier reports after a failed update. Issue #4771.
