Tasks for audit-menu-22-devices-site-info

- task: review-devices-method
  description: Read OrgInventoryExporter.devices_with_site_info and note exact data export calls and filenames.
  status: pending

- task: review-endpoint-strategy
  description: Verify ENDPOINT_PRIMARY_KEY_STRATEGIES contains appropriate entries for device and site endpoints used by the method (e.g., getOrgInventory, listOrgSites, getOrgDevices).
  status: pending

- task: confirm-write-method
  description: Check whether DataExporter.write_with_format_selection is used with api_function_name. If not, identify all DataExporter.save_data_to_output calls to be updated.
  status: pending

- task: tests-coverage
  description: Search tests/ for unit or integration tests targeting this method and list missing cases (fast/cache mode, address parsing edge cases, empty inventory).
  status: pending

- task: report-and-recommendations
  description: Produce final findings and recommended code changes and tests (do not implement in this ticket).
  status: pending
