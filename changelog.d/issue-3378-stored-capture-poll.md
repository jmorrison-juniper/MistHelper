### Fixed

- The page of a stored capture now stops its status poll after the first answer. The status of a stored capture held the content word `complete` or `partial`, which the page does not treat as an end state. Therefore, an idle tab read the whole capture from the store every 3 seconds with no end. The status now sends `verified` when the stored capture passed its read-back check and this release can compare it. It sends `failed` in every other case (issue #3378).

- The precheck card of the multi-site mode reads the same status. If the portal restarted during a precheck, the card waited at that site with no end. The card now accepts the stored capture (issue #3378).
