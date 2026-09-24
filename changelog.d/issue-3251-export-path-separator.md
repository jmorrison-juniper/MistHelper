### Fixed

- The WLAN export of menu 69 and the SLE metric insight export of menu 73 now name the output file with the separator of the platform. In the Linux container, the notice read `! 0 records exported to data\SiteWlans_HQ.csv`, and now reads `! 0 records exported to data/SiteWlans_HQ.csv`. On Windows, each notice stays the same (#3251).
