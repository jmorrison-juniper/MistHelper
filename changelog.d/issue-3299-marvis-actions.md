### Export and resolve Marvis Actions by category and subcategory (menu 270)

- **Added**: Menu 270 reads every Marvis Action of one organization, and a
  numbered table filters the actions by category and by subcategory. Mode 1
  exports every action, and mode 2 exports the open actions only. Each mode
  writes `OrgMarvisActions.csv` through CSV, SQLite, or ArangoDB. The database
  receives the full nested action. The CSV file holds a fixed set of columns
  with readable names for the category, the subcategory, the status, the site,
  and the device. Issue #3299.

- **Added**: Mode 3 marks the open actions of the selected topics as resolved.
  The operator chooses one of the four resolution codes of Mist and can add a
  comment. The code for another method needs a comment. The run shows a preview
  of every action, and it sends no request until the operator types `RESOLVE`
  and the action count. The run reads the list again, records the status that
  Mist reports for each action, and writes
  `OrgMarvisActionsResolveResults.csv`. Issue #3299.

- **Added**: `MARVIS_RESOLVE_MAX_ACTIONS` limits the number of actions that one
  resolve run changes. The default is 500. Issue #3299.

- **Added**: The operations portal on port 8055 runs menu 270 under the heading
  "Marvis Actions", with six controls in prompt order. Issue #3299.

- **Added**: `documentation/marvis-actions-api-endpoints.md` lists every API
  endpoint that menu 270 calls, with the request, the response, and the paging
  rule. Issue #3299.
