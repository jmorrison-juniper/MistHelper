### Added

- The multi-site upgrade portal can retry the devices that did not reach the target version. The retry opens a new plan with only those devices and the earlier choices, and it never writes firmware before the typed confirmation. Issue #3247.
- The multi-site progress page can check each child job with an uncertain outcome against the running versions. A child job completes only with complete proof, and the page shows the evidence of each check. Issue #3247.
- The multi-site confirmation page can move the start time of a plan before the typed confirmation. The move uses the start time window of the single-site page, and it refuses a request that holds no start time field. Issue #3247.

### Fixed

- The hint under a typed-word field no longer asks for capital letters when the word holds small letters. The hint now tells the operator to copy the capital and small letters of the page. Issue #3247.
