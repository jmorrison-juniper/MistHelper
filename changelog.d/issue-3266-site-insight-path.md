### Fixed

- Menu 74 now exports the site insight metrics. The Mist cloud answers the SDK request with HTTP 404 and an empty body, so menu 74 always reported that no data was available. Menu 74 now requests each metric from the path form that the cloud serves. If the Mist API refuses a metric, menu 74 names the metric, the HTTP status, and the reason. A refused metric no longer becomes a record in the export. Issue #3266 records the live probe.
