### SSH command CSV error handling

- **Fixed**: The SSH command CSV loader preserves its empty fallback for file access, Unicode decoding, and CSV parser failures.
  Logs name the exception type without raw exception text. Programming errors now propagate. Issue #1794.
