### Protect exception tracebacks and menu titles in logs

- Security: Redact credential-shaped values in exception tracebacks, including chained exceptions and cached text from earlier handlers. Preserve registered menu titles through typed provenance without exempting matching untrusted text. Refs #4704.
