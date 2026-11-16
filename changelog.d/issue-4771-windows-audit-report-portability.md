### Windows audit report portability

- **Fixed**: The writer sets owner-only access through an ACL-capable Windows handle, rejects reparse points, and preserves earlier reports after failed updates. Issue #4771.
- **Added**: A path-filtered Windows workflow runs native helper and writer regressions after relevant feature-branch changes. Issue #4771.
