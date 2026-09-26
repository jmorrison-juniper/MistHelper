### Refuse the upgrade options save after a short device read

- **Fixed**: The options save of the upgrade capture portal now refuses a site
  whose device list read lost a page. Before this change, the save planned the
  devices of the pages that the portal read. The devices of the lost pages kept
  the old firmware, and no record named them.

  The portal now checks the status and the body of each page of that read. An
  error page in the middle of the read no longer stops the options page with
  status 500. The options page of each mode shows a Caution banner for a short
  site. The refusal tells the operator to reload the page and to save the
  options again. Issue #3424.
