### Export the closed Marvis Actions (menu 270, mode 4)

- **Added**: Menu 270 mode 4 exports the closed Marvis Actions only. A closed
  action holds the status Resolved By User, AI Validated, Marvis Self Driven, or
  Expired Action. The category and subcategory tables add a `Closed` column, and
  the filter shows only the topics that hold a closed action. The columns
  `status_name`, `label_name`, `comment`, `resolve_time_iso`, and
  `validation_time_iso` show how and when each action closed. Mode 4 writes the
  same outputs as mode 1. The default format writes `OrgMarvisActions.csv`, and
  the `--output-format sqlite` flag writes the SQLite table `OrgMarvisActions`
  instead. When ArangoDB answers, the run also writes the collection
  `listOrgMarvisActions`. Mode 4 changes no Mist data. Issue #3342.

- **Added**: If Mist returns a status key that MistHelper does not know, mode 4
  exports the action and prints a caution line that names the key. The
  operations portal on port 8055 offers mode 4 in the Mode list. Issue #3342.
