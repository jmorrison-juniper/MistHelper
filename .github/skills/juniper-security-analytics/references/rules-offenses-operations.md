# Rules, offenses, and operations

This reference gives safe procedures for rules, building blocks, false positives,
offenses, reports, dashboards, retention, health, backups, and upgrades.

Sources: JSA-UG, JSA-AD, JSA-TUNE, JSA-AQL, JSA-DP, and JSA-UP.

## 1. Rules and building blocks

### Task: understand the rule path

1. Event Collectors gather and normalize events.
2. Flow Processors read packets or receive flow records.
3. Event Processors examine and correlate event and flow data.
4. The Custom Rules Engine compares data against rules.
5. A matched rule runs the configured response.
6. A rule can contribute events or flows to an offense.

Source: JSA-UG, JSA 7.4.2. The guide states that building blocks are tested
before rules.

### Task: create a custom rule

1. Click the Offenses, Log Activity, or Network Activity tab.
2. Click Rules.
3. Click Actions > New Event Rule, New Flow Rule, New Common Rule, or New Offense Rule.
4. Select the tests that match the threat behavior.
5. Use AQL WHERE tests for complex event or flow criteria.
6. Configure the rule response.
7. Name the rule and assign the rule group.
8. Finish the wizard.
9. Monitor rule performance after events or flows route to storage.

Source: JSA-UG, JSA 7.4.2. The guide defines event, flow, common, and offense
rules and says AQL WHERE clauses can test complex criteria.

Warning: do not enable a new high-volume rule without a performance review. A slow
rule can degrade correlation and cause missed notifications.

### Task: edit a building block

1. Click the Offenses or Network Activity tab.
2. Click Rules.
3. From Display, select Building Blocks.
4. Double-click the building block.
5. Update the tests.
6. Click Next.
7. Continue through the wizard.
8. Click Finish.

Source: JSA-UG, JSA 7.4.2. The guide gives this procedure and uses the mail
server building block as an example.

Warning: do not remove a host from a shared building block until you identify each
rule that uses it. The change can alter many detections at once.

## 2. False positive tuning

### Task: tune a false positive

1. Open the event or flow that triggered the noise.
2. Confirm the source, destination, event name, rule, and payload.
3. Search for similar events or flows in the same time window.
4. Confirm that the activity is expected and approved.
5. Choose a narrow rule edit or a building block exclusion.
6. Record the reason in the rule note or change record.
7. Run the same search again to confirm that expected attacks still match.
8. Monitor the rule performance and offense rate after the change.

Source: JSA-UG and JSA-TUNE, JSA 7.4.2. The user guide includes false positive
configuration for events and flows. The tuning guide directs operators to tune
rules, offenses, building blocks, and search performance during application tuning.

Warning: do not mark an event or flow as a false positive until a second search
proves it is benign. The change can hide a real attack.

## 3. Offense investigation

### Task: investigate events in an offense

1. Open the Offense Summary window.
2. Click Events.
3. Set the Start Time, End Time, and View options.
4. Sort by a column when the list is large.
5. Right-click a value to add a quick filter.
6. Double-click an event to view details.
7. Review raw payload data that JSA did not normalize.
8. Add notes to preserve investigation context.

Source: JSA-UG, JSA 7.4.2. The guide states that events created by JSA have no
payload because no raw event created them.

### Task: investigate flows in an offense

1. Open the Offense Summary window.
2. Click Flows.
3. Set the Start Time, End Time, and View options.
4. Sort by a column when needed.
5. Right-click a flow value to add a quick filter.
6. Double-click a flow to view details.
7. Check source and destination payload sizes.
8. Review partially matched custom rules.

Source: JSA-UG, JSA 7.4.2. The guide states that JSA extracts normalized fields
and custom flow properties from the first 64 bytes by default.

### Task: hide or show an offense

1. Select the offense on the Offenses tab.
2. Use Actions > Hide only when the offense must leave normal lists.
3. Clear Exclude Hidden Offenses when you need to find hidden offenses.
4. Use Actions > Show to remove the hidden flag.
5. Add a note that explains why the offense was hidden or shown.

