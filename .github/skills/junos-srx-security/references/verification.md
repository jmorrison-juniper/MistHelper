# Verification

Use this reference to verify sources, commands, writing quality, size, and limits for the `junos-srx-security` skill.

The verified snapshot date is 2026-09-17. The source manifest holds 192 documents and 55,947 pages. This skill indexes 12 documents that cover the SRX security subject.

## 1. Source selection

The source manifest is outside the repository.

```text
C:\Users\jmorrison\Downloads\juniper-doc-archives\skill-manifests\junos-srx-security.json
```

The corpus root is outside the repository.

```text
C:\Users\jmorrison\Downloads\juniper-doc-archives
```

The index uses relative paths below that root. Do not commit vendor documents to the repository.

## 2. Source match rules

Use these rules before you answer.

1. Read `references/corpus-index.csv`.
2. Select the row that matches the feature.
3. Prefer a user guide over a release note.
4. Prefer the newest release when two guides cover the same subject.
5. Join the row `path` to the corpus root.
6. Confirm that the Markdown file exists.
7. Search the file for the command or statement.
8. Cite the title and release from the row.
9. If the command is absent, state that the command is unverified.

Caution: several SRX feature guides in the staged manifest come from the SRX archive and state a modified date instead of a Junos train. Cite the modified date as the release marker.

## 3. Indexed documents

| Topic | Source | Release | Why selected |
| - | - | - | - |
| Zones and policies | Junos OS Security Basics Guide for Security Devices | SRX document set, modified 2017-07-18 | It covers zones, host inbound traffic, policy, global policy, and order. |
| NAT | Junos OS Network Address Translation Feature Guide for Security Devices | SRX document set, modified 2017-08-03 | It covers source, destination, static NAT, and proxy ARP. |
| Screens | Junos OS Attack Detection and Prevention Feature Guide for Security Devices | SRX document set, modified 2017-08-08 | It covers flood, scan, and malformed packet screen options. |
| ALG | Junos OS Application Layer Gateways Feature Guide for Security Devices | SRX document set, modified 2017-07-31 | It covers ALG options and operational checks. |
| Application identification | Junos OS AppSecure Services Feature Guide for Security Devices | SRX document set, modified 2017-09-10 | It covers application identification and application firewall. |
| UTM | Junos OS UTM Feature Guide for Security Devices | SRX document set, modified 2017-09-11 | It covers UTM policy and status commands. |
| IDP | Junos OS Intrusion Detection and Prevention Feature Guide for Security Devices | SRX document set, modified 2017-06-14 | It covers the security package, IDP policy, and active policy. |
| IPsec | Junos OS VPN Feature Guide for Security Devices | SRX document set, modified 2017-08-14 | It covers IKE, IPsec, gateways, VPN, and `st0.0`. |
| Flow | Junos OS Flow-Based and Packet-Based Processing Feature Guide for Security Devices | SRX document set, modified 2017-09-15 | It covers flow status, sessions, and packet path checks. |
| Security Director | Security Director User Guide | 22.3, published 2023-03-09 | It covers policy publish and update. |
| Policy Enforcer | Security Director Policy Enforcer User Guide | 22.2, published 2022-11-23 | It covers policy enforcement groups and updates. |
| Security Intelligence | Juniper SecIntel Administration Guide | 22.3, published 2023-03-09 | It covers feed-backed policy design. |

## 4. Confirmed command families

The references use 79 command families. Each family below maps to a source document in `corpus-index.csv`.

### Zones and policies

- `set security zones security-zone <zone> interfaces <interface>`.
- `set security zones security-zone <zone> interfaces <interface> host-inbound-traffic system-services <service>`.
- `set security zones security-zone <zone> interfaces <interface> host-inbound-traffic protocols <protocol>`.
- `show security zones`.
- `show security zones security-zone <zone>`.
- `show configuration security zones`.
- `set security policies from-zone <zone> to-zone <zone> policy <policy> match source-address <address>`.
- `set security policies from-zone <zone> to-zone <zone> policy <policy> match destination-address <address>`.
- `set security policies from-zone <zone> to-zone <zone> policy <policy> match application <application>`.
- `set security policies from-zone <zone> to-zone <zone> policy <policy> then permit`.
- `set security policies from-zone <zone> to-zone <zone> policy <policy> then deny`.
- `insert security policies from-zone <zone> to-zone <zone> policy <policy> before policy <policy>`.
- `show security policies`.
- `show security policies from-zone <zone> to-zone <zone>`.
- `set security policies global policy <policy> match source-address <address>`.
- `set security policies global policy <policy> match destination-address <address>`.
- `set security policies global policy <policy> match application <application>`.
- `set security policies global policy <policy> match from-zone <zone>`.
- `set security policies global policy <policy> match to-zone <zone>`.
- `set security policies global policy <policy> then permit`.
- `set security policies global policy <policy> then deny`.
- `show security policies global`.
- `show security policies global policy-name <policy>`.
- `set security application-firewall rule-sets <set> rule <rule> match dynamic-application <application>`.
- `set security application-firewall rule-sets <set> rule <rule> match dynamic-application-groups <group>`.
- `set security policies from-zone <zone> to-zone <zone> policy <policy> then permit application-services application-firewall rule-set <set>`.
- `show security flow session application-firewall dynamic-application <application>`.

### NAT and threat services

