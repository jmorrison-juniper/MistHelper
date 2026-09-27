### Fixed

- The upgrade capture portal now makes the noun agree with each count in two
  notes (issue #3449). For one match, the organization picker note says "1
  organization" and not "1 organizations". For one capture, the capture history
  note says "1 capture" and not "1 captures". The second sentence of each note
  names the noun, and it no longer says "of them". A page size of one reads as
  "1 row". A count of zero, or of two or more, keeps the plural noun. Each note
  also carries a test identifier, `org-search-note` or `history-count-note`.
