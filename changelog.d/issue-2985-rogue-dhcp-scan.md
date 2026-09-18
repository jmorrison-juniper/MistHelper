### Scan the organization for rogue DHCP servers on switches (menu 269)

- **Added**: Menu 269 scans one organization for every rogue DHCP server signal
  in a 30-day window. It reads organization alarms, organization switch events,
  site alarms, site switch events, and Marvis config actions. It queries the
  organization first, then it queries only a site that an organization result
  named, so a large organization does not spend a request on every site. The
  operation merges the sources into one table, marks each row `active` or
  `historical`, prints the table, and writes `OrgRogueDhcpServers.csv` through
  CSV, SQLite, or ArangoDB. Issue #2985.
- **Added**: The operations web dashboard on port 8055 runs menu 269 and shows
  its output file. The upgrade capture portal on port 8056 is unchanged. Issue
  #2985.
