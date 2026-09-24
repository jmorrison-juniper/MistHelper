### Fixed

- The upgrade capture portal now answers an unknown run identifier with status 404 and an error page. The run page, the options page, and the confirm page showed an empty page with status 200 and write controls. The error page names the identifier, shows the error code `run_not_found`, and links to the site list (#3276).
