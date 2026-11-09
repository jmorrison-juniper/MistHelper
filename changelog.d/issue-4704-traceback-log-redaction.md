### Protect exception tracebacks in logs

- Security: Redact credential-shaped values in exception tracebacks, including chained exceptions and cached text from earlier handlers. Preserve safe diagnostic context. Refs #4704.
