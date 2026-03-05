# API Contracts: Web Portal Interactivity

**Feature**: 006-web-interactivity  
**Date**: 2026-03-04

## New Endpoints

### GET /api/operations/parameters/{menu_number}

Returns parameter requirements for a specific operation.

**Response 200**:
```json
{
  "menu_number": "31",
  "description": "Export device list for a selected site",
  "category": "interactive",
  "parameters": [
    {
      "name": "site_id",
      "label": "Site",
      "param_type": "site",
      "required": true,
      "depends_on": null,
      "device_filter": null,
      "options": null,
      "default": null,
      "placeholder": null
    }
  ]
}
```

**Response 200 (CLI-only)**:
```json
{
  "menu_number": "79",
  "description": "Interactive CLI shell",
  "category": "cli_only",
  "parameters": [],
  "cli_only_message": "Interactive CLI shell requires persistent keyboard input. Use SSH access on port 2200."
}
```

**Response 200 (non-interactive)**:
```json
{
  "menu_number": "11",
  "description": "Export a list of all sites in the organization",
  "category": "non_interactive",
  "parameters": []
}
```

**Response 404**:
```json
{
  "error": "Operation 999 not found"
}
```

---

### GET /api/operations/sites

Returns list of organization sites for site selector dropdowns.

**Response 200**:
```json
{
  "sites": [
    {
      "id": "d1234567-abcd-1234-efgh-567890abcdef",
      "name": "NYC-Office-Floor1",
      "address": "123 Main St, New York, NY",
      "country_code": "US",
      "timezone": "America/New_York"
    }
  ],
  "total_count": 42
}
```

**Response 200 (empty org)**:
```json
{
  "sites": [],
  "total_count": 0
}
```

---

### GET /api/operations/sites/{site_id}/devices?type={device_type}

Returns devices at a site, filtered by type.

**Query parameters**:
- `type` (optional): `ap`, `switch`, `gateway`, `all` (default: `all`)

**Response 200**:
```json
{
  "devices": [
    {
      "id": "00000000-0000-0000-1000-aabbccddeeff",
      "mac": "aa:bb:cc:dd:ee:ff",
      "name": "AP-Floor1-NE",
      "model": "AP45",
      "type": "ap",
      "status": "connected"
    }
  ],
  "total_count": 15,
  "site_id": "d1234567-abcd-1234-efgh-567890abcdef"
}
```

---

### GET /api/operations/sites/{site_id}/clients

Returns clients at a site (wireless + wired merged).

**Response 200**:
```json
{
  "clients": [
    {
      "mac": "11:22:33:44:55:66",
      "hostname": "laptop-jmorrison",
      "ip": "10.0.1.42",
      "type": "wireless",
      "ssid": "CorpWiFi",
      "ap_name": "AP-Floor1-NE"
    }
  ],
  "total_count": 87,
  "site_id": "d1234567-abcd-1234-efgh-567890abcdef"
}
```

---

### POST /api/operations/run (Modified)

Existing endpoint, now accepts `input_answers` in parameters.

**Request body**:
```json
{
  "menu_number": "31",
  "parameters": {
    "input_answers": ["NYC-Office-Floor1"]
  }
}
```

**Response 202** (unchanged):
```json
{
  "run_id": "uuid-here",
  "menu_number": "31",
  "description": "Export device list for a selected site",
  "status": "pending"
}
```

---

## Modified Endpoints

### GET /api/operations/list (Enhanced)

Now includes `category` field per operation.

**Response 200**:
```json
{
  "categories": [
    {
      "name": "Site Data Exports",
      "operations": [
        {
          "menu_number": "31",
          "description": "Export device list for a selected site",
          "category": "interactive"
        },
        {
          "menu_number": "11",
          "description": "Export a list of all sites in the organization",
          "category": "non_interactive"
        }
      ]
    }
  ],
  "total_count": 65
}
```

---

## Existing Endpoints (Reused)

### GET /api/data/preview/{filepath}

Used by the modal preview component. No changes needed.

**Query parameters**: `page`, `per_page`, `search`

### GET /api/data/preview/{filepath}/{table_name}

SQLite table preview. No changes needed.

### GET /api/data/download/{filepath}

File download. No changes needed.

### GET /api/maps/sites

Existing site list for map viewer — may be reused by operations site dropdown to avoid duplication.
