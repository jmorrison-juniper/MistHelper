# Research: MistDSW Migration

## Source Evidence

**Repository**: [jmorrison-juniper/MistDSW](https://github.com/jmorrison-juniper/MistDSW)
**Inspected revision**: `dd51eba16319eeb960ec6e13c813c1fbf9872e50`
**Inspection date**: 2026-10-15

Each source link below uses the inspected revision.
Inspection used GitHub repository metadata, the recursive tree, and raw contents responses.
No source file, dataset, template, or test was copied into MistHelper.

| Evidence | Finding |
| --- | --- |
| [README](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/README.md) | Four CLI generators, Python 3.9+, no GUI, and standard-library dependencies. |
| [User guide](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/docs/user-guide.md) | Addressing plan, commands, site-variable names, gateway ports, and manual deployment sequence. |
| [CSV generator](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/snips_to_mist_csv.py) | Single-store and TSV modes, normalization, explicit gateways, DHCP exclusion, and transposed CSV. |
| [Switch generator](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/templatize_branch_json.py) | Replaces four named networks' VLAN and subnet fields. Preserves other fields, including metadata. |
| [Gateway generator](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/templatize_gateway_json.py) | Replaces IP and DHCP configurations, chooses the first LAN port, rewrites tenants, and removes four metadata fields. |
| [Network generator](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/generate_network_payloads.py) | Creates ten networks and one combined reference. Prints an embedded organization identifier but sends no request. |
| [Regression tests](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/tests/test_mistdsw.py) | Nine offline unittest cases. No browser tests or HTTP tests. |
| [Test workflow](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/.github/workflows/tests.yml) | Runs unittest discovery on Python 3.9 for PRs, main pushes, and manual requests. |
| [Combined networks](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/network_payloads/all_networks.json) | Four variable-based networks and six static networks. Guest uses VLAN 2000. |
| [Combined services](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/network_payloads/all_services.json) | Four custom services use variable subnet references and protocol `any`. |
| [Switch example](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/Branch-Master-Template.json) | Contains organization metadata and network settings. Realo shares the Imbox subnet in this example. |
| [Gateway example](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/Gateway-Spoke-Template.json) | Ten IP configurations, ten DHCP blocks, three WAN ports, and one LAN port. |
| [IP block example](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/network_payloads/ip_configs.json) | Uses a top-level `ip_configs` wrapper. |
| [DHCP block example](https://github.com/jmorrison-juniper/MistDSW/blob/dd51eba16319eeb960ec6e13c813c1fbf9872e50/network_payloads/dhcpd_config.json) | Uses a top-level `dhcpd_config` wrapper. |

The earlier README request timeout did not recur.
`gh api repos/jmorrison-juniper/MistDSW/readme -H 'Accept: application/vnd.github.raw+json'` returned the complete README.
All required source categories were accessible.
The license endpoint returned HTTP 404. Metadata reported `licenseInfo: null`.
The complete source tree contained no license file.
These results mean that reuse permission remains unavailable.
The source tests were inspected, not executed. Their result is unknown.
No installed dependency list or performance measurement exists in the source evidence.

## Decision: Reuse Requires Permission

**Decision**: Treat MistDSW source, assets, templates, and tests as unlicensed until documented permission proves otherwise.
**Rationale**: Public visibility and common ownership do not establish a redistribution license.
**Alternatives considered**: Direct copying and assumed MIT licensing are rejected.

Blocker B1 requires written permission or a license covering the pinned revision and each proposed material.
Record attribution, notice, distribution, modification, and third-party restrictions before reuse.
Customer exports and embedded identifiers require separate data-owner approval.
A later independently written implementation can use approved behavior contracts and synthetic fixtures.
It must not reproduce source expression or customer data.
The owner must approve that route explicitly.

## Decision: Preserve Preparation, Not Automatic Deployment

**Decision**: Preserve the four offline workflows and add service-output preparation.
**Rationale**: Source deployment is a manual guide, not a built-in API client.
**Alternatives considered**: Automatic template upload and network creation would add destructive behavior without source evidence or user authorization.

No source imports mistapi, Redis, database drivers, or a web framework.
Runtime dependencies are `argparse`, `csv`, `ipaddress`, `json`, filesystem support, and other standard-library modules.
Tests also use `subprocess`, `tempfile`, and `unittest`.
Retain behavior tests inside MistHelper pytest. Do not copy the source workflow YAML.
Do not add a Python 3.9 runtime, a second CI pipeline, or a source-specific container.

## Decision: Explicit Profiles Resolve Source Conflicts

| Conflict | Source evidence | Required disposition |
| --- | --- | --- |
| Guest VLAN | Guide says 200. CSV uses 200. Network generator and switch example use 2000. | B2 requires one approved VLAN per profile. |
| Guest subnet | CSV uses `192.168.200.0/24`. Guide and network payloads use `192.168.222.0/24`. | B2 requires one approved subnet and matching gateway. |
| Realo subnet | Switch example uses `192.168.204.0/24`. Network and gateway outputs use `192.168.205.0/24`. | B2 requires one approved subnet without unintended Imbox overlap. |
| Services | Guide and examples include services. Network generator does not write them. | Add explicit service generation and tests. |
| Mixed tenants | Gateway generator replaces a policy's entire tenant list when `lan` appears. | Require reviewed policy mapping. Preserve unrelated tenants. |
| LAN selection | Gateway generator chooses the first LAN port. | Require explicit selection if several ports qualify. |
| Metadata | Switch generator retains metadata. Gateway generator removes four fields. | Show sanitized artifact metadata rules before export. |

**Rationale**: Selecting one conflicting value silently can change a production addressing plan.
**Alternatives considered**: Automatic source precedence and hardcoded production profiles are rejected.

## Decision: Existing Portal and Database

**Decision**: Add a preparation page to the existing Flask web portal on port 8055.
Preserve unattended CLI preparation through the same application.
Use the configured ArangoDB logical database for run metadata.

**Rationale**: The source has no UI to preserve. The current portal already provides operations, themes, and shared dependencies.
**Alternatives considered**: A separate ops-portal service, copied GUI, standalone app, Redis state store, and separate SQLite file add unnecessary ownership.

Local evidence: `web_portal/app.py` registers Flask blueprints and provides shared dependencies and security middleware.
`compose.yml` has one `misthelper` application service and the existing ArangoDB and Redis services.
`src/foundation/persistence/db/router.py` routes document records to ArangoDB.
`DatabaseConfig` uses `ARANGO_DATABASE`, with `misthelper` as its default.
Existing SQLite export support remains unchanged. This feature does not introduce a second authoritative run store.
Private artifacts are files under `data/`, not a new database.

## Decision: Explicit Failure and Privacy

**Decision**: Require ownership checks, bounded inputs, 24-hour expiration, and verified private exports.
**Rationale**: Customer templates can contain credentials and private network data.
**Alternatives considered**: Public static downloads, unbounded uploads, and database-to-file success fallbacks are rejected.

Blocker B3 requires proof that portal identity and download ownership work together.
Existing CSRF middleware is evidence of request protection, not proof of operator authorization.
Blocker B4 requires local schema checks against the approved Mist export and payload shapes.
No live write is permitted to obtain that evidence.
