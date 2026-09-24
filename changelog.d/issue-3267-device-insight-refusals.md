### Fixed

- Menu 76 no longer exports an HTTP 400 error body as a device insight metric row. The summary now counts only the metrics that returned data. After the export, the operator reads each refused metric with its HTTP status and its reason. Issue #3267.
