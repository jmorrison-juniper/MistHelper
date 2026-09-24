### Added

- The multi-site upgrade page of the capture portal now follows each cascade phase until its devices settle, as the single-site page does (issue #3245). The page shows a "Cascade phases" card with the gateways, the switches, the access points, and the wireless clients. The poll continues while a phase still waits for its devices, so the page no longer reads "completed" while the devices reboot.
- The submission reads the uptime of each device before the first firmware write. If the read fails, the page names the count of devices with no uptime, and the upgrade continues.
- A cancel stops the phase watch, and the page shows "Stopped". A portal restart resumes the watch from the first phase that did not end.
