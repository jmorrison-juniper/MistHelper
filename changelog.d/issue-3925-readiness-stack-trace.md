### Readiness probe hides exception text

- **Security**: The `/ready` endpoint of the web portal now gives only the
  exception class name for a failed check. The full exception text goes to the
  portal log. This closes CodeQL alert 197 (`py/stack-trace-exposure`). Issue
  #3925.
