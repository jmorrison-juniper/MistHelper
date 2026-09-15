# SSR_FIRMWARE_HEALTH

## 1. Overview

| Field | Value |
|---|---|
| **Document type** | Cross-alarm procedure. No Mist alarm key maps to it. |
| **Platform** | Any Mist-managed Juniper Session Smart Router. The steps are model agnostic. |
| **Purpose** | Read the software state from the console, and diagnose a fault that followed a software change. |
| **Audience** | Tier 1 for the read steps. Tier 2 for every step that changes software. |

### Who drives a software change

Mist drives the software on a Mist-managed router. The console holds the same
commands, and they work, but a change made at the console fights the cloud.

| Action | Who performs it |
|---|---|
| Read the current version. | Tier 1, at the console or in Mist. |
| Read the upgrade state and the health check result. | Tier 1, at the console. |
| Start an upgrade. | Mist, through the portal or the scheduled workflow. |
| Revert after a failed upgrade. | Tier 2, and only with approval. |

Warning: never start an upgrade at the console on a Mist-managed router without
Tier 2 approval. Mist holds the intended version. A console upgrade creates a
mismatch, and the next cloud push can reverse your change during business hours.

## 2. Read the current state

Every command in this section is read only. Run them all before you form a
conclusion.

| Command | Why you run it | Healthy output | Unhealthy signature and next action |
|---|---|---|---|
| `show system` | States the node status and the running version in one line. | `Status: running`. The version matches the version that Mist reports. | An uptime under 10 minutes after a planned upgrade is expected. An uptime under 10 minutes with no planned change means an unplanned restart, so read the event history. |
| `show system version detail` | States the exact build, the build date, and the package name. The vendor matches a defect to this string. | The build matches the release notes for the intended version. | A build that differs from the intended version means that the upgrade did not complete, or that the router reverted. |
| `show system software upgrade` | Reports the upgrades that are in progress, and the upgrades that finished. | No upgrade is in progress. The last upgrade reports success. | An upgrade stuck in progress blocks every later change. Record the state and escalate. Do not start a second upgrade. |
| `show system software download` | Reports the downloads that are in progress, and the downloads that finished. | The intended version is present. | A download that never finishes means that the router cannot reach the software source. Check the transport in stage D of [SSR_CONSOLE_HEALTH_CHECK.md](SSR_CONSOLE_HEALTH_CHECK.md). |
| `show system software available` | Lists the versions that the router can install. | The intended version appears. | An empty list means that the router reached no source. Read `show system software sources`. |
| `show system software revert` | Reports a reversion in progress, and a reversion that finished. | No reversion is in progress. | An automatic reversion means that the upgrade failed its own health check. The router protected itself. Read the health check result next. |
| `show system software health-check` | Lists the health checks that the platform offers, and the last result. | The last check passed. | A failed check names the condition that blocked the upgrade. That condition is the real fault, not the upgrade. |
| `show system software sources` | States where the router looks for software. | The source matches the design. | A missing source or a disabled source stops every download. |

## 3. Confirm a planned upgrade succeeded

Run this list after any planned change. A green result in Mist is not proof on
its own, because Mist reports the push and not the outcome.

| Step | Command | Pass condition |
|---|---|---|
| 1 | `show system` | `Status: running`, and `Alarm Count: 0`. |
| 2 | `show system version detail` | The build matches the intended version. |
| 3 | `show system processes` | Every process reports `running`. |
| 4 | `show system services` | Every service reports `active`. |
| 5 | `show alarms` | No active alarm. |
| 6 | `show device-interface summary` | Every port that carries service reports up. |
| 7 | `show peers` | Every designed peer path reports `up` or `standby`. |
| 8 | `show bgp summary` | Every neighbor holds a time value under `Up/Down`. |
| 9 | `show service-path` | Every service reports `Up`. |
| 10 | `show mist` | The cloud link is present. |

A failure at any step means that the upgrade did not deliver a working router.
Record the step number in the ticket, and escalate.

## 4. Diagnose a fault that followed a software change

Start here when the ticket says "it broke after the upgrade".

