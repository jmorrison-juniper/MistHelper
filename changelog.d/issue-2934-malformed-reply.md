### Fixed

- A malformed reply from the Mist cloud no longer reads as an empty result. The
  `mistapi` SDK catches every parse error inside `APIResponse`, so the caller saw
  HTTP 200 with an empty payload and could not tell a broken reply from an empty
  site. MistHelper now reads the pair of fields the SDK leaves behind and reports
  a failure at four read boundaries. A firmware decision can no longer read a
  broken reply as a site that needs no work. See issue #2934.
