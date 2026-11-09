### Verification URL log protection

- Security: Extend the shared filter for #4705 to remove email verification URL values from protected log messages and exception reports.
- Changed: Preserve unrelated URLs and safe diagnostic context. Direct console output and unlabeled response details require separate repairs.
- Fixed: Treat punctuation within verification URL values as private. Only whitespace ends the protected suffix.
- Fixed: Preserve ordinary menu titles that contain credential words. Ordinary credential assignments require a colon or equals sign.
