### Fixed

- The multi-site save no longer replaces the options of the operator with the defaults when the last selected site holds no device. The save now stops and names each site that it cannot read, or each site that holds no planned device. A retry of the failed devices still saves when a site holds no retry device. A retry still stops when the portal cannot read a site. Issue #3389.
