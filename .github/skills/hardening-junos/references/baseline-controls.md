# Baseline controls

This file holds one entry for each item of the hardening checklist from Juniper. Each entry gives
the control, the Junos statement, the reason, and the evidence command.

The verified snapshot date is 2026-09-16. The file holds 67 controls in 8 sections. The controls
come from the Juniper checklist. The statements come from the hardening book, its sample
configuration, and Junos 26.2 guides.

Warning: do not paste a full baseline into production without a reviewed change window. A wrong
management, authentication, or firewall statement can remove access to the device.

Use `commit confirmed 2` for a remote change that can remove access. The two-minute timer
rolls back the candidate configuration if the management session dies. Confirm access through
the management path, then run `commit` before the timer expires.

## Contents

1. [Administrative](#1-administrative)
2. [Physical Security](#2-physical-security)
3. [Network Security](#3-network-security)
4. [Management Services Security](#4-management-services-security)
5. [Access Security](#5-access-security)
6. [User Authentication Security](#6-user-authentication-security)
7. [Routing Protocol Security](#7-routing-protocol-security)
8. [Firewall Filter](#8-firewall-filter)
9. [Repository security decisions](#repository-security-decisions)
10. [Verified Junos rules](#verified-junos-rules)
11. [Sources](#sources)

## 1. Administrative

Sources: Hardening Junos Devices Checklist, This Week: Hardening Junos Devices, Second Edition,
Junos OS Installation and Upgrade Guide, and Junos OS Release Notes 26.2R1.

| ID | Control | Why it matters | Junos statement | Verify |
| - | - | - | - | - |
| ADM-01 | Read Juniper Security Advisories before you approve the baseline. | Advisories identify a known vulnerability and the fixed release. | No configuration statement exists. Use the Juniper Security Advisories page and the release notes. | `show version` and `show system license` |
| ADM-02 | Install the Junos release that Juniper recommends for the platform. | A supported release receives security fixes and upgrade guidance. | `request system software add <package> validate` | `show version` and `file checksum sha1 <package>` |

## 2. Physical Security

Sources: Hardening Junos Devices Checklist, This Week: Hardening Junos Devices, Second Edition,
Junos OS Chassis-Level User Guide, and Junos OS Ethernet Switching User Guide.

| ID | Control | Why it matters | Junos statement | Verify |
| - | - | - | - | - |
| PHY-01 | If you redeploy a device, reinstall the media before reuse. | A reinstall removes the prior configuration and stored data. | Use the platform installation procedure for a media install. | `show system storage` and `show version` |
| PHY-02 | Disable each unused network port. | A disabled port blocks an unapproved physical connection. | `set interfaces <interface> disable` | `show interfaces terse <interface>` |
| PHY-03 | Configure the console session to close when the cable disconnects. | A closed console session prevents the next user from inheriting access. | `set system ports console log-out-on-disconnect` | `show configuration system ports console` |
| PHY-04 | Configure the console port as insecure after you create a local administrator. | The setting blocks root from direct console sign-in and protects recovery mode. | `set system ports console insecure` | `show configuration system ports console` |
| PHY-05 | Disable the auxiliary port when the platform has one. | An unused auxiliary port can become an unmonitored access path. | `set system ports auxiliary disable` | `show configuration system ports auxiliary` |
| PHY-06 | Configure the auxiliary port as insecure when the platform supports it. | The setting blocks root access through an auxiliary path. | `set system ports auxiliary insecure` | `show configuration system ports auxiliary` |
| PHY-07 | Protect diagnostic ports with a password or disable their password value. | A protected diagnostic port reduces unauthorized service access. | `set system diag-port-authentication plain-text-password` and `set system pic-console-authentication plain-text-password` | `show configuration system | match "diag-port-authentication|pic-console-authentication"` |
| PHY-08 | Disable unneeded craft interface and LCD functions. | A front-panel control can change hardware state or load a rescue configuration. | `set chassis craft-lockout`, `set chassis config-button no-clear`, or `set chassis config-button no-rescue` | `show configuration chassis | match "craft-lockout|config-button"` |

Caution: configure `system ports console insecure` only after you confirm a local administrator.
If you lose the root password, recovery can require a reinstall that deletes the configuration.

## 3. Network Security

Sources: Hardening Junos Devices Checklist, This Week: Hardening Junos Devices, Second Edition,
Junos OS ICMP Router Discovery Protocol User Guide, Junos OS Neighbor Discovery User Guide, and
Junos OS Denial-of-Service Protection User Guide.

Warning: do not change the active management interface address without a second tested path and
`commit confirmed 2`. You can lose all remote access and need console access.

| ID | Control | Why it matters | Junos statement | Verify |
| - | - | - | - | - |
| NET-01 | Use the out-of-band interface for management traffic. | A separate management path keeps device access away from transit traffic. | Configure `fxp0`, `em0`, or `me0` for management, then apply management services there only. | `show interfaces terse fxp0`, `show interfaces terse em0`, or `show interfaces terse me0` |
| NET-02 | Enable default address selection. | The router uses a stable address for traffic that the routing engine starts. | `set system default-address-selection` | `show configuration system default-address-selection` |
| NET-03 | Set a source address for routing-engine traffic. | A fixed source address lets filters and servers identify the device. | `set system syslog source-address <address>` and `set system ntp source-address <address>` | `show configuration system | match source-address` |
| NET-04 | Disable ICMP redirects unless a design requires them. | Redirects can influence host path selection and hide a path change. | `set system no-redirects` | `show configuration system no-redirects` |
| NET-05 | Do not configure source routing. | Source routing lets a sender choose a path around policy controls. | Remove any `source-route` statement from the affected family. | `show configuration | display set | match source-route` |
| NET-06 | Do not configure IP directed broadcast. | Directed broadcast can amplify traffic toward a subnet. | Remove any `directed-broadcast` statement from the affected interface. | `show configuration interfaces | display set | match directed-broadcast` |
| NET-07 | Restrict proxy ARP to the interfaces that need it. | Broad proxy ARP can answer for unintended addresses. | `set interfaces <interface> unit <unit> proxy-arp restricted` | `show configuration interfaces <interface> | match proxy-arp` |
| NET-08 | Drop TCP packets that have both SYN and FIN set. | The abnormal flag pair often indicates a scan or evasion attempt. | `set system internet-options tcp-drop-synfin-set` (source: This Week: Hardening Junos Devices, Second Edition) | `show configuration system internet-options | match tcp-drop-synfin-set` |
| NET-09 | Discard ICMP timestamp and record-route requests. | These messages can expose device time and path information. | `set system no-ping-record-route` and `set system no-ping-time-stamp` (source: Junos OS User Access Management Guide) | `show configuration system | match "no-ping-record-route|no-ping-time-stamp"` |
| NET-10 | Discard ICMP source quench messages. | Source quench is obsolete and can influence traffic behavior. | `set system internet-options no-source-quench` (source: m-mx-series and nsm-j-series-srx-series-swguide) | `show configuration system internet-options | match no-source-quench` |
| NET-11 | Enable LLDP only on required network ports. | LLDP exposes neighbor and platform data to the connected segment. | `set protocols lldp interface <interface>` and remove unused LLDP interfaces. | `show lldp neighbors` and `show configuration protocols lldp` |

## 4. Management Services Security

Sources: Hardening Junos Devices Checklist, This Week: Hardening Junos Devices, Second Edition,
Junos OS Network Management and Monitoring Guide, Junos OS Time Management Guide, and Junos OS
System Log Messages Reference.

| ID | Control | Why it matters | Junos statement | Verify |
| - | - | - | - | - |
| MGT-01 | Configure NTP authentication with more than one trusted server. | Authenticated time keeps logs reliable and rejects a false time source. | `set system ntp authentication-key <id> type md5 value <secret>`, `set system ntp trusted-key <id>`, and `set system ntp server <address> key <id>` | `show ntp associations` and `show configuration system ntp` |
| MGT-02 | Configure SNMP with the most secure method that the manager supports. | SNMPv3 can authenticate and encrypt management traffic. | `set snmp v3 usm local-engine user <user> authentication-sha authentication-password <secret>` | `show snmp v3` and `show configuration snmp v3` |
| MGT-03 | Use strong SNMP community strings and USM passwords. | Weak secrets let an attacker read or alter management data. | `set snmp community <string> authorization read-only` or the matching SNMPv3 USM statement. | `show configuration snmp | display set` |
| MGT-04 | Configure read-only SNMP unless read-write access has approval. | Read-only access limits the effect of a leaked SNMP secret. | `set snmp community <string> authorization read-only` | `show configuration snmp | match authorization` |
| MGT-05 | Allow SNMP queries and traps only to trusted management servers. | Server limits reduce the source set that can read data or receive traps. | `set snmp community <string> clients <address>` and `set snmp trap-group <group> targets <address>` | `show configuration snmp | match "clients|targets"` |
| MGT-06 | Send syslog messages to more than one trusted server with precise timestamps. | Remote logs preserve evidence when the device fails or an attacker deletes local logs. | `set system syslog host <address> any info` and `set system syslog time-format millisecond` | `show log messages` and `show configuration system syslog` |
| MGT-07 | Configure secure automatic configuration backups to more than one trusted server. | A current backup makes recovery faster after error or device loss. | `set system archival configuration transfer-on-commit` and `set system archival configuration archive-sites "scp://<user>@<host>/<path>"` | `show configuration system archival` |

## 5. Access Security

Sources: Hardening Junos Devices Checklist, This Week: Hardening Junos Devices, Second Edition,
Junos OS User Access and Authentication Guide, Junos OS CLI User Guide, and Junos OS NETCONF XML
Management Protocol Guide.

### Safe order for remote access changes

Use this order for ACC-02 and each access service change that can remove the current session.

1. Configure SSH with `set system services ssh`.
2. Commit the SSH configuration with `commit`.
3. Open a second SSH session, and confirm that sign-in works. Keep the first session open.
4. Disable Telnet only after the SSH test succeeds.
5. Commit the Telnet change with `commit confirmed 2`. The two-minute timer rolls back the
   candidate configuration if the management session dies.

Warning: do not disable Telnet on a remote device until a second SSH session works. You can lose
all remote access and need console access.

| ID | Control | Why it matters | Junos statement | Verify |
| - | - | - | - | - |
| ACC-01 | Configure a login warning banner. | A banner states authorized use before authentication. | `set system login message "<approved warning text>"` | `show configuration system login message` |
| ACC-02 | Disable insecure or unnecessary access services. | Unused services expand the management surface. | Remove `set system services telnet`, `set system services ftp`, and `set system services web-management http`. | `show configuration system services` |
| ACC-03 | Enable SSH for required remote access. | SSH protects CLI access better than Telnet. | `set system services ssh` | `show configuration system services ssh` |
| ACC-04 | Use SSH protocol version 2. | Version 2 removes older SSH protocol weaknesses. | `set system services ssh protocol-version v2` | `show configuration system services ssh protocol-version` |
| ACC-05 | Deny root sign-in through SSH. | Named administrator accounts give better accountability than root access. | `set system services ssh root-login deny` | `show configuration system services ssh root-login` |
| ACC-06 | Set SSH connection limits and rate limits. | Limits reduce brute-force attempts and protect the routing engine. | `set system services ssh connection-limit <count>` and `set system services ssh rate-limit <count>` | `show configuration system services ssh | match limit` |
| ACC-07 | Use HTTPS with a valid certificate for J-Web. | HTTPS protects browser management traffic. | `set system services web-management https system-generated-certificate` or use a trusted certificate. | `show configuration system services web-management` |
| ACC-08 | Limit J-Web access to authorized interfaces. | Interface limits keep browser access off untrusted networks. | `set system services web-management https interface <interface>` | `show configuration system services web-management https` |
| ACC-09 | Set idle and session limits for J-Web. | Limits close stale browser sessions and reduce resource use. | `set system services web-management session idle-timeout <minutes>` and `set system services web-management session session-limit <count>` | `show configuration system services web-management session` |

## 6. User Authentication Security

Sources: Hardening Junos Devices Checklist, This Week: Hardening Junos Devices, Second Edition,
Junos OS User Access and Authentication Guide, Junos OS Network Access and Authentication Guide,
and Junos OS Public Key Infrastructure User Guide.

| ID | Control | Why it matters | Junos statement | Verify |
| - | - | - | - | - |
| UAS-01 | Configure a password complexity policy. | Complexity makes password guessing more difficult. | `set system login password minimum-length <number>` and the approved character-class statements. | `show configuration system login password` |
| UAS-02 | Set minimum length and required character classes. | A length and class rule blocks short or simple passwords. | `set system login password minimum-length 12`, `set system login password minimum-upper-cases 1`, `set system login password minimum-lower-cases 1`, and `set system login password minimum-punctuations 1` | `show configuration system login password` |
| UAS-03 | Use SHA-1 or a stronger supported format for local password storage. | A stored hash protects the password value in the configuration. | `set system login password format sha1` when the platform uses that statement. | `show configuration system login password format` |
| UAS-04 | Configure the root account with a strong password. | The root account controls recovery and system-level access. | `set system root-authentication plain-text-password` | `show configuration system root-authentication` |
| UAS-05 | Configure login security options to hinder guessing attacks. | Retry and lockout controls slow repeated password attempts. | `set system login retry-options tries-before-disconnect <count>` and `set system login retry-options backoff-threshold <count>` | `show configuration system login retry-options` |
| UAS-06 | Create custom login classes for different access levels. | A class gives each role only the permissions that it needs. | `set system login class <class> permissions [ <permissions> ]` | `show configuration system login class` |
| UAS-07 | Restrict commands by job function. | Command limits reduce the effect of a compromised account. | `set system login class <class> allow-commands "<regex>"` and `set system login class <class> deny-commands "<regex>"` | `show configuration system login class <class>` |
| UAS-08 | Set idle timeout values for all login classes. | Idle limits close abandoned CLI sessions. | `set system login class <class> idle-timeout <minutes>` | `show configuration system login class | match idle-timeout` |
| UAS-09 | Limit access to secret data in the configuration. | Secret data can include password hashes, SNMP secrets, and shared keys. | Use a class with limited permissions and avoid `secret` permission unless approved. | `show configuration system login class` |
| UAS-10 | Use a strong shared secret for centralized authentication. | A weak shared secret can let a false server or client join the exchange. | `set system radius-server <address> secret <secret>` or `set system tacplus-server <address> secret <secret>` | `show configuration system radius-server` or `show configuration system tacplus-server` |
| UAS-11 | Configure more than one centralized authentication server. | A second server preserves sign-in when one server fails. | `set system radius-server <address>` or `set system tacplus-server <address>` for each server. | `show configuration system | match "radius-server|tacplus-server"` |
| UAS-12 | Configure accounting for administrator activity. | Accounting creates a record of who used the device and when. | `set system accounting events login` and `set system accounting destination radius server <address>` | `show configuration system accounting` |
| UAS-13 | Create an emergency local administrator account. | A local account preserves access when centralized authentication fails. | `set system login user <user> class super-user authentication plain-text-password` | `show configuration system login user <user>` |
| UAS-14 | Know the origin and purpose of all local accounts. | Unknown accounts can indicate drift or unauthorized access. | No single statement exists. Review `system login user` and remove unapproved users. | `show configuration system login user` |
| UAS-15 | Limit local accounts to required users. | Fewer accounts reduce the number of credentials to protect. | Delete unapproved users with `delete system login user <user>`. | `show configuration system login user` |
| UAS-16 | Use a strong password for each local account. | Strong local passwords protect the backup access path. | `set system login user <user> authentication plain-text-password` | `show configuration system login user <user>` |
| UAS-17 | Set the authentication order to match the access policy. | The order controls when Junos uses local or centralized authentication. | `set system authentication-order [ radius password ]` or `set system authentication-order [ tacplus password ]` | `show configuration system authentication-order` |

Caution: keep one tested local administrator before you change centralized authentication. If all
remote servers fail and no local account works, an operator needs console access.

## 7. Routing Protocol Security

Sources: Hardening Junos Devices Checklist, This Week: Hardening Junos Devices, Second Edition,
Junos OS BGP User Guide, Junos OS OSPF User Guide, Junos OS IS-IS User Guide, and Junos OS Routing
Policies User Guide.

| ID | Control | Why it matters | Junos statement | Verify |
| - | - | - | - | - |
| RPS-01 | Configure routing protocols only on required interfaces. | Fewer protocol interfaces reduce unwanted neighbors and route injection. | Remove unneeded `set protocols <protocol> interface <interface>` statements. | `show configuration protocols | display set | match interface` |
| RPS-02 | Source BGP communication from a loopback interface. | A loopback source remains stable across physical link changes. | `set protocols bgp group <group> local-address <loopback-address>` | `show bgp summary` and `show configuration protocols bgp` |
| RPS-03 | Configure route authentication with internal and external trusted neighbors. | Authentication helps reject a false routing peer. | `set protocols bgp group <group> authentication-key <secret>` or the protocol-specific key-chain statement. | `show configuration protocols | match authentication` |
| RPS-04 | Select the strongest authentication algorithm that all peers support. | A stronger algorithm gives better protection for protocol messages. | `set security authentication-key-chains key-chain <name> key <id> algorithm <algorithm>` | `show configuration security authentication-key-chains` |
| RPS-05 | Use strong authentication keys. | Strong keys reduce the chance of neighbor impersonation. | Configure the key with the protocol or key-chain statement that the platform supports. | `show configuration protocols | display set | match authentication` |
| RPS-06 | Use separate authentication keys for different organizations. | Separate keys limit exposure if one neighbor loses a secret. | Configure one key chain or protocol key per organization or peer group. | `show configuration security authentication-key-chains` |
| RPS-07 | Change route authentication keys on the approved schedule. | Rotation limits the useful life of an exposed key. | Use key-chain key start times when the protocol supports hitless rollover. | `show configuration security authentication-key-chains` |

## 8. Firewall Filter

Sources: Hardening Junos Devices Checklist, This Week: Hardening Junos Devices, Second Edition,
Junos OS Routing Policies, Firewall Filters, and Traffic Policers User Guide, Junos OS
Denial-of-Service Protection User Guide, and Junos OS Class of Service User Guide.

| ID | Control | Why it matters | Junos statement | Verify |
| - | - | - | - | - |
| FWF-01 | Protect the routing engine with a default-deny firewall filter. | A filter on `lo0` limits traffic that reaches the control plane. | `set interfaces lo0 unit 0 family inet filter input protect-re` and `set firewall family inet filter protect-re term default-deny then discard` | `show configuration interfaces lo0` and `show firewall filter protect-re` |
| FWF-02 | Put time-sensitive protocol terms near the top of the filter. | Early terms reduce delay for routing, NTP, and other required control traffic. | Place terms such as `allow-bgp`, `allow-ospf`, and `allow-ntp` before broad terms. | `show configuration firewall family inet filter protect-re` |
| FWF-03 | Permit only required protocols from authorized sources. | Source limits block unapproved management and routing traffic. | `set firewall family inet filter protect-re term allow-ssh from source-prefix-list mgmt-nets` and the matching protocol term. | `show configuration firewall family inet filter protect-re` |
| FWF-04 | Rate-limit SYN packets to protect against a SYN flood. | A policer limits control-plane load from repeated connection attempts. | `set firewall family inet filter protect-re term synflood-protect then policer limit-10m` | `show firewall filter protect-re` and `show policer` |
| FWF-05 | Rate-limit authorized protocols with policers. | Policing protects the routing engine even for allowed traffic. | `set firewall family inet filter protect-re term allow-snmp then policer limit-1m` | `show firewall filter protect-re` and `show policer` |
| FWF-06 | Add syslog to the final default-deny term. | Logging denied traffic helps the operator find missing terms and scans. | `set firewall family inet filter protect-re term default-deny then syslog` | `show log messages | match protect-re` and `show firewall log` |

Warning: do not apply a default-deny routing-engine filter remotely until required permit terms
exist and a second session proves access. Use `commit confirmed 2`. A missing term can remove all
remote access and require console access.

Warning: test FWF-03 source limits with `commit confirmed 2` before you make them permanent. A
wrong prefix list can block SSH, SNMP, NTP, or routing adjacencies.

## Repository security decisions

These decisions come from MistHelper repository sources. Cite the listed file and line when you answer.

### Secret handling

- `.github/instructions/coding-standards.instructions.md:165` says to redact tokens and passwords at the logging boundary.
- `documentation/security.md:8` says MistHelper loads credentials from `.env` and never logs them in clear text.
- `deploy/.env.example:2` tells the operator to copy the template to `.env`.
- `deploy/.env.example:3` says never to commit the actual `.env` file.
- `.gitignore:5` ignores `.env`, and `.gitignore:9` ignores `.env.*` copies.

Rule: never place a token, password, private key, or customer secret in code, logs, examples, screenshots, issue text, or a pull request.

### Logging policy

- `.github/copilot-instructions.md:269` requires ASCII log output.
- `.github/instructions/coding-standards.instructions.md:167` requires ASCII log output for cross-platform use.
- `.github/instructions/coding-standards.instructions.md:229` allows `#nosec` only for a verified false positive.
- `.github/instructions/coding-standards.instructions.md:234` forbids a suppression that hides a real finding.

Rule: fix a security finding at its cause. Use a suppression only when the tool is wrong, and write the reason near the suppression.

### Typed confirmation

- `.github/instructions/coding-standards.instructions.md:109` requires explicit typed confirmation for destructive operations.
- `documentation/security.md:9` states the same practice for a destructive operation.
- `documentation/security.md:18` warns against an unattended destructive script.

Rule: require a typed confirmation when an action can erase data, change configuration, restart a device, or interrupt traffic.

### Destructive menu classification

The current registry marks these menu entries as destructive.

- `src/utils/operation_registry.py:180` marks menu 154 as an AP firmware upgrade.
- `src/utils/operation_registry.py:529` through `src/utils/operation_registry.py:532` mark menu 189, 190, 191, and 194 as destructive ticket and template writes.
- `src/utils/operation_registry.py:533` through `src/utils/operation_registry.py:550` mark menu 206, 207, and 208 as destructive synthetic-probe and device-profile changes.
- `.github/copilot-instructions.md:830` requires explicit human review for menu 154 through 187, 189 through 191, 194, and 206 through 208.

Rule: read the current operation registry before you decide that a menu entry is safe for automation.

### SSH path

- `.github/copilot-instructions.md:414` says the SSH container uses `ForceCommand` for direct MistHelper launch and no shell access.
- `Dockerfile:47` writes the `ForceCommand /usr/local/bin/misthelper-session` configuration.
- `Dockerfile:144` exposes port 2200 for SSH and web and telemetry ports for other services.
- `src/ssh/ssh_runner_manager.py:143` through `src/ssh/ssh_runner_manager.py:147` show the target hosts, username, and command count, but not the password.

Rule: show the operator the target and command count before an SSH run. Do not show or log the password.

### ZTP password path

- `src/device/_utility_commands_action.py:43` defines the warning shown before the live credential.
- `src/device/_utility_commands_action.py:259` identifies menu 144 as the ZTP password path.
- `src/device/_utility_commands_action.py:286` through `src/device/_utility_commands_action.py:290` check whether stdout is a live terminal.
- `src/device/_utility_commands_action.py:311` says the credential print method must never call the logging module.
- `src/device/_utility_commands_action.py:332` through `src/device/_utility_commands_action.py:335` print the withheld notice and the safe ways to view the value.
- `src/device/_utility_commands_action.py:346` and `src/device/_utility_commands_action.py:351` log only the terminal decision.

Rule: a ZTP credential can appear on a live terminal only. A stored stream must receive a withheld notice.

## Verified Junos rules

This section records only Junos claims verified during issue #2754. Do not add a new hardening step unless a source verifies it.

### Root authentication

Source: Juniper `root-authentication` statement page.
Train: the statement was introduced before Junos OS Release 7.4.
URL: https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/statement/root-authentication-edit-system.html

Verified claims:

- The `root-authentication` statement configures authentication methods for the root-level user named `root`.
- The statement can configure SSH ECDSA, ED25519, or RSA public keys for root login.
- More than one public key can be configured for root login and user accounts.
- The `encrypted-password` option accepts one encrypted password string.
- The password string must have 1 through 128 characters.
- The required privilege level is `admin-control` to add the statement.
- A downgrade from Junos OS Release 15.1 to 12.3 or earlier can make a SHA-256-hashed root password fail.

Skill rule: do not give a root password or root key change without the target Junos train. Check downgrade risk before you advise a password hash change.

### Zeroize

Source: Juniper `request system zeroize` command page.
Train: the command was introduced before Junos OS Release 9.0.
URL: https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/command/request-system-zeroize.html

Verified claims:

- `request system zeroize` removes all configuration information and resets all key values on the device where the operator runs it.
- On a device with dual Routing Engines, the command broadcasts to all Routing Engines on that device.
- On supported EX Series or QFX Series Virtual Chassis systems, the command operates only on the member where the operator runs it.
- The command removes user-created files, including plain-text passwords, secrets, and private keys.
- The command reboots the device and restores the factory default configuration.
- After the reboot, management Ethernet access is not available until the operator uses console access.
- The `media` option scrubs storage media and can take more time than a standard zeroize.
- The required privilege level is `maintenance`.

Skill rule: treat zeroize as destructive and potentially irreversible. Require console access, a recovery plan, and typed confirmation before execution.

### Local command help checks

Source: `documentation/Junos show_command_help.json`.
Train: local command help snapshot, exact train not recorded.

Verified local entries:

- `documentation/Junos show_command_help.json:5780` maps `request system zeroize` to "Erase all data, including configuration and log files".
- `documentation/Junos show_command_help.json:5783` maps `request system zeroize media` to "Overwrite media".
- `documentation/Junos show_command_help.json:27763` maps `help topic system root-authentication` to "Root password".

Skill rule: use the local command help to confirm a command name. Do not use it as the only source for the safety impact of a command.

## Sources

The vendor text is not committed. The repository holds this distilled file instead.

| Source | Local copy path below the corpus root | Reason it is not committed | Rebuild command |
| - | - | - | - |
| <https://www.juniper.net/assets/kr/kr/local/pdf/books/tw-hardening-junos-devices-checklist.pdf> | `extracted/TW_HardeningJunosDevices_2ndEd/TW_HardeningJunosDevices_2ndEd_Checklist.pdf` | The file is a vendor PDF. The repository cannot redistribute it. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/dayone> | `extracted/TW_HardeningJunosDevices_2ndEd/TW_HardeningJunosDevices_2ndEd.pdf` | The file is a vendor book. The repository cannot redistribute it. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/junos-install-upgrade.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/junos-os-release-notes-26.2r1.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/chassis.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/interfaces-ethernet-switches.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/icmp.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/neighbor-discovery.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/denial-of-service.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/network-mgmt.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/time-mgmt.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/junos-for-srx-doc-set-pdfs.zip> | `extracted/junos-for-srx-doc-set-pdfs/junos-for-srx-doc-set-pdfs/system-logs.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/user-access.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/cli.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/netconf.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/network-access-protocols.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/pki.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/bgp.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/ospf.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/is-is.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/routing-policy.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |
| <https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip> | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/cos.pdf` | The archive holds vendor PDFs. The repository cannot redistribute them. | `python scripts/pdf_to_markdown.py` |

The staged corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives\`. The Markdown
copies below `markdown/` support fast search only. Trust the body text, not the heading level.
