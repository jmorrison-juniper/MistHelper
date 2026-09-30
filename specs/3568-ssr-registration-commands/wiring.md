# Wiring manifest

## Menu entries
| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 288 | Show the SSR registration commands | src.gateway.ssr_registration.operation | SsrRegistrationCommands.run | interactive_safe | Prompts before writing `data/SsrRegistrationCommands.txt` with `Write registration commands to data/SsrRegistrationCommands.txt? (y/N):` | False | False |

## OperationRegistry comment
One `# WHY:` paragraph: Menu 288 prints SSR registration commands for a NOC engineer who must manually onboard a Session Smart Router. The read is safe and has no prompt, but the optional file write asks y/N because the command text can include a live registration code. Keep the row in `interactive_safe` so `--testinteractive` can skip it with the write-prompt reason.

## Primary key strategies
```python
# No primary key strategy is required. Menu 288 prints command text and optionally writes a local text file. It does not export rows to CSV, SQLite, ArangoDB, or Redis.
```

## copilot-instructions category table
Add menu `288` to the `interactive_safe` category row. Increase that row count by one. Increase the full menu range end if the integration pull request owns the documentation update.

## Import line for MistHelper.py
`from src.gateway.ssr_registration.operation import SsrRegistrationCommands  # Menu 288 (issue #3568) -- show SSR registration commands.`

## Deferred registration call
Bind menu `288` to `SsrRegistrationCommands.run` in the menu dispatcher during the integration pull request.

## Generated documentation
Regenerate the menu reference and API map in the integration pull request after the menu row is wired.
