### Fixed

- The progress page of a final multi-site upgrade shows no cancel form. The portal refuses a cancel request for it with the code `org_upgrade_not_cancellable` and the HTTP status 409, and it sends no request to Mist. A poll that reports a final state closes the form. Issue #3225.
- The Cancellation column of the multi-site site table shows one text in the first render and in each poll. The family, site, type, and state cells no longer break a word inside its letters at a narrow width. Issue #3225.
