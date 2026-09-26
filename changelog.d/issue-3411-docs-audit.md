### Added

- The menu API endpoint map shows the Mist API endpoints that each menu option
  can call. Each menu option has a Mermaid flowchart and a table. The table
  gives the HTTP method, the path, the mistapi function, its document link, and
  the code that sends the request. Read `documentation/menu-api/README.md` or
  the `Menu-API-Endpoints` wiki page. See issue #3411.
- `tools/menu_api_map` writes the map from the source code and from a vendored
  index of the mistapi functions. The `menu_reference_drift` CI job runs
  `python -m tools.menu_api_map --check`, and the job fails when a map page is
  stale. See issue #3411.

### Changed

- An audit corrected the README, the wiki, the Mermaid diagram suite, the
  operator guides, and the agent instruction files. The pages now state the
  current menu count, the current CI jobs, the current SNMP base OID, and the
  current compose services. See issue #3411.
