# Request Body Contracts

## Claim

Operation `claimOrgMxEdge` sends:

```json
{"code":"135-546-673"}
```

## Assign

Operation `assignOrgMxEdgeToSite` sends:

```json
{"mxedge_ids":["387804a7-3474-85ce-15a2-f9a9684c9c90"],"site_id":"4ac1dcf4-9d8b-7211-65c4-057819f0862b"}
```

## Unassign

Operation `unassignOrgMxEdgeFromSite` sends:

```json
{"mxedge_ids":["387804a7-3474-85ce-15a2-f9a9684c9c90"]}
```

## Bounce data ports

Operation `bounceOrgMxEdgeDataPorts` sends:

```json
{"ports":["0","2"]}
```

## Upgrade

Operation `upgradeOrgMxEdges` sends:

```json
{"mxedge_ids":["387804a7-3474-85ce-15a2-f9a9684c9c90"],"strategy":"serial","versions":{"tunterm":"default"}}
```
