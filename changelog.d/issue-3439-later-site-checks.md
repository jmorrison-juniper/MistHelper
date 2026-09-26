### Name an incomplete site list at each later site check

- **Fixed**: The upgrade capture portal no longer tells the operator that a
  site does not exist when the site read lost a page. Before this change, nine
  later steps refused a site of a lost page as unknown. The operator then read
  the wrong cause and chose the sites again.

  Each step now answers the status 503 with the code `site_list_incomplete`.
  The message tells the operator to try again. The site choice, the inventory
  page, the inventory answer, and the capture start use the rule. The options
  page, the options save, the confirm page, the pre-check start, and the retry
  use it too. A refused step changes no stored state. A browser page shows the
  shared error page with a link to the site list. A refused site choice returns
  to the site picker with a Caution message. A whole site list keeps the
  answers of today, and a site of a kept page still passes. Issue #3439.
