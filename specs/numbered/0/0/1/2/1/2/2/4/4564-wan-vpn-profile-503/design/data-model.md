# Data Model: Reject Profiles from Failed Responses

## Profile Response

The profile response has two relevant values:

| Value | Meaning | Rule |
|---|---|---|
| HTTP status | Whether the profile request succeeded | Only a successful status permits profile data to be used. |
| Response body | Profile records or an error result | Ignore profile records when the HTTP status is unsuccessful. |

## Gateway Profile

A gateway profile is an existing Mist profile that the operator may select for a VPN. The feature does not change its fields, identity, or relationship to a VPN.
