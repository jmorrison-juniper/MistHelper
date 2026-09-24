### Added

- The multi-site progress page shows a cancellation result for each child job after a cancel. Each child job lists the devices that the cloud canceled, the devices that still write firmware, and the devices with no cancel path. A reload shows the same lists, because the page reads them from the stored operation. Issue #3246.
- The multi-site progress page shows a caution beside the cancel button. The caution states that a device that already writes firmware finishes the write, and that each site can hold two firmware versions after the cancellation. Issue #3246.

### Fixed

- The access point child job of a multi-site cancel now uses the sort rule of the single-site stop. An access point that the last status marks as rebooting stays in the list of devices that still write firmware. Before this change, the portal stored no device list for that child job. Issue #3246.
