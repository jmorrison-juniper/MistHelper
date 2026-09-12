# createOrgAlarmTemplate

> createOrgAlarmTemplate

## HTTP

`POST /api/v1/orgs/{org_id}/alarmtemplates`

## Description

Available rules can be found in [List Alarm Definitions#]($e/Events%20Definitions/listAlarmDefinitions)

The delivery dict is only required if different from the template delivery settings.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "delivery": {
      "type": "object",
      "properties": {
        "additional_emails": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of additional email string to deliver the alarms via emails"
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether to enable the alarm delivery via emails or not",
          "examples": [
            true
          ]
        },
        "to_org_admins": {
          "type": "boolean",
          "description": "Whether to deliver the alarms via emails to Org admins or not",
          "examples": [
            true
          ]
        },
        "to_site_admins": {
          "type": "boolean",
          "description": "Whether to deliver the alarms via emails to Site admins or not",
          "examples": [
            false
          ]
        }
      },
      "required": [
        "enabled"
      ],
      "description": "Delivery object to configure the alarm delivery"
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "Some string to name the alarm template",
      "examples": [
        "default"
      ]
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "rules": {
      "type": "object",
      "additionalProperties": {
        "title": "alarm_template_rule",
        "type": "object",
        "properties": {
          "delivery": {
            "type": "object",
            "properties": {
              "additional_emails": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "List of additional email string to deliver the alarms via emails"
              },
              "enabled": {
                "type": "boolean",
                "description": "Whether to enable the alarm delivery via emails or not",
                "examples": [
                  true
                ]
              },
              "to_org_admins": {
                "type": "boolean",
                "description": "Whether to deliver the alarms via emails to Org admins or not",
                "examples": [
                  true
                ]
              },
              "to_site_admins": {
                "type": "boolean",
                "description": "Whether to deliver the alarms via emails to Site admins or not",
                "examples": [
                  false
                ]
              }
            },
            "required": [
              "enabled"
            ],
            "description": "Delivery object to configure the alarm delivery"
          },
          "enabled": {
            "type": "boolean"
          }
        }
      },
      "description": "Alarm Rules object to configure the individual alarm keys/types. Property key is the alarm name.",
      "examples": [
        {
          "ap_offline": {
            "delivery": {
              "additional_emails": [
                "string"
              ],
              "enabled": true,
              "to_org_admins": true,
              "to_site_admins": true
            },
            "enabled": true
          },
          "bad_cable": {
            "delivery": {
              "additional_emails": [
                "string"
              ],
              "enabled": true,
              "to_org_admins": true,
              "to_site_admins": true
            },
            "enabled": true
          }
        }
      ]
    }
  },
  "required": [
    "delivery",
    "rules"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "delivery": {
      "type": "object",
      "properties": {
        "additional_emails": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of additional email string to deliver the alarms via emails"
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether to enable the alarm delivery via emails or not",
          "examples": [
            true
          ]
        },
        "to_org_admins": {
          "type": "boolean",
          "description": "Whether to deliver the alarms via emails to Org admins or not",
          "examples": [
            true
          ]
        },
        "to_site_admins": {
          "type": "boolean",
          "description": "Whether to deliver the alarms via emails to Site admins or not",
          "examples": [
            false
          ]
        }
      },
      "required": [
        "enabled"
      ],
      "description": "Delivery object to configure the alarm delivery"
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "Some string to name the alarm template",
      "examples": [
        "default"
      ]
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "rules": {
      "type": "object",
      "additionalProperties": {
        "title": "alarm_template_rule",
        "type": "object",
        "properties": {
          "delivery": {
            "type": "object",
            "properties": {
              "additional_emails": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "List of additional email string to deliver the alarms via emails"
              },
              "enabled": {
                "type": "boolean",
                "description": "Whether to enable the alarm delivery via emails or not",
                "examples": [
                  true
                ]
              },
              "to_org_admins": {
                "type": "boolean",
                "description": "Whether to deliver the alarms via emails to Org admins or not",
                "examples": [
                  true
                ]
              },
              "to_site_admins": {
                "type": "boolean",
                "description": "Whether to deliver the alarms via emails to Site admins or not",
                "examples": [
                  false
                ]
              }
            },
            "required": [
              "enabled"
            ],
            "description": "Delivery object to configure the alarm delivery"
          },
          "enabled": {
            "type": "boolean"
          }
        }
      },
      "description": "Alarm Rules object to configure the individual alarm keys/types. Property key is the alarm name.",
      "examples": [
        {
          "ap_offline": {
            "delivery": {
              "additional_emails": [
                "string"
              ],
              "enabled": true,
              "to_org_admins": true,
              "to_site_admins": true
            },
            "enabled": true
          },
          "bad_cable": {
            "delivery": {
              "additional_emails": [
                "string"
              ],
              "enabled": true,
              "to_org_admins": true,
              "to_site_admins": true
            },
            "enabled": true
          }
        }
      ]
    }
  },
  "required": [
    "delivery",
    "rules"
  ],
  "description": "Alarm Template"
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Syntax |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.alarm_templates.createOrgAlarmTemplate()`

## Usage Context

Creates a new alarm template for the organization.

## Gotchas

- Alarm templates define which alarms trigger and their notification rules.

## Related Endpoints

- [GET_orgs_org_id_alarmtemplates.md](GET_orgs_org_id_alarmtemplates.md) — List templates
- [PUT_orgs_org_id_alarmtemplates_alarmtemplate_id.md](PUT_orgs_org_id_alarmtemplates_alarmtemplate_id.md) — Update template

## MistHelper Notes

Not currently used by MistHelper directly.
