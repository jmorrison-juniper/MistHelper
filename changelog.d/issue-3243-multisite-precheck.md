### Added

- Issue #3243: the multi-site confirm page of the upgrade capture portal now shows the card "Pre-check captures". The card shows one row for each selected site, with the capture link, the tier, and the state. The operator takes each missing pre-check capture, or a new capture for each site, from the same page, in tier 2 or tier 3.
- Issue #3243: the multi-site progress page lists the pre-check capture of each site, with a link to the capture page.

### Changed

- Issue #3243: a multi-site upgrade now needs a verified pre-check capture for each selected site, as a single-site upgrade does. The confirmation field stays disabled until each site holds a capture. The start route refuses with 409 `pre_capture_missing` and names each site that holds no capture.
- Issue #3243: the store reads only seven fields of the newest pre-check capture, and not the whole document. For a site with 35 pre-check captures, one read moves 221 bytes instead of 49,141 bytes.
