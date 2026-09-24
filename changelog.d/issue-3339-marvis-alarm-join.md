### Add the Marvis alarm to each exported Marvis Action (menu 270)

- **Added**: Menu 270 modes 1, 2, and 4 search the Marvis alarms one time for
  each export. Each exported row then holds the eight alarm columns `alarm_id`,
  `alarm_type`, `alarm_status`, `alarm_resolved_time_iso`, `alarm_acked`,
  `alarm_acked_time_iso`, `alarm_ack_admin_name`, and `alarm_note`. The CSV
  file, the SQLite table, and the ArangoDB document hold the same values. The
  join matches the alarm `action_id` or the alarm `id` to the action `uuid`. Two
  count lines show the number of joined actions and the number of alarms without
  an action. Issue #3339.

- **Changed**: The Marvis Actions export holds 51 columns instead of 43. The
  eight alarm columns come after `exported_at`, so the first 43 columns keep
  their positions. If the alarm search fails, the export writes every action
  with empty alarm columns, and one warning line names the reason. Mode 3 sends
  no alarm search, and no mode acknowledges an alarm. Issue #3339.
