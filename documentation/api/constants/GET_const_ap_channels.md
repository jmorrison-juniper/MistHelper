# listApChannels

> listApChannels

## HTTP

`GET /api/v1/const/ap_channels`

## Description

Get List of List of Available channels per country code

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| country_code | string | No |  |  | Country code, in two-character |

## Request Body

None.

## Response

### 200

AP Channels

```json
{
  "type": "object",
  "properties": {
    "band24_40mhz_allowed": {
      "type": "boolean",
      "examples": [
        true
      ]
    },
    "band24_channels": {
      "type": "object",
      "additionalProperties": {
        "type": "array",
        "items": {
          "type": "integer",
          "format": "int32"
        },
        "description": "Property key is the channel width",
        "example": {
          "20": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11
          ],
          "40": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11
          ]
        }
      },
      "description": "Property key is the channel width",
      "examples": [
        {
          "20": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11
          ],
          "40": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11
          ]
        }
      ]
    },
    "band24_enabled": {
      "type": "boolean",
      "examples": [
        true
      ]
    },
    "band5_channels": {
      "type": "object",
      "additionalProperties": {
        "type": "array",
        "items": {
          "type": "integer",
          "format": "int32"
        },
        "description": "Property key is the channel width",
        "example": {
          "20": [
            36,
            40,
            44,
            48,
            52,
            56,
            60,
            64,
            100,
            104,
            108,
            112,
            116,
            120,
            124,
            128,
            132,
            136,
            140,
            144,
            149,
            153,
            157,
            161,
            165
          ],
          "40": [
            36,
            40,
            44,
            48,
            52,
            56,
            60,
            64,
            100,
            104,
            108,
            112,
            116,
            120,
            124,
            128,
            132,
            136,
            140,
            144,
            149,
            153,
            157,
            161
          ],
          "80": [
            36,
            40,
            44,
            48,
            52,
            56,
            60,
            64,
            100,
            104,
            108,
            112,
            116,
            120,
            124,
            128,
            132,
            136,
            140,
            144,
            149,
            153,
            157,
            161
          ],
          "dfs": [
            52,
            56,
            60,
            64,
            100,
            104,
            108,
            112,
            116,
            120,
            124,
            128,
            132,
            136,
            140,
            144
          ],
          "outdoor": [
            36,
            40,
            44,
            48,
            52,
            56,
            60,
            64,
            100,
            104,
            108,
            112,
            116,
            120,
            124,
            128,
            132,
            136,
            140,
            144,
            149,
            153,
            157,
            161,
            165
          ]
        }
      },
      "description": "Property key is the channel width",
      "examples": [
        {
          "20": [
            36,
            40,
            44,
            48,
            52,
            56,
            60,
            64,
            100,
            104,
            108,
            112,
            116,
            120,
            124,
            128,
            132,
            136,
            140,
            144,
            149,
            153,
            157,
            161,
            165
          ],
          "40": [
            36,
            40,
            44,
            48,
            52,
            56,
            60,
            64,
            100,
            104,
            108,
            112,
            116,
            120,
            124,
            128,
            132,
            136,
            140,
            144,
            149,
            153,
            157,
            161
          ],
          "80": [
            36,
            40,
            44,
            48,
            52,
            56,
            60,
            64,
            100,
            104,
            108,
            112,
            116,
            120,
            124,
            128,
            132,
            136,
            140,
            144,
            149,
            153,
            157,
            161
          ],
          "dfs": [
            52,
            56,
            60,
            64,
            100,
            104,
            108,
            112,
            116,
            120,
            124,
            128,
            132,
            136,
            140,
            144
          ],
          "outdoor": [
            36,
            40,
            44,
            48,
            52,
            56,
            60,
            64,
            100,
            104,
            108,
            112,
            116,
            120,
            124,
            128,
            132,
            136,
            140,
            144,
            149,
            153,
            157,
            161,
            165
          ]
        }
      ]
    },
    "band5_enabled": {
      "type": "boolean",
      "examples": [
        true
      ]
    },
    "band6_channels": {
      "type": "object",
      "additionalProperties": {
        "type": "array",
        "items": {
          "type": "integer",
          "format": "int32"
        },
        "description": "Property key is the channel width",
        "example": {
          "160": [
            1,
            5,
            9,
            13,
            17,
            21,
            25,
            29,
            33,
            37,
            41,
            45,
            49,
            53,
            57,
            61,
            65,
            69,
            73,
            77,
            81,
            85,
            89,
            93,
            97,
            101,
            105,
            109,
            113,
            117,
            121,
            125,
            129,
            133,
            137,
            141,
            145,
            149,
            153,
            157,
            161,
            165,
            169,
            173,
            177,
            181,
            185,
            189,
            193,
            197,
            201,
            205,
            209,
            213,
            217,
            221
          ],
          "20": [
            1,
            5,
            9,
            13,
            17,
            21,
            25,
            29,
            33,
            37,
            41,
            45,
            49,
            53,
            57,
            61,
            65,
            69,
            73,
            77,
            81,
            85,
            89,
            93,
            97,
            101,
            105,
            109,
            113,
            117,
            121,
            125,
            129,
            133,
            137,
            141,
            145,
            149,
            153,
            157,
            161,
            165,
            169,
            173,
            177,
            181,
            185,
            189,
            193,
            197,
            201,
            205,
            209,
            213,
            217,
            221,
            225,
            229,
            233
          ],
          "40": [
            1,
            5,
            9,
            13,
            17,
            21,
            25,
            29,
            33,
            37,
            41,
            45,
            49,
            53,
            57,
            61,
            65,
            69,
            73,
            77,
            81,
            85,
            89,
            93,
            97,
            101,
            105,
            109,
            113,
            117,
            121,
            125,
            129,
            133,
            137,
            141,
            145,
            149,
            153,
            157,
            161,
            165,
            169,
            173,
            177,
            181,
            185,
            189,
            193,
            197,
            201,
            205,
            209,
            213,
            217,
            221,
            225,
            229
          ],
          "80": [
            1,
            5,
            9,
            13,
            17,
            21,
            25,
            29,
            33,
            37,
            41,
            45,
            49,
            53,
            57,
            61,
            65,
            69,
            73,
            77,
            81,
            85,
            89,
            93,
            97,
            101,
            105,
            109,
            113,
            117,
            121,
            125,
            129,
            133,
            137,
            141,
            145,
            149,
            153,
            157,
            161,
            165,
            169,
            173,
            177,
            181,
            185,
            189,
            193,
            197,
            201,
            205,
            209,
            213,
            217,
            221
          ],
          "psc": [
            5,
            21,
            37,
            53,
            69,
            85,
            101,
            117,
            133,
            149,
            165,
            181,
            197,
            213,
            229
          ]
        }
      },
      "description": "Property key is the channel width",
      "examples": [
        {
          "160": [
            1,
            5,
            9,
            13,
            17,
            21,
            25,
            29,
            33,
            37,
            41,
            45,
            49,
            53,
            57,
            61,
            65,
            69,
            73,
            77,
            81,
            85,
            89,
            93,
            97,
            101,
            105,
            109,
            113,
            117,
            121,
            125,
            129,
            133,
            137,
            141,
            145,
            149,
            153,
            157,
            161,
            165,
            169,
            173,
            177,
            181,
            185,
            189,
            193,
            197,
            201,
            205,
            209,
            213,
            217,
            221
          ],
          "20": [
            1,
            5,
            9,
            13,
            17,
            21,
            25,
            29,
            33,
            37,
            41,
            45,
            49,
            53,
            57,
            61,
            65,
            69,
            73,
            77,
            81,
            85,
            89,
            93,
            97,
            101,
            105,
            109,
            113,
            117,
            121,
            125,
            129,
            133,
            137,
            141,
            145,
            149,
            153,
            157,
            161,
            165,
            169,
            173,
            177,
            181,
            185,
            189,
            193,
            197,
            201,
            205,
            209,
            213,
            217,
            221,
            225,
            229,
            233
          ],
          "40": [
            1,
            5,
            9,
            13,
            17,
            21,
            25,
            29,
            33,
            37,
            41,
            45,
            49,
            53,
            57,
            61,
            65,
            69,
            73,
            77,
            81,
            85,
            89,
            93,
            97,
            101,
            105,
            109,
            113,
            117,
            121,
            125,
            129,
            133,
            137,
            141,
            145,
            149,
            153,
            157,
            161,
            165,
            169,
            173,
            177,
            181,
            185,
            189,
            193,
            197,
            201,
            205,
            209,
            213,
            217,
            221,
            225,
            229
          ],
          "80": [
            1,
            5,
            9,
            13,
            17,
            21,
            25,
            29,
            33,
            37,
            41,
            45,
            49,
            53,
            57,
            61,
            65,
            69,
            73,
            77,
            81,
            85,
            89,
            93,
            97,
            101,
            105,
            109,
            113,
            117,
            121,
            125,
            129,
            133,
            137,
            141,
            145,
            149,
            153,
            157,
            161,
            165,
            169,
            173,
            177,
            181,
            185,
            189,
            193,
            197,
            201,
            205,
            209,
            213,
            217,
            221
          ],
          "psc": [
            5,
            21,
            37,
            53,
            69,
            85,
            101,
            117,
            133,
            149,
            165,
            181,
            197,
            213,
            229
          ]
        }
      ]
    },
    "band6_enabled": {
      "type": "boolean",
      "examples": [
        true
      ]
    },
    "certified": {
      "type": "boolean",
      "examples": [
        true
      ]
    },
    "code": {
      "type": "integer",
      "description": "Country code, ISO 3166-1 numeric",
      "contentEncoding": "int32",
      "examples": [
        840
      ]
    },
    "dfs_ok": {
      "type": "boolean",
      "examples": [
        true
      ]
    },
    "key": {
      "type": "string",
      "description": "Country code, in two-character",
      "examples": [
        "US"
      ]
    },
    "name": {
      "type": "string",
      "examples": [
        "United States"
      ]
    },
    "uses": {
      "type": "string",
      "examples": [
        "US_FCC"
      ]
    }
  }
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

`mistapi.api.v1.constants.definitions.listApChannels()`

## Usage Context

Returns the list of supported Wi-Fi channels per regulatory domain (country), organized by frequency band (2.4 GHz, 5 GHz, 6 GHz). Use this to understand which channels are available in a given country when configuring RF templates or troubleshooting channel assignments.

## Gotchas

- Channel availability is country-specific and regulated — always filter by the relevant country code.
- DFS channels (5 GHz) may be listed as available but are subject to radar detection requirements that cause temporary channel changes.
- 6 GHz channels are only available on Wi-Fi 6E capable APs and in countries that have approved 6 GHz band usage.

## Related Endpoints

- [GET_const_countries.md](GET_const_countries.md) — Country code list (input for channel filtering)
- [GET_const_device_models.md](GET_const_device_models.md) — AP models with radio capabilities
- [../orgs/GET_orgs_org_id_rftemplates.md](../orgs/GET_orgs_org_id_rftemplates.md) — RF templates that configure channel plans

## MistHelper Notes

Not currently used by MistHelper directly. Menu **37** (`OrgTemplateExporter.rf_templates`) exports RF templates that reference channel settings defined by this endpoint.
