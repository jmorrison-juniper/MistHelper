### Device fetch error privacy

- **Security**: Device fetch failures log the exception type without private exception text.
  The existing callback fallback, HTTP refusal result, and output behavior remain unchanged. Issue #1794.
