# Research: Reject Failed HTTP Data in Rogue DHCP Scans

## Decision

Check the Mist SDK response status before calling `mistapi.get_all`. Accept an SDK response only when its status is an integer from 200 through 299.

## Rationale

The rogue DHCP scanner currently passes every response to pagination. The SDK can expose error data that contains a plausible alarm. The scanner must not treat that data as evidence.

The existing organization security posture source checks failed HTTP responses before it reads response data. This scanner needs stricter handling because an empty result could appear to mean that no rogue DHCP signal exists. Raising at the read boundary preserves the current error behavior. The site fan-out already records a site failure.

## Alternatives Considered

- Return an empty list for failed responses. This hides an incomplete scan as a clean result.
- Filter rows after pagination. This still lets failed response data enter the scanner.
- Add another transport or endpoint. The existing SDK provides the required response status.

## Evidence

- `src/operations/protection/security/rogue_dhcp/scanner.py` calls the paginator without checking the SDK status.
- `src/mist/intelligence/reports/org_security_posture/io/sources.py` rejects failed HTTP response data before parsing it.
- The scanner's `_fan_out` method records raised site errors in `sites_failed`.
