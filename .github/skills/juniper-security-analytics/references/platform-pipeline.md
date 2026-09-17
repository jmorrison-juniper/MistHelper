# Platform and pipeline

This reference explains the JSA deployment, the component roles, and the event
and flow pipeline. It also gives the verified SRX PCAP procedure.

Sources: JSA-DP, JSA-AD, JSA-UG, and JSA-PCAP.

## 1. Deployment model

### Task: choose the component

1. Use the Console for the product interface, searches, reports, offenses, assets, and administration.
2. Use an Event Collector to collect local and remote events and normalize raw events.
3. Use an Event Processor to process events and run rule responses.
4. Use a Flow Processor to process flows from Flow Processor appliances or routers.
5. Use a Data Node to store events and flows for an Event Processor or a Flow Processor.

Source: JSA-DP, JSA 7.4.2. The guide states that an All-in-One appliance collects,
processes, and stores data. It states that distributed deployments use the Console
mainly for the interface, searches, reports, alerts, and investigations.

### Task: avoid a mixed-release deployment

1. Identify the software version and build on each appliance.
2. Upgrade receivers before senders when off-site appliances exchange data.
3. Keep all appliances on the same software version and build.
4. Do not rely on rules, offenses, or searches while versions differ.

Warning: do not operate a mixed-release JSA deployment. Rules can fail to fire,
offenses can fail to update, and searches can return errors.

Source: JSA-DP, JSA 7.4.2. The component section says mixed versions are not
supported and can affect rules, offenses, and search results. JSA-AD says later
versions can receive from earlier versions, but earlier versions cannot receive
from later versions.

## 2. Event pipeline

### Task: explain event collection

1. A log source sends raw events to JSA.
2. The Event Collector parses and normalizes raw events.
3. The Event Collector coalesces identical events to conserve resources.
4. The Event Processor runs Custom Rules Engine tests.
5. The Event Processor stores event data locally or on a Data Node.

Source: JSA-DP, JSA 7.4.2. The data collection section states that event data is
collected, parsed, and normalized before processing. The component section states
that the Event Collector bundles identical events and sends them to the Event Processor.

### Task: explain event time fields

1. Use Start Time when you need the first time that the log source reported the event.
2. Use Storage Time when you need the time JSA stored the normalized event.
3. Use Log Source Time when you need the time in the raw event.
4. Compare these fields when a time zone or clock problem can affect the investigation.

Source: JSA-UG, JSA 7.4.2. The offense investigation section lists Start Time,
Storage Time, and Log Source Time on event details.

## 3. Flow pipeline

### Task: choose a flow source type

1. Use an internal flow source when a TAP or SPAN port sends packet data to a monitor port.
2. Use an external flow source when a router sends NetFlow, IPFIX, sFlow, J-Flow, or flow logs.
3. Use a dedicated Flow Processor when internal packet collection needs capacity.
4. Confirm that firewall rules allow the configured monitoring port.
5. Confirm that the flow source template includes required fields.

Source: JSA-AD, JSA 7.4.2. The flow source section lists internal and external
sources. It lists NetFlow, IPFIX, sFlow, J-Flow, and flowlog file as external sources.

### Task: configure an external flow source

1. Click the Admin tab.
2. Click Flow Sources.
3. Add or edit the flow source.
4. Select the Flow Processor that receives the data.
5. Set the monitoring interface and monitoring port.
6. Save the flow source.
7. Deploy changes.
8. Search flows by source, destination, protocol, and bytes.

Source: JSA-AD, JSA 7.4.2. The guide confirms the Flow Sources page and the add,
enable, disable, and delete tasks. Confirm vendor-specific fields in the same guide
before you configure a production source.

Warning: if you change the external flow source monitoring port, update the firewall
rule. Otherwise, the Flow Processor can stop receiving external flow records.

## 4. SRX packet capture

### Task: configure SRX PCAP into JSA

Use this procedure only after you confirm the SRX IDP policy and the JSA log source.

1. On the SRX, enable IDP attack logging for the policy rule.
2. On the SRX, enable packet-log pre-attack, post-attack, and timeout values.
3. On the SRX, set packet-log memory, maximum sessions, source address, host, and host port.
4. In JSA, go to Admin > Data Source > Events > Log Sources.
5. Add a Juniper SRX Series Services Gateway log source.
6. Select the PCAP Syslog Combination protocol.
7. Set the Incoming PCAP Port to match the SRX host port.
8. Delete the auto-discovered Syslog-only log source when the PCAP source replaces it.
9. Deploy changes.
10. Add the PCAP Data column to the event search results.

Source: JSA-PCAP, JSA 7.4.2. The guide confirms the PCAP Syslog Combination
protocol and states that the SRX outgoing port must match the JSA incoming port.

### Verified SRX commands

These commands come from JSA-PCAP, JSA 7.4.2. Replace the policy, rule, and
addresses before use.

```text
set security idp idp-policy Test rulebase-ips rule 1 then notification log-attacks
set security idp idp-policy Test rulebase-ips rule 1 then notification packet-log pre-attack 10
set security idp idp-policy Test rulebase-ips rule 1 then notification packet-log post-attack 3
set security idp idp-policy Test rulebase-ips rule 1 then notification packet-log post-attack-timeout
set security idp sensor-configuration packet-log total-memory 5
set security idp sensor-configuration packet-log max-sessions 15
set security idp sensor-configuration packet-log source-address 10.0.0.1
set security idp sensor-configuration packet-log host 10.0.0.2
set security idp sensor-configuration packet-log host port 5
show security idp sensor-configuration
```

Warning: if the SRX packet-log source address differs from the log source IP, JSA
can store the PCAP under `/store/pcap/` but fail to show it in the web interface.

## 5. Data storage and Data Nodes

### Task: use a Data Node safely

1. Connect a Data Node to an Event Processor or a Flow Processor.
2. Use Active mode when the node must receive new data.
3. Use Archive mode when the node must keep historical data online.
4. Do not expect an Archive mode node to receive new data.
5. Set the mode back to Active when it must receive new data again.

Source: JSA-DP and JSA-AD, JSA 7.4.2. The guides state that a Data Node stores
security events and flows and that Archive mode preserves existing data only.

Warning: do not set a Data Node to Archive mode during active collection. The node
stops receiving new data, and the deployment can lose storage capacity.
