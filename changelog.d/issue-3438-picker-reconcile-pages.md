### Name a lost page in the site picker and in the reconciliation read

- **Fixed**: The site picker of the upgrade capture portal now shows a Caution
  note for each read that loses a page. Before this change, the picker showed a
  short site list that read as whole. A site could also show 0 devices when it
  held devices.

  Each mode of the picker shows the note above the site list. The note tells
  the operator to reload the page. The site list answer of `GET /api/sites`
  holds the new fields `site_list_complete` and `device_counts_complete`. The
  portal keeps a whole read only, so a reload reads the cloud again. The
  reconciliation read of a stopped run now marks each target of a lost page
  with unavailable evidence, instead of a stored version. Issue #3438.
