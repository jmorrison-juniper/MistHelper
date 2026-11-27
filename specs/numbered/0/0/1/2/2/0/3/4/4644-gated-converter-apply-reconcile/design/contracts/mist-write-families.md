# Contract: Mist Write Families

This contract lists the apply families for issue 4644. Each family starts disabled. A family is enabled only after its gates pass and decision D-17 closes. Source for each path: `documentation/mist-api-openapi31yaml.yaml`. Source for each SDK method: the pinned `mistapi` 0.64.1 package in `.venv\Lib\site-packages\mistapi\api\v1\`.

## Registered Write Families

| ID | Action | Mist operation | OpenAPI line | SDK method and file line | Allow-list |
| --- | --- | --- | --- | --- | --- |
| F-01 | create | `POST /api/v1/orgs/{org_id}/sites`, `createOrgSite` | 20047 | `orgs/sites.py` line 58 | Empty until gate G2 |
| F-02 | update | `PUT /api/v1/sites/{site_id}`, `updateSiteInfo` | 26004 | `sites/sites.py` line 67 | Empty until gate G2 |
| F-03 | update | `PUT /api/v1/sites/{site_id}/setting`, `updateSiteSettings` | 37086 | `sites/setting.py` line 42 | Empty until gate G2 |
| F-04 | create | `POST /api/v1/orgs/{org_id}/gatewaytemplates`, `createOrgGatewayTemplate` | 9764 | `orgs/gatewaytemplates.py` line 58 | `name`, `type`, `dns_servers` |
| F-05 | update | `PUT /api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}`, `updateOrgGatewayTemplate` | 9951 | `orgs/gatewaytemplates.py` line 145 | Same as F-04 |
| F-06 | create | `POST /api/v1/orgs/{org_id}/deviceprofiles`, `createOrgDeviceProfile` | 7988 | `orgs/deviceprofiles.py` line 63 | Empty until gate G2 |
| F-07 | update | `PUT /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}`, `updateOrgDeviceProfile` | 8187 | `orgs/deviceprofiles.py` line 150 | Empty until gate G2 |
| F-08 | assign | `POST /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}/assign`, `assignOrgDeviceProfile` | 8370 | `orgs/deviceprofiles.py` line 182 | Empty until gate G2 |

The allow-list for F-04 comes from the parent contract `mist-apply.md`, lines 11 and 13. It names the verified fields only.

Warning: The allow-lists for F-01, F-02, F-03, F-05, F-06, F-07, and F-08 stay empty until issue 4634 supplies field evidence. An empty allow-list refuses every change item for that family.

## Read Operations for Reconciliation

| ID | Mist operation | OpenAPI line | SDK method and file line |
| --- | --- | --- | --- |
| R-a | `GET /api/v1/sites/{site_id}`, `getSiteInfo` | 25978 | `sites/sites.py` line 17 |
| R-b | `GET /api/v1/sites/{site_id}/setting`, `getSiteSetting` | 37065 | `sites/setting.py` line 17 |
| R-c | `GET /api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}`, `getOrgGatewayTemplate` | 9929 | `orgs/gatewaytemplates.py` line 89 |
| R-d | `GET /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}`, `getOrgDeviceProfile` | 8164 | `orgs/deviceprofiles.py` line 94 |
| R-e | `GET /api/v1/orgs/{org_id}/sites`, `listOrgSites`, paginated | 20022 | `orgs/sites.py` line 17 |

## Call Rules

- Each call passes the session first, then the path arguments, then the body. The adapter names each argument.
- A call never forwards `*args` or `**kwargs`.
- A list call reads every page before the duplicate-name check.
- A write call runs under the bound from decision D-8. The call never repeats after an outcome.
