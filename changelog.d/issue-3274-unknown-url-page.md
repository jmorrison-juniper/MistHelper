### Fixed

- The upgrade capture portal now answers a browser page view of a wrong address with status 404 and an error page. The browser showed the raw JSON text `{"error":{"code":"not_found",...}}` with no portal layout. The page states that the portal holds no page at the address, and it links to the site list. A refused method and an unexpected fault also show the error page to a browser. The portal script, a JSON client, and a request from outside the address allow list still receive the JSON envelope (#3274).
