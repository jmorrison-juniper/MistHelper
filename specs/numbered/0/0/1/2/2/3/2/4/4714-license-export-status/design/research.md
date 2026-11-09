# License response decisions

## Decision

Require an integer status from 200 through 299 before consuming the initial response. Reject Boolean values.

## Rationale

The original direct path consumes error dictionaries. The wrapper path passes an unchecked response to `mistapi.get_all`.
The shared writer rejects empty input and returns a Boolean result.
The existing exporter ignores that result and attempts an empty recovery write after exceptions.

## Alternatives considered

Shared fetcher status helpers allow missing or malformed statuses for legacy doubles. They do not meet this repair's strict requirement.
Changing shared pagination would alter other operations and violate the reservation.
Raising on writer rejection would change the public error behavior unnecessarily. An error log and `None` result preserve that behavior.

## Evidence

The assigned source and existing unit tests establish both endpoint paths and public behavior.
Local inspection of installed mistapi 0.64.1 confirms that `get_all` consumes subsequent page data without this exporter's status validation.
This repair validates the initial response only. Later-page status validation remains a separate limitation.
