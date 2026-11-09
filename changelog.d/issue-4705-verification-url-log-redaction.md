### Verification URL log protection

- Security: Extend the shared filter for #4705 to remove email verification URL values from protected log messages and exception reports.
- Changed: Preserve unrelated URLs and safe diagnostic context. Direct console output and unlabeled response details require separate repairs.
