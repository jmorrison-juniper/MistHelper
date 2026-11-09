### Preserve gateway address values during export

- **Fixed**: The gateway export keeps each address value from the API. The parser reads a string only after it finds each required field. It sends unexpected errors to the caller. Issue #1794.
