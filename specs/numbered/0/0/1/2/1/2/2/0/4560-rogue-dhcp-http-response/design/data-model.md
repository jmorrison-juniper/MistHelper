# Data Model: Reject Failed HTTP Data in Rogue DHCP Scans

## Scan response

One result from a Mist SDK search.

| Field | Meaning | Validation |
|---|---|---|
| HTTP status | The result of the request | SDK responses require an integer from 200 through 299 before pagination |
| Response data | Records returned by the request | Read only after the status passes validation |

## Rogue DHCP finding

One record that the scanner accepts as evidence.

| Field | Meaning | Validation |
|---|---|---|
| Source | The Mist search that returned the record | The response must have a successful status |
| Site identifier | The site named by the record | Existing scanner validation remains unchanged |
| Alarm or event data | The signal the scanner normalizes | Failed response data cannot create a finding |

No stored schema or export format changes.
