### Fixed

- The upgrade capture portal now answers a refused browser form post with status 400 and an error page. The browser showed the raw JSON text `{"error":{"code":"csrf_missing",...}}` when a session ended while a form was open. The page states the cause, shows the error code `csrf_missing`, and links back to the form page. The portal script and a JSON client still receive the JSON envelope (#3275).
- The shared error page of the upgrade capture portal now shows the header links and the sign-out control only to a live session (#3275).
