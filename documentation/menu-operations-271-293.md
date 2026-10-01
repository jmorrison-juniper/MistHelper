# Menu operations 271 to 293

This page explains the 23 operations that the 2026-09 feature program added.
Each operation reads the Mist cloud and writes a file under `data/`. Every
file also reaches the SQLite database or the ArangoDB store when you select
that output format. Read [the menu reference](menu_reference.md) for the
full table of every menu.

The operations fall into five families.

| Family | Menus | Safety |
| - | - | - |
| Hygiene reports | 271 to 276 | Safe. They read only. `--test` runs them. |
| Health scorecards | 277, 278, 279, 282 | Safe. They read only. `--test` runs them. |
| Alert digest | 280, 281 | 280 is safe. 281 changes alarm state. |
| Diagnostic utilities | 283, 284, 285, 288, 289, 290 | They prompt for a target. 283, 284, 285, and 290 can start a test on a device. |
| Lifecycle operations | 286, 287, 291, 292, 293 | Destructive. Each one needs a typed word and supports `--dry-run`. |

Warning: a destructive operation can change the production configuration of
the Mist cloud. It sends no request until you type the exact confirmation that
its title names. The `--dry-run` flag prints the request that the operation
would send, and it sends nothing. Use `--dry-run` first on a production
organization.

## Hygiene reports (271 to 276)

Each report joins data from the older export menus, and it scores each row. The console prints a summary with the count for each finding.

| Menu | Reads | Writes | Finding rules |
| - | - | - | - |
| 271 | Licenses, license usage, JSI contracts | `SubscriptionExpiry.csv`, `ContractExpiry.csv` | A subscription is `Active`, `Expired`, `Exceeded`, or `Inactive`. Usage above the entitled count gives `Exceeded` even before the end date. Days remaining never go below 0. The bands are expired, 0 to 30 days, 31 to 90 days, and more than 90 days. A device with no contract record is `Unsupported`. |
| 272 | Device statistics, organization settings, SSO records, PSK portals | `CertificateExpiry.csv` | One row for each device certificate, organization device certificate, NAC server certificate, SSO identity provider certificate, PSK portal certificate, and CA certificate. The row holds the subject, the issuer, the serial, and the dates. No key and no certificate body reach the file or the log. |
| 273 | Administrators, API tokens | `AdminHygiene.csv`, `TokenHygiene.csv` | An administrator with no two-factor authentication and no SSO is a finding. A token that no one used for 90 days is `idle`. A token that was never used is `never_used`. A token with org-wide write and no source IP limit is a finding. The token key never reaches the file or the log. |
| 274 | PSKs, organization WLANs | `PskHygiene.csv` | An expired key, a key that expires in 30 days, a multi-use key with no `max_usage`, a rotation that still holds the old passphrase, and a key whose SSID no organization WLAN carries (`orphan_ssid`) are findings. Site-level WLANs are outside the scope. The passphrase never reaches the file or the log. |
| 275 | Gateway, network, RF, and site templates, WLANs, device profiles, site variables | `SiteVariableAudit.csv`, `SiteVariableSummary.csv` | The audit finds every `{{variable}}` token at any depth of a template body. A site whose assigned template needs a variable that the site does not define appears in the audit file with the JSON path of the field. A variable that a site defines and no template uses counts as unused. |
| 276 | Organization settings, SSO records, administrators, API tokens, webhooks | `OrgSecurityPosture.csv` | One row for each check with a stable check id, the current value, the recommended value, and a verdict of `pass`, `fail`, or `review`. A setting that the API does not return gives `review`. A webhook URL that does not start with `https` gives `fail`. |

Environment variables for this family.

| Variable | Default | Menu | Meaning |
| - | - | - | - |
| `TOKEN_IDLE_DAYS` | `90` | 273 | A token with no use for this many days is `idle`. |

## Health scorecards (277, 278, 279, 282)

The web interface of Mist shows the health tiles of one site. These scorecards
compute the same tiles for every site of the organization from one read of
the device statistics. Each scorecard writes a row for each device and a
row for each site.

| Menu | Device type | Writes | Tiles and thresholds |
| - | - | - | - |
| 277 | Switches | `SwitchScorecard.csv`, `SwitchScorecardBySite.csv` | Switch-AP affinity (more than 12 APs on one switch fails), PoE compliance (draw above budget fails), version compliance (the predominant version of each model), switch uptime, config success, and potential anomalies. The row also holds the pending BIOS or FPGA version, the backup partition version, and fan and PSU errors. |
| 278 | Access points | `ApScorecard.csv`, `ApScorecardBySite.csv` | Connection status, inactive wired VLANs, version compliance, switch redundancy (`1` is none, `2` is good, `3` or more is excellent), power constrained state, configuration reverted state, and expiring certificates. The site color band is green at 98.5 percent or more, orange from 80 to 98.5 percent, and red below 80 percent. These values come from the Access Points page of the Mist web interface. |
| 279 | WAN edges | `WanEdgeScorecard.csv`, `WanEdgeDhcpPools.csv`, `WanEdgeScorecardBySite.csv` | Config status, version compliance, HA and cluster state, service status, DHCP pool use (one row for each pool), VPN peers up and down, BGP peers established and not established, and uptime. A pool at 80 percent or more use is a warning. |
| 282 | Rogue detections, site settings, organization WLANs | `RogueEvidence.csv`, `RogueSiteSettings.csv`, `RogueEvidenceSummary.md` | Each detection is `honeypot` (the SSID equals an organization SSID and the BSSID is not an organization AP), `rogue`, or `neighbor`. The site file states whether rogue and honeypot detection are on, the neighbor RSSI threshold, and the approved SSID and BSSID counts. The summary states that the Mist cloud sits outside the cardholder data environment. The site settings pass reads one record for each site. |

