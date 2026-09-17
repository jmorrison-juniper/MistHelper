# Software and monitoring operations

Use this reference for software maintenance, show commands, system logs, trace
files, and log archive tasks.

## Source map

| Source | Train | Use |
| - | - | - |
| `Junos OS Software Installation and Upgrade Guide` | 26.2 | Install, validate, snapshot, and software rollback. |
| `Junos OS CLI User Guide for Junos OS` | 26.2 | Operational show command families, log display, and file archive. |
| `System Management and Monitoring User Guide` | 26.2 | Core files, processes, interfaces, and system state counters. |
| `Junos OS Monitoring, Sampling, and Collection Services Interfaces User Guide` | 26.2 | Sampling logs and passive monitoring examples. |

## Software install and upgrade

| Task | Command | Mode | Source |
| - | - | - | - |
| Check available storage. | `show system storage` | Operational | Install guide 26.2. |
| Show current software. | `show version` | Operational | Install guide 26.2. |
| Validate a package only. | `request system software validate /var/tmp/junos-install.tgz` | Operational | Install guide 26.2. |
| Add a software package. | `request system software add /var/tmp/junos-install.tgz` | Operational | Install guide 26.2. |
| Add from a URL. | `request system software add https://server.example.invalid/path/junos-install.tgz` | Operational | Install guide 26.2. |
| Add without copy. | `request system software add no-copy /var/tmp/junos-install.tgz` | Operational | Install guide 26.2. |
| Reboot after install. | `request system reboot` | Operational | Install guide 26.2. |
| Verify the installed release. | `show version` | Operational | Install guide 26.2. |
| Read install messages. | `show log messages | match install` | Operational | Install guide 26.2. |

Warning: a software install can reboot the device. The reboot interrupts traffic
and management access until the device returns.

Run validation before the add command when the platform supports validation. Do
not start an upgrade when storage, alarms, or rescue recovery is unknown.

## Snapshot and image rollback

| Task | Command | Mode | Source |
| - | - | - | - |
| Save a software snapshot. | `request system snapshot` | Operational | Install guide 26.2. |
| Save a snapshot to media. | `request system snapshot media usb` | Operational | Install guide 26.2. |
| Revert to the alternate slice. | `request system software rollback` | Operational | Install guide 26.2. |
| Reboot after software rollback. | `request system reboot` | Operational | Install guide 26.2. |
| Check package state after rollback. | `show version` | Operational | Install guide 26.2. |

Warning: software rollback needs a reboot. The reboot interrupts traffic and
can change the running image.

Take a snapshot only after the new release works. A bad snapshot can overwrite a
good fallback image.

## Show command families

| Need | Command | Source |
| - | - | - |
| Device identity and release. | `show version` | CLI guide 26.2. |
| Chassis inventory. | `show chassis hardware` | CLI guide 26.2. |
| Chassis alarms. | `show chassis alarms` | CLI guide 26.2. |
| System alarms. | `show system alarms` | CLI guide 26.2. |
| Interface summary. | `show interfaces terse` | CLI guide 26.2 and monitoring guide 26.2. |
| Interface detail. | `show interfaces extensive` | Monitoring guide 26.2. |
| Route table. | `show route` | CLI guide 26.2. |
| ARP table. | `show arp` | CLI guide 26.2. |
| Ethernet switching table. | `show ethernet-switching table` | CLI guide 26.2. |
| LLDP neighbors. | `show lldp neighbors` | CLI guide 26.2. |
| System users. | `show system users` | CLI guide 26.2. |
| Recent commits. | `show system commit` | CLI guide 26.2. |
| Processes. | `show system processes extensive` | Monitoring guide 26.2. |
| Core files. | `show system core-dumps` | Monitoring guide 26.2. |

Start with summary commands. Use detail commands only when the summary shows a
fault or a missing value.

## System logs

| Task | Command | Mode | Source |
| - | - | - | - |
| Show the main log. | `show log messages` | Operational | CLI guide 26.2. |
| Show the last 50 messages. | `show log messages | last 50` | Operational | CLI guide 26.2. |
| Search the main log. | `show log messages | match error` | Operational | CLI guide 26.2. |
| Read sampled traffic records. | `show log sampled` | Operational | Flow monitoring guide 26.2. |
| Follow a log file. | `monitor start messages` | Operational | CLI guide 26.2. |
| Stop following a log file. | `monitor stop messages` | Operational | CLI guide 26.2. |
| List log files. | `file list /var/log/` | Operational | CLI guide 26.2. |
| Archive a log file. | `file archive compress source /var/log/messages destination /var/tmp/messages.tgz` | Operational | CLI guide 26.2. |

Do not leave `monitor start` running in an unattended terminal. Stop it before
you close the session.

## Trace files

| Task | Command | Mode | Source |
| - | - | - | - |
| Configure a script trace file. | `set system scripts commit traceoptions file commit-script.log` | Configuration | Automation guide 22.1. |
| Configure sampled trace output. | `set sampling traceoptions file sampled` | Configuration | Flow monitoring guide 26.2. |
| Read a trace file. | `show log commit-script.log` | Operational | Automation guide 22.1. |
| Read the last trace entries. | `show log op-script.log | last 100` | Operational | Automation guide 22.1. |
| Read a NETCONF trace file. | `show log netconf` | Operational | NETCONF guide 26.2. |
| Read a JET trace file. | `show log jet.log` | Operational | NETCONF guide 26.2. |

Trace files can grow quickly. Set file size and file count in the traceoptions
hierarchy when the source guide provides those options for the feature.

## Maintenance checks before a change window

1. Run `show version`.
2. Run `show chassis alarms`.
3. Run `show system alarms`.
4. Run `show system storage`.
5. Run `show system commit`.
6. Run `request system configuration rescue save` when no current rescue file exists.
7. Copy the package to `/var/tmp/`.
8. Run `request system software validate /var/tmp/junos-install.tgz`.

Warning: do not start an upgrade if alarms, storage, or validation fails. The
failure can leave the device in an unknown state after reboot.
