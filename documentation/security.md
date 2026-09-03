# Security and Safety

MistHelper reaches production networks and holds a live cloud credential. These
practices keep both safe.

| Area | Practice |
|------|---------|
| Credentials | Loaded from `.env`, never logged in cleartext |
| Destructive operations | Uppercase warnings, and an explicit typed confirmation |
| File output | Filenames sanitized, and path traversal blocked in the helpers |
| SSH | The Paramiko host key auto-add stays inside trusted internal contexts |
| Logging | Secrets and tokens excluded, and debug gating prevents noisy output |
| Data integrity | Natural and composite primary keys avoid silent duplication |
| Container TLS | The image verifies every certificate. A corporate proxy needs a mounted root certificate, and not a disabled check. |

## Destructive operations

An operation that the registry names `destructive` changes the Mist cloud
configuration. Read [the menu reference](menu_reference.md) for the current
list.

Warning: never script a destructive operation unattended. Each one asks for a
typed confirmation from a person, and that gate exists because the change
reaches production hardware.

The automated test modes never run a destructive operation. The classifier in
`src/utils/operation_registry.py` fails closed, so an operation that the
registry does not name runs in no automated pass.

## Handle a finding, do not hide it

Fix a security finding at its cause. Add a suppression comment only when the
tool reports a false positive, and state the reason in the comment.

The pipeline runs Bandit, pip-audit, and CodeQL on every pull request. Read
[the quality gates page](quality-gates.md).

## Report a vulnerability

Open a GitHub issue with the `security` label. Do not include a token, a
password, or a customer name in the report.
