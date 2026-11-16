### Windows audit report portability

- **Fixed**: The writer sets owner-only access through an ACL-capable Windows handle, rejects reparse points, and preserves earlier reports after failed updates. Issue #4771.
