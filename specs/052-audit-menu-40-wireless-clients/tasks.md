Tasks for Menu #40 (wireless_clients):

- task-052-1: Write unit test 'test_wireless_clients_invokes_exporter' that:
  - Mocks mistapi.api.v1.orgs.clients.searchOrgWirelessClients to return sample data
  - Mocks DataExporter.write_with_format_selection to capture args
  - Calls OrgClientSecurityExporter.wireless_clients()
  - Asserts DataExporter.write_with_format_selection called with api_function_name="searchOrgWirelessClients"

- task-052-2: Write integration test 'test_wireless_clients_sql_strategy' that:
  - Runs APIDataFetcher workflow with small sample data
  - Writes to temp SQLite and inspects schema to validate PRIMARY KEY includes (mac,timestamp)

- task-052-3: Run full test suite and document results.

Estimated effort: 2-4 hours.