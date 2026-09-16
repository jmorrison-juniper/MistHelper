# Junos verified rules

This file records only Junos claims verified during issue #2754. Do not add a
new hardening step unless a source verifies it.

## Root authentication

Source: Juniper `root-authentication` statement page.
Train: the statement was introduced before Junos OS Release 7.4.
URL: https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/statement/root-authentication-edit-system.html

Verified claims:

- The `root-authentication` statement configures authentication methods for the
root-level user named `root`.
- The statement can configure SSH ECDSA, ED25519, or RSA public keys for root
login.
- More than one public key can be configured for root login and user accounts.
- The `encrypted-password` option accepts one encrypted password string.
- The password string must have 1 through 128 characters.
- The required privilege level is `admin-control` to add the statement.
- A downgrade from Junos OS Release 15.1 to 12.3 or earlier can make a
SHA-256-hashed root password fail.

Skill rule: do not give a root password or root key change without the target
Junos train. Check downgrade risk before you advise a password hash change.

## Zeroize

Source: Juniper `request system zeroize` command page.
Train: the command was introduced before Junos OS Release 9.0.
URL: https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/command/request-system-zeroize.html

Verified claims:

- `request system zeroize` removes all configuration information and resets all
key values on the device where the operator runs it.
- On a device with dual Routing Engines, the command broadcasts to all Routing
Engines on that device.
- On supported EX Series or QFX Series Virtual Chassis systems, the command
operates only on the member where the operator runs it.
- The command removes user-created files, including plain-text passwords,
secrets, and private keys.
- The command reboots the device and restores the factory default
configuration.
- After the reboot, management Ethernet access is not available until the
operator uses console access.
- The `media` option scrubs storage media and can take more time than a standard
zeroize.
- The required privilege level is `maintenance`.

Skill rule: treat zeroize as destructive and potentially irreversible. Require
console access, a recovery plan, and typed confirmation before execution.

## Local command help checks

Source: `documentation/Junos show_command_help.json`.
Train: local command help snapshot, exact train not recorded.

Verified local entries:

- `documentation/Junos show_command_help.json:5780` maps `request system zeroize`
to "Erase all data, including configuration and log files".
- `documentation/Junos show_command_help.json:5783` maps
`request system zeroize media` to "Overwrite media".
- `documentation/Junos show_command_help.json:27763` maps
`help topic system root-authentication` to "Root password".

Skill rule: use the local command help to confirm a command name. Do not use it
as the only source for the safety impact of a command.
