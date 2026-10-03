# Contract: Webhook response refusals

The controlled host is `api.mist.com`, in the US cloud.
The existing operations remain `searchOrgWebhooksDeliveries` and directly coupled `listOrgWebhooks`.

## Accepted page

The page has a reliable integer HTTP status in the successful `200` through `299` range.
Boolean, missing, unreadable, and malformed statuses are not successful statuses.
The wire body is readable and nonblank.
The SDK body integrity signal does not report a parse failure.
The parsed payload is a record list or a dictionary with a `results` record list.
Every record is an object.
The next link is absent, empty, or a readable string from the SDK contract.

The collector passes the original next link to native `mistapi.get_next`.
It retains the page order and original record values.
It does not synthesize pagination links or replace SDK errors.

## Refused page

Any failed status, unavailable status, malformed body, unsupported shape, or unusable pagination result refuses the complete export.
The exporter emits an ERROR record with safe resource and page context.
The log states the number of response pages checked.
The refusal does not call persistence or final output.
It does not print a successful empty-result notice.
It does not print an exported-record success notice.
It does not expose raw bodies, credentials, or private exception text.

## Successful empty result

A successful `[]` or `{"results":[]}` collection retains the existing empty-data notice.
Discovery retains its configured-empty notice only after a successful collection.
A failed response with zero rows is not a valid empty result.

## Output compatibility

The existing normalization, multiline escaping, filename, and output selection remain.
The filename remains `OrgWebhookDeliveries_<webhook-name-with-underscores>.csv`.
The metadata remains `api_function_name="searchOrgWebhooksDeliveries"`.
A delivery record's destination status does not replace the cloud response status.
Standalone mode retains the real `written=False` database outcome and its warning.
This repair adds no database-success guarantee.