| Question | Command | What the answer means |
|---|---|---|
| Did the software really change? | `show events type admin` | The event record states the change and its time. Compare that time against the start of the fault. If they do not match, the software is not the cause. |
| Did the configuration change at the same time? | `show config version` | An upgrade and a configuration push often arrive together. The configuration is the more common cause of the two. |
| Did a process die after the change? | `show system processes` | A process that does not report `running` names the fault. The `process` alarm reports the same condition. |
| Did the platform run out of room? | `show platform disk` | An upgrade consumes disk space. A `disk space low` alarm after an upgrade is a known pattern. |
| Did the resource tables change behavior? | `show capacity` | A new release can change a table limit. A table near 100 percent explains dropped traffic that no interface counter shows. |
| Did the router revert on its own? | `show system software revert` | An automatic reversion means that the new version failed its post-upgrade check. The router is now on the old version, and the ticket is a failed upgrade, not an outage. |
| Which volume will boot next? | `show system software available detail` | On an image-based platform, the boot volume decides the version after the next restart. |

### Two faults that look like a firmware fault and are not

| Symptom | Real cause | Command that proves it |
|---|---|---|
| The router reports the old version, and Mist reports the new version. | Local configuration override is in force, so the cloud cannot push. | `show config local-override` |
| Every feature works, and the cloud shows the device as disconnected. | The management path failed. The software is fine. | `show mist`, then stage C and stage D of [SSR_CONSOLE_HEALTH_CHECK.md](SSR_CONSOLE_HEALTH_CHECK.md) |

## 5. Commands that change software

Warning: every command in this section is service affecting. Tier 2 owns them.
Read [Shared Appendix §8](_shared_common.md) before you run one.

| Command | What it does | The risk |
|---|---|---|
| `request system software health-check` | Runs the health check without changing anything. | None. This is the safe first step, and Tier 1 may run it. |
| `request system software download version <version>` | Downloads a version. It does not install it. | It consumes disk space and transport bandwidth. Run it outside business hours on a slow link. |
| `request system software upgrade version <version>` | Upgrades the router. | Service affecting. On a two-node router the default sequence takes one node at a time. |
| `request system software revert` | Returns the router to the previous version. | Service affecting. Use it to recover a failed upgrade. |
| `request system software downgrade version <version>` | Moves the router to a lower version. | Service affecting, and it can lose data and function. The vendor blocks a sequenced downgrade on a two-node router. |
| `set system software boot-volume <id>` | Chooses the volume for the next restart. | The change takes effect on the next restart, not at once. |
| `delete system software version <version>` | Removes a downloaded version, or cancels a download. | It frees disk space. It cannot remove the running version. |

### Four arguments that remove a safety net

Never pass one of these without a written instruction from Tier 2 or from the
vendor.

| Argument | What it removes |
|---|---|
| `simultaneous` | It upgrades both nodes of a two-node router at the same time. Service stops for the whole operation. |
| `skip-pre-health-check` | It starts the upgrade even when the router fails its own readiness check. |
| `skip-post-health-check` | It keeps the new version even when the router fails its check afterward. |
| `no-revert` | It stops the automatic return to the previous version when the upgrade fails. |

## 6. Closure criteria

- `show system version detail` reports the intended build.
- Every one of the ten steps in §3 passes.
- No alarm from §2 or §3 remains active.
- Mist reports the device as connected, and it reports the same version as the
  console.
- The ticket records the intended version, the achieved version, and the time of
  the change.

## 7. Escalation

| Condition | Action |
|---|---|
| An upgrade reports in progress and does not finish. | Escalate to Tier 2. Do not start a second upgrade. |
| The router reverted on its own. | Escalate to Tier 2 with the health check result. |
| A process fails to start after an upgrade. | Escalate to the vendor with the archive from [SSR_EVIDENCE_CAPTURE.md](SSR_EVIDENCE_CAPTURE.md) §4. |
| The console version and the Mist version disagree. | Check local override first. Then escalate to Tier 2. |

## 8. Sources

| Source | Where |
|---|---|
| Session Smart Networking command line reference | <https://docs.128technology.com/docs/cli_reference> |
| Session Smart Networking alarm guide | <https://docs.128technology.com/docs/events_alarms> |
| Juniper Mist WAN Assurance documentation | <https://www.juniper.net/documentation/us/en/software/mist/mist-wan/mist-wan.pdf> |

Run `python scripts/fetch_ssr_docs.py` to build a local copy of every page above
under `documentation/references/ssr/`. That directory is not committed, because it
holds verbatim vendor text.
