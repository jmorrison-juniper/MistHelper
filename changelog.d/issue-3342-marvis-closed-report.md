### Export the closed Marvis Actions (menu 270, mode 4)

- **Added**: Menu 270 mode 4 exports the closed Marvis Actions only, and it
  changes no Mist data. A closed action holds the status Resolved By User, AI
  Validated, Marvis Self Driven, or Expired Action. The tables add a `Closed`
  column, and in mode 4 they show only the topics that hold a closed action. The
  columns `status_name`, `label_name`, `comment`, `resolve_time_iso`, and
  `validation_time_iso` show how and when each action closed. Mode 4 writes the
  outputs of mode 1, logs a caution line for each unknown status key, and runs in
  the operations portal. Issue #3342.

- **Changed**: Each column of the menu 270 tables fits its widest value, and the
  Name column moves to the end. In the portal log, the row of each known topic
  stays on one line. If a line is wider than the log viewer, only the end of the
  name wraps, and the numbers stay in their columns. Issue #3342.
