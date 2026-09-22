### Fixed

- The web portal no longer deadlocks when the event bus reports a dropped
  event. The bus held its own lock while it wrote that report through the
  logging framework. The portal installs a log handler that publishes into the
  bus, so the report re-entered the bus on the same thread and waited for a
  lock that thread already held. Every request thread then blocked behind the
  logging lock, and the portal answered nothing until a restart. Issue #3177.
