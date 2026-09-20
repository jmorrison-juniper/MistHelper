### Fixed

- The operations portal now reports every file an operation wrote. The portal
  used to read the file name out of the log prose, and it accepted three
  sentences and four extensions. An operation that wrote a Markdown report and
  logged `Mermaid report: data/OrgAuditAnalysis.md` therefore listed no file at
  all, and the engineer read an empty result panel. The portal now compares the
  data directory before and after the run, so a report reaches the panel even
  when no log line names it. Issue #3089.
