# Contract: Refused Multi-Site Options Save

## Endpoint

The save endpoint is `POST /api/org-upgrades/options`. The route constant `OPTIONS_API_PATH` names it at `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py:145` [RC16]. The browser form posts to the same path at `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html:91` [RC45].

## Request Fields That Drive the Rule

- `selected_types`: the checked device types. The allowed values are `ap`, `switch`, and `gateway`, as the template labels them at line 98 [RC46].
- `targets`: the explicit list of device addresses and target versions. The browser sends only enabled, non-empty choices [RC43].
- `version_ap`, `version_switch`, and `version_gateway`: the older type-wide version fields. `_selected_target_rows` reads them when no `targets` list arrives [RC23].

## Refusal Response (New Condition)

- HTTP status: `400`.
- Body: `{"error": {"code": "org_upgrade_options_invalid", "message": "Choose the switch target version, or clear Switches."}}`.
- Envelope: the body comes from `json_error` at `src/interfaces/portals/upgrade_portal/app/factory.py:322` [RC39]. The contract tests read `error.code` and `error.message` [RC102, RC103].
- Message form: `Choose the {noun} target version, or clear {label}.` The pairs are access point and Access points, switch and Switches, and gateway and Gateways [RC46].
- Side effects: none. The save stores no aggregate plan [RC30] and makes no browser session write [RC29].

## Success Response (Unchanged)

- HTTP status: `200`.
- Body: `{"next": "/upgrade/org/confirm"}`. The route answers the confirmation path at `org_upgrade.py:1235` [RC104]. The contract test asserts that answer [RC105]. The constant is at line 34 of the test module [RC101].

## Compatibility

- The change adds one refusal condition. The HTTP status and the code stay the same as the existing refusals [RC17].
- No field is added to or removed from a successful response.
- Existing refusals keep their messages.
