### Changed

- The results table now leads with the column that names each row. The table
  took its order from the file, and an exporter writes the keys alphabetically,
  so the site export opened with `address`, `alarmtemplate_id`, and
  `aptemplate_id` while `name` sat far to the right. A reader had to scroll
  sideways to learn which site each row described. The table now moves a known
  identity column to the front, in the order `name`, `hostname`, `site_name`,
  `mac`, `serial`, `id`. A record that holds none of those names keeps the
  order the file supplies, and the CSV download keeps the file order. Issue
  #3125.
