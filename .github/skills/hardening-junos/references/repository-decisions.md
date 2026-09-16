# Repository decisions

These decisions come from the MistHelper repository. Cite the listed file and
line when you answer.

## Secret handling

- `.github/instructions/coding-standards.instructions.md:165` says to redact
tokens and passwords at the logging boundary.
- `documentation/security.md:8` says MistHelper loads credentials from `.env`
and never logs them in clear text.
- `deploy/.env.example:2` tells the operator to copy the template to `.env`.
- `deploy/.env.example:3` says never to commit the actual `.env` file.
- `.gitignore:5` ignores `.env`, and `.gitignore:9` ignores `.env.*` copies.

Rule: never place a token, password, private key, or customer secret in code,
logs, examples, screenshots, issue text, or a pull request.

## Logging policy

- `.github/copilot-instructions.md:269` requires ASCII log output.
- `.github/instructions/coding-standards.instructions.md:167` requires ASCII log
output for cross-platform use.
- `.github/instructions/coding-standards.instructions.md:229` allows `#nosec`
only for a verified false positive.
- `.github/instructions/coding-standards.instructions.md:234` forbids a
suppression that hides a real finding.

Rule: fix a security finding at its cause. Use a suppression only when the tool
is wrong, and write the reason near the suppression.

## Typed confirmation

- `.github/instructions/coding-standards.instructions.md:109` requires explicit
typed confirmation for destructive operations.
- `documentation/security.md:9` states the same destructive-operation practice.
- `documentation/security.md:18` warns against unattended destructive scripts.

Rule: require a typed confirmation when an action can erase data, change
configuration, restart a device, or interrupt traffic.

## Destructive menu classification

The current registry marks these menu entries as destructive:

- `src/utils/operation_registry.py:180` marks menu 154 as an AP firmware
upgrade.
- `src/utils/operation_registry.py:529` through `src/utils/operation_registry.py:532`
mark menu 189, 190, 191, and 194 as destructive ticket and template writes.
- `src/utils/operation_registry.py:533` through `src/utils/operation_registry.py:550`
mark menu 206, 207, and 208 as destructive synthetic-probe and device-profile
changes.
- `.github/copilot-instructions.md:830` requires explicit human review for
menu 154 through 187, 189 through 191, 194, and 206 through 208.

Rule: read the current operation registry before you decide that a menu entry is
safe for automation.

## SSH path

- `.github/copilot-instructions.md:414` says the SSH container uses
`ForceCommand` for direct MistHelper launch and no shell access.
- `Dockerfile:47` writes the `ForceCommand /usr/local/bin/misthelper-session`
configuration.
- `Dockerfile:144` exposes port 2200 for SSH and web and telemetry ports for
other services.
- `src/ssh/ssh_runner_manager.py:143` through `src/ssh/ssh_runner_manager.py:147`
show the target hosts, username, and command count, but not the password.

Rule: show the operator the target and command count before an SSH run. Do not
show or log the password.

## ZTP password path

- `src/device/_utility_commands_action.py:43` defines the warning shown before
the live credential.
- `src/device/_utility_commands_action.py:259` identifies menu 144 as the ZTP
password path.
- `src/device/_utility_commands_action.py:286` through `src/device/_utility_commands_action.py:290`
check whether stdout is a live terminal.
- `src/device/_utility_commands_action.py:311` says the credential print method
must never call the logging module.
- `src/device/_utility_commands_action.py:332` through `src/device/_utility_commands_action.py:335`
print the withheld notice and the safe ways to view the value.
- `src/device/_utility_commands_action.py:346` and `src/device/_utility_commands_action.py:351`
log only the terminal decision.

Rule: a ZTP credential can appear on a live terminal only. A stored stream must
receive a withheld notice.
