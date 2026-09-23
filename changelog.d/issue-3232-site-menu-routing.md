### Fixed

- A site-scoped run no longer prints the 143-line command-line site menu into
  the Execution Log, because the pick list already answered it. The database
  lines of the site cache refresh also move to the Debug Log panel. A site that
  cannot be found, and any database warning, still appear in the Execution Log
  (#3232).
