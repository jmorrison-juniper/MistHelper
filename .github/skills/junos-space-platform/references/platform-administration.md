# Platform administration

This reference covers the Junos Space fabric, platform upgrade, database backup,
database restore, user roles, user sessions, domains, and API access profiles.

Use the newest selected platform sources first:

- Junos Space Network Management Platform Complete Software Guide, Release 21.1.
- Junos Space Network Management Platform Workspaces User Guide, Release 21.1.

## Deploy a fabric node

Use this procedure when the user needs the first node or another node in a Junos
Space fabric.

Source: Junos Space Network Management Platform Complete Software Guide, Release
21.1, pages 54 through 56.

1. Open the appliance CLI console.
2. Enter the `eth0` IP address and subnet mask.
3. If this is the first node, enter the virtual IP address for browser access.
4. Enter the default gateway IP address.
5. Enter the name server IP address.
6. If the deployment uses a separate management network, enter the `eth3` IP address and subnet mask.
7. If this is the first node, choose `n` when the console asks whether to add the appliance to a cluster.
8. If this is an added node, choose `y` when the console asks whether to add the appliance to a cluster.
9. Enter the NTP server settings.
10. Enter the maintenance mode user ID and password.
11. Store the maintenance credentials in the approved secret store.

Warning: do not lose the maintenance credentials. A platform upgrade or database
restore can require those credentials, and the fabric can stay in maintenance
mode without them.

The hardware appliance source says that the appliance shows a menu-driven CLI
when you start it. The virtual appliance source says that the OVA must be
deployed to ESX, ESXi, or KVM before you start the appliance.

## Add capacity to a virtual appliance

Use this check when a fabric uses virtual appliances.

Source: Junos Space Network Management Platform Complete Software Guide, Release
21.1, page 56.

1. Confirm that the CPU, RAM, and disk meet the documented virtual appliance requirements.
2. If the fabric has more than one node, place the first and second appliances on separate servers.
3. Confirm that the first and second nodes have the same disk size.
4. If disk use exceeds 80 percent, add sufficient disk space before the platform degrades.

Caution: unequal disk sizes can make a multinode fabric unreliable. Equalize the
disks before you add the second node.

## Upgrade the platform

Use this procedure when the user upgrades Junos Space Network Management
Platform.

Source: Junos Space Network Management Platform Complete Software Guide, Release
21.1, pages 62 and 63.

1. Read the release notes for the source and target releases.
2. Confirm that a direct upgrade path exists.
3. If the direct path does not exist, plan each intermediate upgrade.
4. Confirm that time is synchronized on all Junos Space nodes.
5. Download the platform `.img` file from the Juniper software download site.
6. If you use SCP, place the image on an SCP server that Junos Space can reach.
7. In the Junos Space UI, select `Administration > Applications`.
8. Right-click the image file.
9. Select `Upgrade Platform`.
10. Upload the image file with HTTP or SCP.
11. Select the uploaded file.
12. Click `Upgrade`.
13. Enter the maintenance mode user name and password when Junos Space asks for them.
14. Monitor the job until all nodes finish the upgrade.

Warning: a platform upgrade can deactivate incompatible applications. Inventory
all installed applications before you start the upgrade.

Warning: a platform upgrade restarts JBoss servers and can reboot all nodes.
Plan downtime before you start the upgrade.

The source states an average downtime of 30 to 45 minutes for a single-node
fabric. It states 45 to 60 minutes for a two-node fabric. Use those values as a
planning estimate, not as a guarantee.

## Back up and restore the database

Use this procedure for platform database backup or restore.

Source: Junos Space Network Management Platform Workspaces User Guide, Release
21.1, pages 1158 through 1161.

1. Confirm that the operator has the `System Administrator` role.
2. Open `Administration > Database Backup and Restore`.
3. For a backup, choose local backup or remote backup.
4. For a remote backup, use a Linux server that runs SCP.
5. For a remote backup, confirm the remote host, user ID, password, and destination directory.
6. If network monitoring data is too large, choose whether to include it.
7. If Cassandra runs on at least one node, choose whether to include Cassandra.
8. Start the backup.
9. Monitor the backup job until Junos Space shows the backup file.
10. For a restore, select a backup from the same Junos Space release.
11. Start the restore from `Administration > Database Backup and Restore`.
12. Use the maintenance mode administrator while the fabric restores the database.
13. After restore, restart the application servers as required by the platform.

Warning: a database restore puts Junos Space Network Management Platform into
maintenance mode. All users except the maintenance administrator lose access.

Warning: restore a database only from the same release version. A different
release can corrupt or reject the platform data.

The backup includes the MySQL database, Cassandra database, network-monitoring
database, DMI schemas, and configuration files when those options are selected.
A local backup uses `/var/cache/jboss/backup`. A remote backup has no local path
restriction.

## Assign access with roles and domains

Use this procedure when a user needs access to platform tasks or objects.

Source: Junos Space Network Management Platform Complete Software Guide, Release
21.1, pages 68 through 70.

1. Decide whether Junos Space uses local authentication or remote AAA servers.
2. If the site uses remote AAA, open the Administration workspace.
3. Select the authentication server page.
4. Add the RADIUS or TACACS+ server addresses, ports, and shared secrets.
5. Test the connection to each AAA server after you add it.
6. Create the user account or remote profile.
7. Assign only the roles that match the required tasks.
8. Assign the user to the correct domain or domains.
9. Confirm that the user can see only the intended workspaces and objects.

Warning: a role or domain error can give access to devices outside the intended
scope. Review the domain and role before you save the user.

Junos Space includes more than 25 predefined roles and supports custom roles.
Domains group objects such as devices, templates, users, and services. Use
multiple domains to separate large or regional systems.

## Manage user sessions

Use this procedure before a maintenance cycle or when too many sessions affect
platform performance.

Source: Junos Space Network Management Platform Workspaces User Guide, Release
21.1, pages 965 through 969.

1. To view sessions, select `Role Based Access Control > User Sessions`.
2. Review the user name, current domain, client IP address, fabric node, start time, and duration.
3. To limit future sessions, select `Administration > Applications`.
4. Select `Network Management Platform`.
5. Select `Modify Application Setting` from the Actions menu.
6. Click `User`.
7. Enter the maximum concurrent UI sessions per user.
8. Click `Modify`.
9. To terminate sessions, return to `Role Based Access Control > User Sessions`.
10. Select one or more sessions.
11. Start the termination action.

Caution: a session limit affects the next login only. Existing sessions continue
until the user exits or an administrator terminates them.

The source states that the super user can log in even when the limit is
exceeded. It also states that API configuration does not count as a UI session.

## Create an API access profile

Use this procedure when a user needs to run RPC commands through `exec-rpc`.

Source: Junos Space Network Management Platform Workspaces User Guide, Release
21.1, pages 961 and 962.

1. Select `Role Based Access Control > API Access Profiles`.
2. Click the `Create API Access Profile` icon.
3. Enter a profile name.
4. Optionally, enter a description.
5. On the RPC Command Rules tab, click the `Add Rule` icon.
6. Enter an XPath rule for the allowed RPC command.
7. Click `OK`.
8. Repeat the rule step until the profile has at least one rule.
9. Click `Save`.
10. Assign the API access profile to the local user, remote user, or remote profile.

Warning: if no API access profile is associated with a user account, the user
cannot execute RPC commands on the device. Junos Space shows `Unauthorized
AccessError`.

An API access profile restricts commands that can be unsafe or harmful to the
network. Junos Space writes an audit log entry when an operator creates,
modifies, or deletes a profile.
