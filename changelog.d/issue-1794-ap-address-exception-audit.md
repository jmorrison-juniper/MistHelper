### AP model export address exceptions

- **Fixed**: The AP model site export preserves incomplete and non-string addresses but no longer hides unexpected address parsing errors. Issue #1794.
- **Fixed**: Address transforms use debug messages instead of operator messages. Errors from both address splits remain visible to callers. Issue #1794.
