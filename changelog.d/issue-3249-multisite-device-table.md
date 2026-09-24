### Added

- The multi-site progress page of the upgrade capture portal now shows one row for each device of each site (issue #3249). Each row shows the site, the name, the MAC address, the type, and the state. Each row also shows the version before, the target version, the version after, the version check, and the failure reason. The page also shows the typed operator address, the Mist account, and the age of the last update. The version after is the running version from `listSiteDevicesStats`, and the portal reads a site only when a device of that site needs a reading.
