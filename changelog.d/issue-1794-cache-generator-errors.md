### Cache generator error reporting

- **Fixed**: Cache generation failures report the exception type without exposing callback exception text.
  The filename, generator name, failure return, and interrupt behavior remain unchanged. Issue #1794.
