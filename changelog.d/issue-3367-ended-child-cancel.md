### Fixed

- Issue #3367: A cancel of a running multi-site upgrade no longer sends a cancel request to a child job that already ended. The cancel result panel now shows the status `already_ended` for that child job, with a note and no device list. Before this repair, the panel listed each upgraded access point as a cancelled device.
