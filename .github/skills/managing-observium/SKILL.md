---
name: managing-observium
description: |
  Use when working with Observium, the network monitoring platform that
  auto-discovers network devices, polls them with SNMP, analyzes traffic, and
  raises alerts. The skill covers the device inventory, the port utilization,
  the health sensors, the alert review, and the syslog analysis. Use it when you
  monitor network infrastructure, when you investigate device health, when you
  analyze bandwidth utilization, or when you review Observium alerts.
connection_type: observium
preload: false
---

# Observium Monitoring Skill

Query, analyze, and manage the Observium monitoring data through the Observium
API.

Source: https://github.com/cloudthinker-ai/CloudSkills/blob/main/skills/connections/managing-observium/SKILL.md

## API overview

Observium supplies a REST API at `https://<OBSERVIUM_HOST>/api/v0`.

Set these three environment variables before you call the API. Keep them in
`.env`, and never write them into a file that git tracks.

| Variable | Purpose |
| - | - |
| `OBSERVIUM_URL` | The base URL of the Observium server. |
| `OBSERVIUM_USER` | The API user name. |
| `OBSERVIUM_PASS` | The API password. |

### Core helper function

```bash
#!/bin/bash

obs_api() {
    local endpoint="$1"
    curl -s "${OBSERVIUM_URL}/api/v0/${endpoint}" \
        -u "${OBSERVIUM_USER}:${OBSERVIUM_PASS}" \
        -H "Accept: application/json"
}
```

## MANDATORY: the discovery-first pattern

Always discover the devices, the device groups, and the ports before you query
anything else.

### Phase 1: discovery

```bash
#!/bin/bash

echo "=== Devices ==="
obs_api "devices" | jq -r '.devices | to_entries[] | "\(.value.device_id)\t\(.value.hostname)\t\(.value.os)\t\(.value.status | if . == "1" then "UP" else "DOWN" end)"' | head -25

echo ""
echo "=== Device Groups ==="
obs_api "groups/device" | jq -r '.groups | to_entries[] | "\(.value.group_id)\t\(.value.group_name)"' | head -15

echo ""
echo "=== Port Count by Device ==="
obs_api "ports" | jq -r '[.ports | to_entries[].value | .device_id] | group_by(.) | map({device: .[0], ports: length}) | sort_by(-.ports)[] | "\(.device)\t\(.ports) ports"' | head -15

echo ""
echo "=== Alert Checks ==="
obs_api "alerts/checks" | jq -r '.checks | to_entries[] | "\(.value.alert_test_id)\t\(.value.alert_name)\t\(.value.entity_type)"' | head -15
```

### Phase 2: analysis

```bash
#!/bin/bash

echo "=== Active Alerts ==="
obs_api "alerts" | jq -r '.alerts | to_entries[] | "\(.value.severity)\t\(.value.device_hostname // "unknown")\t\(.value.alert_message[0:60])"' | head -15

echo ""
echo "=== Down Devices ==="
obs_api "devices" | jq -r '.devices | to_entries[] | select(.value.status != "1") | "\(.value.hostname)\t\(.value.os)\t\(.value.last_polled)"' | head -15

echo ""
echo "=== Top Ports by Traffic ==="
obs_api "ports" | jq -r '.ports | to_entries[] | select(.value.ifOperStatus == "up") | "\(.value.device_id)\t\(.value.ifName)\tin:\((.value.ifInOctets_rate // 0) / 125000 | . * 10 | round / 10)Mbps\tout:\((.value.ifOutOctets_rate // 0) / 125000 | . * 10 | round / 10)Mbps"' | sort -t$'\t' -k3 -rn | head -15

echo ""
echo "=== Health Sensors ==="
obs_api "sensors" | jq -r '.sensors | to_entries[] | select(.value.sensor_alert == "1") | "\(.value.device_id)\t\(.value.sensor_descr)\tcurrent:\(.value.sensor_value)\tlimit:\(.value.sensor_limit)"' | head -10

echo ""
echo "=== Recent Syslog ==="
obs_api "syslog?limit=15" | jq -r '.syslog[] | "\(.timestamp[0:19])\t\(.device_hostname)\t\(.msg[0:60])"' | head -15
```

## Output rules

- Token efficiency: keep the output at 50 lines or less. Use the `limit`
  parameter and the `head` command.
- The device status field reads 0 for DOWN and 1 for UP.
- Use a device group to scope a query to one infrastructure segment.
- A port rate reports bytes each second. Divide the rate by 125000 for Mbps.

## Output format

Present the result as a structured report.

```text
Managing Observium Report
=========================
Resources discovered: [count]

Resource        Status     Key Metric    Issues
--------------------------------------------------
[name]          [ok/warn]  [value]       [findings]

Summary: [total] resources | [ok] healthy | [warn] warnings | [crit] critical
Action Items: [list of prioritized findings]
```

Keep the report at 50 lines or less. Use a table for a comparison of more than
one resource.

## Anti-hallucination rules

1. Never assume a resource name. Discover each name through the API in Phase 1
   before you reference it in Phase 2.
2. Never invent a metric name or a dimension. Verify each name against the
   service documentation or the `--help` output.
3. Never mix commands between two service versions. Confirm which API version
   you target.
4. Always follow the chain discover, verify, analyze. Every resource that you
   reference must come from the discovery step.
5. Always handle an empty result as valid data. An empty response is not an
   error, so do not retry it.

## Counter-rationalizations

| Shortcut | Counter | Why |
| - | - | - |
| "I will skip the discovery and check the resources that I know." | Always run the Phase 1 discovery first. | A resource name changes, and a new resource appears. An assumed name causes an error. |
| "The user asked for a quick check only." | Follow the full discovery and analysis flow. | A quick check misses a critical problem. A structured analysis finds a silent failure. |
| "The default configuration is probably correct." | Audit the configuration explicitly. | A default often leaves the logging, the security, and the optimization features off. |
| "This task does not need the metrics." | Always read the relevant metrics when they exist. | An API response shows the current state only. A metric shows the trend and the intermittent problem. |
| "I do not have access to that." | Run the command, then report the actual error. | An assumed permission failure stops a useful investigation. An actual error carries information. |
