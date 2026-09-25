### Fixed

- Each multi-site form now sends one request for one click. The page disables the form until the portal answers, so a double click on Start cannot send a second firmware request. If a request started an upgrade before, the refusal links to the progress page of that upgrade and puts the focus on the link. A refusal that started nothing enables the form again, and the typed word stays. A page that the browser shows again from its cache loads again, so no form stays disabled. Issue #3242.
