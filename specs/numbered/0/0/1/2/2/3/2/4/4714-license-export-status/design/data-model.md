# License export states

The repair adds no persistent model or schema.

| State | Input | Result |
|-------|-------|--------|
| Request failed | Non-success status | Runtime error, no data processing or write |
| Request unverified | Missing or malformed status | Runtime error, no data processing or write |
| Empty result | Successful response without records | No write and no file creation claim |
| Write rejected | Valid records and writer `False` | Error log, no success message |
| Write accepted | Valid records and writer success | Record count message |
| Canceled | Operator selection interrupt | Existing exception propagation |

Both endpoint branches use the same initial-response status rule.
