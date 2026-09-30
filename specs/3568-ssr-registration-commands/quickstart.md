# Quickstart: SSR registration commands

## Manual verification

1. Start MistHelper with an organization token that can read WAN Edge registration commands.
2. Select menu `288` after the integration pull request wires the operation.
3. Confirm that the operation prints the registration commands before it asks any question.
4. Answer `N` at the write prompt and confirm that `data/SsrRegistrationCommands.txt` is not changed.
5. Run menu `288` again.
6. Answer `y` at the write prompt and confirm that `data/SsrRegistrationCommands.txt` contains the command text.
7. Read `data/script.log` and confirm that it contains the file path but no registration code.

## Unit verification

Run this command from the worktree:

```powershell
C:\Users\jmorrison\mh-fleet\3568-ssr-registration-commands\.venv\Scripts\python.exe -m pytest tests\unit\gateway\ssr_registration -q --timeout=120
```
