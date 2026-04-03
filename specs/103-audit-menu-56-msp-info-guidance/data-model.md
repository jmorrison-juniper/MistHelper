# data-model.md

This feature touches runtime structures rather than persistent storage. The data model below documents the key in-memory entities relevant to the MSP selection and export flow.

Entities

1) msp_privilege (dict)
- Description: One entry per MSP the user has visibility into.
- Fields:
  - msp_id: string (primary identifier)
  - msp_name: string
  - role: string (e.g., "superuser", "admin")
- Constraints / validation:
  - msp_id: non-empty string
  - msp_name: non-empty string

2) apisession (opaque)
- Description: Mist API session object used to call mistapi.v1.msps.orgs.listMspOrgs
- Validation: must be not None before calling API; tests mock this object.

3) response (object)
- Description: API response expected to have attribute `data`.
- Expected shape: response.data is list-like (list/tuple) of org dicts.

4) org record (dict)
- Description: organization data returned from API
- Fields (expected):
  - id: string (may be None or short)
  - name: string
  - ... other metadata fields returned by API
- Normalization rules:
  - For export, each record will be flattened; missing 'id' or 'name' will be filled with placeholders: '(missing-id)' and '(missing-name)'.
  - Added fields: msp_id (string), msp_name (string) added by processing step.

State transitions

- Initial: msp_privileges loaded from environment/context
- After selection: chosen_msp context available with msp_id and msp_name
- After API call: response -> orgs_data (normalized list) -> processed (flattened and escaped) -> CSV output written via DataExporter


---

End of data-model.md
