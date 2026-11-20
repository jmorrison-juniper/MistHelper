### Protect labeled authorization values in logs

- Security: Redact complete authorization lines without case sensitivity, including Digest and AWS4 parameters. Keep subsequent diagnostic lines. Refs #4705.
- Fixed: Keep safe exception chains complete when a credential word ends a line. Refs #4704.
