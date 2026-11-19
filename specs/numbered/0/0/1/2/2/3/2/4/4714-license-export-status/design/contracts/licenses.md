# License export contract

`OrgAdminExporter.licenses()` returns `None` after a successful export, an empty result, or an explicit writer rejection.
Request, transform, and writer exceptions propagate without an empty recovery write.
Operator selection occurs before request handling and retains its interrupt behavior.

The initial response must expose `status_code` as an integer from 200 through 299. Boolean values are invalid.
A failed integer status produces an error containing the HTTP status and organization.
A missing or malformed status produces an error without formatting the untrusted status object.
Only validated responses reach direct data access or the existing SDK pagination function.

The writer receives the existing flattened and escaped records with endpoint metadata `listOrgLicenses`.
An explicit `False` result logs an error and suppresses the completion message.
An empty result does not call the writer because the shared writer rejects empty input.

Later SDK page validation is not part of this contract.
