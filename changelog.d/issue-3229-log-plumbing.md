### Fixed

- The Execution Log no longer shows internal dependency lines such as
  `Resolving source dependency DataExporter`. In a small operation those lines
  filled most of the panel. The Debug Log panel still shows them, and
  `script.log` still records them (#3229).
