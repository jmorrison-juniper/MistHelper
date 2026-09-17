# Log sources and search

This reference gives verified procedures for DSMs, log sources, parser order,
unknown events, saved searches, and AQL.

Sources: JSA-DSM, JSA-AQL, JSA-UG, JSA-AD, and JATP-SIEM.

## 1. DSM and log source setup

### Task: install a DSM

1. Download the DSM RPM from Juniper Support.
2. Copy the RPM file to the JSA host.
3. Use SSH to log in to the JSA host as `root`.
4. Change to the directory that holds the RPM.
5. Run the verified install command.
6. Log in to JSA.
7. On the Admin tab, click Deploy Changes.

Source: JSA-DSM, JSA 7.4.2. The guide says uninstalling a DSM is not supported.

```text
yum localinstall -y --disablerepo=* --nogpgcheck <DSM_OR_PROTOCOL_RPM>
```

Warning: install a DSM only from a trusted Juniper download. A false parser can
misclassify events and hide an attack.

### Task: add one log source

1. Log in to JSA.
2. Click the Admin tab.
3. Open the JSA Log Source Management app.
4. Click New Log Source > Single Log Source.
5. Select a log source type.
6. Select a protocol type.
7. Configure the log source parameters.
8. Configure the protocol parameters.
9. Save the log source.
10. Test the log source when the Test tab is present.

Source: JSA-DSM, JSA 7.4.2. The guide states that passive protocols listen on
ports and active protocols poll through APIs or other methods.

### Task: set the parser order

1. Click the Admin tab.
2. Click the Log Source Parsing Ordering icon.
3. Select the log source.
4. Select the Event Collector when needed.
5. Select the Log Source Host when needed.
6. Put the most specific or most important log source first.
7. Click Save.

Source: JSA-DSM, JSA 7.4.2. The guide states that parser order applies to log
sources that share an IP address or host name.

## 2. Test and repair a log source

### Task: test collection

1. In the Log Source Management app, select the log source.
2. On the Log Source Summary pane, click the Test tab.
3. Click Start Test.
4. Wait for the test that runs from the Target Event Collector.
5. If the test fails, click Edit on the failed parameter.
6. Test the log source again.
7. Download the text result when you need evidence.

Source: JSA-DSM, JSA 7.4.2. The guide states that a failed result cancels the
remaining tests and no sample event information appears.

### Task: repair unknown or stored events

1. Search the Log Activity tab for the device source IP address.
2. Search for a unique payload value with Payload Contains.
3. Add the Event is Unparsed filter.
4. If the source is unknown, identify the device from the IP address.
5. Create a manual log source in the Log Source Management app.
6. Update DSMs and protocols.
7. If no DSM exists, write a log source extension or open a support request.

Source: JSA-DSM, JSA 7.4.2. The guide says traffic analysis needs at least 25
events and abandons auto discovery after 1,000 events.

Warning: do not ignore Unknown or Stored events during an investigation. JSA can
collect the event but fail to parse the fields that a rule or search needs.

### Task: add a log source extension

1. Click the Admin tab.
2. Click the Log Source Extensions icon.
3. Click Add.
4. Select Available when the DSM parses most fields correctly.
5. Select Set to default for log sources that must use the extension.
6. Browse to the extension XML document.
7. Upload the file and review XSD errors.
8. Click Save.
9. Verify the result on the Log Activity tab.

Source: JSA-DSM, JSA 7.4.2. The guide states that extension status changes apply
immediately. Managed hosts or Consoles enforce the new parsing parameters.

Warning: test a log source extension before you rely on a rule. A bad expression
can change a parsed event into a Stored event.

## 3. AQL query basics

### Task: write a valid AQL query

1. Start with `SELECT`.
2. Add `FROM` with `events` or `flows`.
3. Add `WHERE` when you need filters.
4. Add `GROUP BY` only for selected columns or expressions.
5. Add `HAVING` when grouped results need a filter.
6. Add `ORDER BY` for selected columns or expressions.
7. Add `LIMIT` when you need a bounded result.
8. End with a time window.