Source: JSA-UG, JSA 7.4.2. The guide states that hidden offenses do not appear in
normal Offenses lists, but searches that include hidden offenses can show them.

Warning: do not hide an active offense without a documented reason. Other operators
can miss an attack that still needs action.

## 4. Dashboards and reports

### Task: create a dashboard item from a search

1. Build a grouped search that returns the data for the dashboard.
2. Save the search.
3. Select Include in my Dashboard.
4. Open the Dashboard tab.
5. Add the saved search item.
6. Select a chart type that matches the data.
7. Confirm that the item refreshes inside the expected time window.

Source: JSA-UG, JSA 7.4.2. The dashboard chapter confirms custom dashboards and
search-based dashboard items.

### Task: create a custom report

1. Click the Reports tab.
2. Click Actions > Create.
3. Use the Report Wizard.
4. Select the layout, chart type, and data source.
5. Use a saved search when the report must repeat a known investigation.
6. Configure the schedule or generate the report manually.
7. Review generated report content.
8. Share or delete generated content according to the evidence policy.

Source: JSA-UG, JSA 7.4.2. The report chapter confirms custom reports, generated
reports, manual generation, sharing, and generated content deletion.

Warning: do not delete generated report content during an incident. The deletion
can remove evidence that an investigator needs.

## 5. Retention and storage

### Task: change retention safely

1. Identify the event or flow data that the retention bucket stores.
2. Confirm incident response and legal hold requirements.
3. Confirm the affected hosts and Data Nodes.
4. Confirm that backups or archives cover required evidence.
5. Change the retention bucket only after approval.
6. Search for data in the expected time window after the change.
7. Record the approval and verification result.

Source: JSA-AD and JSA-DP, JSA 7.4.2. The administration guide covers retention
buckets in the event, flow, and storage administration areas. The deployment guide
states that Data Nodes store event and flow data.

Warning: do not shorten retention without approval. The change can delete evidence
before an investigation or legal hold ends.

## 6. Health, backup, and recovery

### Task: check deployment health

1. Install the QRadar Deployment Intelligence app when the deployment uses it.
2. Create an authorized service token for the app.
3. Open the Deployment Intelligence dashboard.
4. Review host status, notifications, appliance type, disk usage, and time changed.
5. Drill down for event rates, flow rates, system notifications, and disk data.
6. Use Get Logs when support needs host log files.

Source: JSA-AD, JSA 7.4.2. The guide states that Deployment Intelligence uses JSA
health metrics and that health metrics do not count against the license.

### Task: schedule a nightly backup

1. Click the Admin tab.
2. Click Backup and Recovery.
3. Click Configure.
4. Set the backup repository path.
5. Set the backup retention period.
6. Select the nightly backup option.
7. Select managed hosts for data backup when needed.
8. Set backup time limits and priority.
9. Click Save.
10. Deploy changes.

Source: JSA-AD, JSA 7.4.2. The guide states that JSA creates a configuration
backup daily at midnight by default and can include data from selected hosts.

Warning: do not store active data and backup archives in the same full directory.
Scheduled backups can fail when storage reaches capacity.

### Task: create an on-demand configuration backup

1. Click the Admin tab.
2. Click Backup and Recovery.
3. Click On Demand Backup.
4. Type a unique name.
5. Type a description.
6. Click Run Backup.
7. Monitor the Backup Archives window until the backup completes.

Source: JSA-AD, JSA 7.4.2. The guide states that on-demand backups include only
configuration information and can affect system performance.

## 7. Upgrade planning

### Task: prepare an upgrade

1. Read the target release notes and upgrade guide.
2. Confirm that all appliances meet the target release requirements.
3. Create and verify a configuration backup.
4. Confirm that off-site receivers upgrade before senders.
5. Confirm a maintenance window with the security operations team.
6. Upgrade the Console and managed hosts according to the upgrade guide.
7. Confirm event rates, flow rates, rules, offenses, searches, and reports after upgrade.

Source: JSA-UP and JSA-DP, JSA 7.4.2. The upgrade guide covers the 7.4.2 upgrade.
The deployment guide warns against mixed-version deployments.

Warning: do not start an upgrade without a tested backup. A failed upgrade can make
configuration recovery impossible.
