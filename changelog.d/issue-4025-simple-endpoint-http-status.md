### Fixed

- The simple endpoint exporter now reads the HTTP status of each Mist answer. A non-2xx answer, such as
  the HTTP 404 that menus 260 and 261 receive, now logs
  `! Error fetching <operation>: HTTP <code> from <url>` and ends the web portal run as failed. Before
  this change the exporter reported `! No <operation> data found`, which is the same wording a genuinely
  empty organization produces, so the portal reported `Complete` for an upstream failure (issue #4025).