- `set security nat source rule-set <set> from zone <zone>`.
- `set security nat source rule-set <set> to zone <zone>`.
- `set security nat source rule-set <set> rule <rule> match source-address <prefix>`.
- `set security nat source rule-set <set> rule <rule> match destination-address <prefix>`.
- `set security nat source rule-set <set> rule <rule> then source-nat interface`.
- `show security nat source rule all`.
- `show security nat source pool all`.
- `set security nat destination rule-set <set> from zone <zone>`.
- `set security nat destination rule-set <set> rule <rule> match destination-address <prefix>`.
- `set security nat destination rule-set <set> rule <rule> then destination-nat pool <pool>`.
- `set security nat destination pool <pool> address <prefix>`.
- `show security nat destination rule all`.
- `set security nat static rule-set <set> from zone <zone>`.
- `set security nat static rule-set <set> rule <rule> match destination-address <prefix>`.
- `set security nat static rule-set <set> rule <rule> then static-nat prefix <prefix>`.
- `show security nat static rule all`.
- `set security nat proxy-arp interface <interface> address <prefix>`.
- `set security screen ids-option <screen> icmp ip-sweep threshold <count>`.
- `set security screen ids-option <screen> icmp flood threshold <count>`.
- `set security screen ids-option <screen> icmp ping-death`.
- `set security screen ids-option <screen> ip bad-option`.
- `set security screen ids-option <screen> ip tear-drop`.
- `set security screen ids-option <screen> tcp syn-fin`.
- `set security screen ids-option <screen> tcp tcp-no-flag`.
- `set security screen ids-option <screen> tcp port-scan threshold <count>`.
- `set security screen ids-option <screen> tcp syn-flood alarm-threshold <count>`.
- `set security screen ids-option <screen> tcp syn-flood attack-threshold <count>`.
- `set security screen ids-option <screen> tcp land`.
- `set security screen ids-option <screen> udp flood threshold <count>`.
- `show security screen ids-option <screen>`.
- `show security screen status`.
- `set security zones security-zone <zone> screen <screen>`.
- `set security alg ike-esp-nat enable`.
- `set security alg ike-esp-nat esp-gate-timeout <seconds>`.
- `set security alg ftp ftps-extension`.
- `set security alg sip maximum-call-duration <seconds>`.
- `clear security alg ike-esp-nat`.
- `request services application-identification download`.
- `request services application-identification install`.
- `set services application-identification application <name> over HTTP signature <signature>`.
- `set security utm utm-policy <policy> anti-spam smtp-profile <profile>`.
- `show security utm status`.
- `show security utm session`.
- `set security idp security-package url <url>`.
- `set security idp security-package automatic enable`.
- `set security idp idp-policy <policy> rulebase-ips rule <rule> match from-zone <zone>`.
- `set security idp active-policy <policy>`.
- `show security idp security-package-version`.

### VPN, management, and flow

- `set interfaces st0 unit <unit> family inet address <prefix>`.
- `set routing-options static route <prefix> next-hop st0.0`.
- `set security ike proposal <proposal> authentication-method pre-shared-keys`.
- `set security ike policy <policy> pre-shared-key ascii-text <secret>`.
- `set security ike gateway <gateway> external-interface <interface>`.
- `set security ipsec vpn <vpn> bind-interface st0.0`.
- `set security ipsec vpn <vpn> ike gateway <gateway>`.
- `show security ike security-associations detail`.
- `show security ipsec security-associations`.
- `show security ipsec statistics`.
- `show security ipsec tunnel-events-statistics`.
- `show security flow session`.
- `show security flow session extensive`.
- `show security flow status`.
- `show interfaces flow-statistics`.

## 5. Safety checks

Run these checks before you use a command on a production SRX.

1. Confirm the source document and release in the index.
2. Confirm the current device state with a `show` command.
3. Confirm that the command changes only the intended feature.
4. Use `show | compare` before a commit.
5. Use `commit confirmed` for remote changes.
6. Test traffic with a limited source or destination.
7. Run `commit` only after the test succeeds.

Warning: do not use a configuration command from memory. An incorrect command on a production firewall can permit unwanted traffic or drop valid traffic.

## 6. Offline acceptance checks

Run these checks from the repository root in the platform worktree.

Set the skill path once.

```powershell
$skill = '.github/skills/junos-srx-security'
```

### V1. Writing score

```powershell
python -m tools.ste_linter --min-score 80 @((Get-ChildItem $skill -Recurse -Filter *.md).FullName)
```

Expected: each Markdown file scores 80 or more.

### V2. Total size

```powershell
'{0:N1} KB' -f ((Get-ChildItem $skill -Recurse -File | Measure-Object Length -Sum).Sum / 1KB)
```

Expected: the result is 400.0 KB or less.

### V3. Folder width

```powershell
(Get-ChildItem "$skill/references").Count
```

Expected: the result is 5 or less.

### V4. Index shape

```powershell
python -c "import csv; rows=list(csv.DictReader(open(r'.github/skills/junos-srx-security/references/corpus-index.csv', encoding='utf-8', newline=''))); print(len(rows), len(rows[0]))"
```

Expected: `12 6`.

### V5. Index paths resolve

```powershell
python -c "import csv, pathlib; root=pathlib.Path(r'C:\Users\jmorrison\Downloads\juniper-doc-archives'); rows=list(csv.DictReader(open(r'.github/skills/junos-srx-security/references/corpus-index.csv', encoding='utf-8', newline=''))); bad=[r['path'] for r in rows if not (root / r['path']).exists()]; print(len(rows), len(bad))"
```

Expected: `12 0`.

### V6. No ignored path citation

```powershell
Select-String -Path $skill -Recurse -Pattern ('documentation' + '/references') | Measure-Object
```

Expected: `Count : 0`.

## 7. Known limits

This skill distills source documents. It does not copy long vendor passages.

The SRX feature guides in the source archive are older than the Security Director 22.3 guides. If a device runs a newer Junos train, read the current release notes before a production change.

Security Director and Policy Enforcer commands are user interface actions in the source guides. Verify the result on the SRX with `show` commands.

The skill does not change a device. It gives commands, checks, warnings, and source citations.