Source: JSA-AQL, JSA 7.4.2. The guide states that AQL uses the Ariel database
and defaults to the last five minutes when no time frame is specified.

### Verified AQL examples

These queries come from JSA-AQL, JSA 7.4.2. Retype quotation marks after a copy
from a PDF conversion.

```sql
SELECT * FROM events LAST 10 MINUTES
```

```sql
SELECT sourceip,destinationip FROM events LAST 24 HOURS
```

```sql
SELECT * FROM events WHERE INCIDR('192.0.2.0/24', sourceip)
```

```sql
SELECT * FROM events WHERE username ILIKE '%ROUL%'
```

```sql
SELECT Hostname, "Metric ID", AVG(Value) AS Avg_Value, Element
FROM events
WHERE LOGSOURCENAME(logsourceid) ILIKE '%%health%%'
AND "Metric ID"='SystemCPU'
OR "Metric ID"='DiskUtilizationDevice'
GROUP BY Hostname, "Metric ID", Element
ORDER BY Hostname LAST 20 minutes
```

```sql
SELECT logsourcename(logsourceid) AS 'MY Log Sources',
SUM(eventcount) / 2.0*60*60 AS EPS_Rates
FROM events
GROUP BY logsourceid
ORDER BY EPS_Rates DESC
LAST 2 HOURS
```

```sql
SELECT sourceip, LONG(SUM(sourcebytes+destinationbytes)) AS TotalBytes
FROM flows
WHERE flowdirection= 'L2R'
AND NETWORKNAME(sourceip) ILIKE 'servers'
GROUP BY sourceip
ORDER BY TotalBytes
```

## 4. Saved searches and quick filters

### Task: save a search

1. Build the search in the Log Activity, Network Activity, or Offenses tab.
2. Type a unique search name.
3. Assign the search to a group, or let JSA use Other.
4. Select the time span.
5. Select Include in my Quick Searches when operators need fast access.
6. Select Include in my Dashboard when a grouped search must feed the dashboard.
7. Select Set as Default only when the search should open automatically.
8. Select Share with Everyone only after you confirm the search is safe to share.
9. Click OK.

Source: JSA-UG, JSA 7.4.2. The guide confirms these saved search options and
states that saved offense criteria does not expire.

Warning: do not share a search that exposes sensitive payloads. Other users can
see the saved criteria and the matching evidence.

### Task: use a quick filter

1. Open the Log Activity or Network Activity tab.
2. Select Quick Filter from the Search toolbar.
3. Type plain text, an exact phrase, a wildcard pattern, or a logical expression.
4. Use uppercase `AND`, `OR`, and `NOT` for logical operators.
5. Escape special characters when they are part of the search term.
6. Keep the time window inside the payload index retention period.

Source: JSA-UG, JSA 7.4.2. The guide states that quick filter searches raw event
or flow payloads and does not distinguish fields.

Warning: a quick filter outside the payload index retention setting can cause a
slow and resource-intensive search.

## 5. JATP SIEM connector

### Task: send JATP alerts to a SIEM

1. In the JATP Central Manager web interface, go to Config > Notifications.
2. Select SIEM Settings from the left panel.
3. Click Add New SIEM Connector.
4. Select Events, System Audit, or System Health.
5. Select CEF, LEEF, or Syslog format.
6. Enter the SIEM host name and port number.
7. Click Add.
8. Confirm that JSA receives the event in the matching log source.

Source: JATP-SIEM, JATP 2018. The guide says JATP sends Download and Infection
incidents, phishing, exploit, email, file upload, data theft, and identity events.

### Task: open a JATP event from SIEM evidence

Use these verified URL shapes from JATP-SIEM, JATP 2018.

```text
https://JATP_HOSTNAME_HERE/admin/index.html?incident_id=0000000
https://JATP_HOSTNAME_HERE/admin/index.html?event_id=0000000
```

Warning: do not paste a real JATP host name or event identifier into shared text.
The values can reveal incident data.
