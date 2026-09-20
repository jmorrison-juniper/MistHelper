### Fixed

- The results panel no longer lists runtime bookkeeping files beside the
  report. A run that wrote one report listed `script.log`, `portal_access.log`,
  `delay_metrics.json`, and `tuning_data.json` as well, so the engineer had to
  pick the report out of a list that changed on every run. The scanner now
  skips the files the runtime writes, including a rotated log. A file that a
  log line names explicitly still reaches the panel. Issue #3126.
