### Fixed

- Create the declared ArangoDB field indexes before exporter writes. Report failed index creation and retry incomplete checks without changing stored records. Fixes #3309.
