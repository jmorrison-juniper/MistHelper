### Fixed

- An expired session now states its cause and its action. An operator who
  clicked Run after the session expired read
  `Unexpected token '<', "<!doctype "... is not valid JSON`, which named
  neither. The portal now answers an API caller with JSON, and every portal
  script reads an answer through one safe reader, so an HTML page from a proxy
  or from a server error also produces a sentence. A dropdown that cannot load
  now names its reason instead of reading as an empty list. Issue #3087.