Environment variables for this family.

| Variable | Default | Menu | Meaning |
| - | - | - | - |
| `SWITCH_AP_AFFINITY_LIMIT` | `12` | 277 | A switch with more APs than this value fails the affinity tile. |
| `DHCP_POOL_WARN_PERCENT` | `80` | 279 | A pool at this percent or more is a warning. |

## Alert digest (280 and 281)

Menu 280 groups the alarms of the last 24 hours into the four categories of a
Mist alert: infrastructure, Marvis, security, and certificate. It writes
`AlertDigest.csv` with one row for each alarm type and site, with the
severity, the recurrence, the first seen time, and the last seen time. It also
writes `AlertDigest.md`, a handover summary with one section for each
category. The category of each alarm comes from the alarm definitions that the
Mist API publishes. An unknown type receives the category `unknown`.

Menu 281 lists the unacknowledged alarms of the same window and acknowledges
them with one request. It writes `AlertAcknowledgeLog.csv` with the result of
each alarm id.

Warning: menu 281 can remove an open alarm from the alert list of every
operator. It sends no request until you type `ACK` followed by the exact alarm
count. Any other input cancels the operation. With `--dry-run`, it prints the
alarm ids and sends nothing. The Mist web interface can set an alarm back to
unacknowledged.

| Variable | Default | Menu | Meaning |
| - | - | - | - |
| `ALERT_DIGEST_HOURS` | `24` | 280, 281 | The lookback window in hours. |

## Diagnostic utilities (283, 284, 285, 288, 289, 290)

Each utility prompts for a target. The four that start a test on a device ask
`y` or `N` before they send the request.

| Menu | What it does | Writes | Notes |
| - | - | - | - |
| 283 | Starts a synthetic test for a site, for one device, or a RADIUS check from one switch, then polls for the result | `SyntheticTestTrigger.csv` | Site scope asks for `Notification email (optional)` before the `y` or `N` gate. The poll stops after 120 seconds with a clear message. The RADIUS shared secret never reaches the log or the file. |
| 284 | Tests the guest portal SMS provider (Twilio, SMSGlobal, or Telstra) with one message to a phone number | `SmsProviderTest.csv` | Each credential prompt hides the input. This menu needs an interactive terminal and cannot run from a pipe or a scheduled job. No credential reaches the log or the file. |
| 285 | Validates a NAC identity provider credential with a username and a hidden password | `NacIdpCredentialTest.csv` | The password never reaches the log or the file. This menu needs an interactive terminal and cannot run from a pipe or a scheduled job. A failed validation prints the reason that the API returns. |
| 288 | Prints the SSR registration commands of the organization | `SsrRegistrationCommands.txt` after a `y` answer | The text holds a registration code, so the file write asks first and the log never holds the code. |
| 289 | Counts clients by family, OS, model, or OS type through the live org fingerprint path | `ClientFingerprintCensus.csv` | The request sends the selected site filter. The live cloud can ignore that filter. |
| 290 | Runs a spectrum analysis on one AP, or records an RF diagnostic for one client and downloads the file | `RfDiagnostics.csv`, recordings under `data/rfdiags/` | A recording stops even when you press Ctrl+C during the wait. |

## Lifecycle operations (286, 287, 291, 292, 293)

Warning: a wrong target in this family can disconnect a production user. It
can also move a configuration to the wrong device, or change the radio plan of
a whole site. Each operation sends no request until you type the exact
confirmation in the table. Each one supports `--dry-run`, which prints the
request and sends nothing. Each one writes a log file with one row for each
request.

| Menu | What it changes | Typed confirmation | Writes | Notes |
| - | - | - | - | - |
| 286 | Forces a client to reauthenticate (wireless or wired CoA), disconnects a client, deauthorizes a guest, or drops the clients of a rogue AP | The target MAC or BSSID, typed again | `ClientSessionControlLog.csv` | The MAC normalizes to the lowercase form with no separators. |
| 287 | Replaces a device for an RMA. The new device keeps the site, the name, and the configuration of the old one | `REPLACE` | `DeviceReplaceLog.csv`, a configuration backup under `data/rma_backups/` | The operation refuses a new device of another type. The backup exists before the request is sent. |
| 291 | Runs an RRM optimization, or resets every AP of a site to RRM | `OPTIMIZE` or `RESET` | `RrmPlanBefore.csv`, `RrmPlanAfter.csv`, `RrmPlanDiff.csv` | The before plan is on disk before the request. The after plan follows a settle time. The diff lists each radio whose channel, width, or power changed. |
| 292 | Imports PSKs, user MAC entries, or assets from a CSV file under `data/` | `IMPORT` followed by the exact row count | `CsvImportLog.csv` | The input file is `data/import_<type>.csv`. A missing required column stops the import before any request. A passphrase column never reaches the log. |
| 293 | Claims a Mist Edge, assigns it to a site, unassigns it, bounces its data ports, or upgrades it | `CLAIM`, `ASSIGN`, `UNASSIGN`, `BOUNCE`, or `UPGRADE` | `MxEdgeLifecycleLog.csv` | The upgrade step polls the status until it completes or the timeout passes. The claim code never reaches the log. |

Environment variables for this family.

| Variable | Default | Menu | Meaning |
| - | - | - | - |
| `RRM_SETTLE_SECONDS` | `300` | 291 | The wait between the request and the after capture. |

## How to run one operation

Start the menu and type the number, or run one operation from the command
line.

```powershell
podman exec misthelper-app python MistHelper.py -M 277
```

Add `--dry-run` for a destructive operation when you want the preview only.

```powershell
podman exec misthelper-app python MistHelper.py -M 291 --dry-run
```

Read [the operator guide](operator-guide.md) for the output location and the
output formats.
