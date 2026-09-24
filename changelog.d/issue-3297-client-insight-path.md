### Fixed

- Menu 75 now exports the client insight metrics. The Mist cloud answers the SDK request with HTTP 404 and an empty body, so menu 75 always reported that no data was available. Menu 75 now requests each metric from the path form that the cloud serves. If the Mist API refuses a metric, menu 75 names the metric, the HTTP status, and the reason. Issue #3297 records the live probe.
